"""Held-out evaluation harness: run frozen analytics, score, persist evidence.

Deterministic by construction: each held-out scenario is regenerated from its
frozen seed, analytics run on it, outputs compared to ground-truth labels, and
metric results persisted. Re-running with the same seeds yields identical
analytics metric values (performance latency excluded — see ``performance``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import ProviderCode, ReserveType, ScenarioCode
from app.contracts.v1.simulation import CreateRunRequest
from app.core.auth import ADMIN, get_demo_user
from app.db.transaction import transaction
from app.services.analytics import runner as analytics_runner
from app.services.analytics import config as analytics_cfg
from app.services.constants import PROVIDER_IDS
from app.services.coordination import alerts as alerts_service
from app.services.simulation import run_service
from app.services.validation import config as vcfg
from app.services.validation import ground_truth, metrics, performance, persistence

_PROVIDER_CODE_BY_ID = {v: k.value for k, v in PROVIDER_IDS.items()}
_DQ_INCIDENT_STATUSES = ("stale", "missing", "conflicting")
_EXPLANATION_SECTIONS = ["situation", "evidence", "uncertainty", "next_step"]


def _provider_alertable(flags, provider_id: UUID) -> bool:
    """A provider is predicted-alertable when it has a requires_review flag."""
    return any(
        f.provider_id == provider_id and f.disposition.value == "requires_review"
        for f in flags
    )


async def _frozen_held_out_run(
    session: AsyncSession, *, scenario_code: ScenarioCode, seed: int, outlet_id: UUID
) -> UUID:
    """Reuse the frozen transaction-bearing run for a seed, or create it once.

    The ledger is append-only and its ``synthetic_transaction_ref`` is derived
    from (seed, index), so re-running the same seed dedups to zero transactions.
    Held-out evaluation data must be frozen *before* measurement (guardrail 6):
    the first invocation materializes the dataset; every later invocation reuses
    the same persisted transactions, giving identical analytics metrics.
    """
    result = await session.execute(
        text(
            """
            SELECT sr.simulation_run_id
            FROM simulation_runs sr
            JOIN simulation_scenarios sc ON sc.scenario_id = sr.scenario_id
            WHERE sc.code = :code AND sr.seed = :seed
              AND EXISTS (
                SELECT 1 FROM transactions t
                WHERE t.simulation_run_id = sr.simulation_run_id
              )
            ORDER BY sr.started_at
            LIMIT 1
            """
        ),
        {"code": scenario_code.value, "seed": seed},
    )
    row = result.first()
    if row is not None:
        return row[0]
    run = await run_service.create_run(
        session,
        CreateRunRequest(scenario_code=scenario_code, seed=seed, outlet_id=outlet_id),
    )
    return run.simulation_run_id


async def _dq_counts(session: AsyncSession, simulation_run_id: UUID) -> tuple[int, int]:
    """Latest quality assessment per (outlet, provider) for a run — reproducible.

    Analytics appends a fresh assessment per provider each time it runs; counting
    only the latest per provider keeps the incident rate stable across re-runs.
    """
    result = await session.execute(
        text(
            """
            SELECT DISTINCT ON (outlet_id, provider_id) status
            FROM data_quality_assessments
            WHERE simulation_run_id = :sim
            ORDER BY outlet_id, provider_id, assessed_at DESC
            """
        ),
        {"sim": simulation_run_id},
    )
    statuses = [r[0] for r in result.all()]
    incidents = sum(1 for s in statuses if s in _DQ_INCIDENT_STATUSES)
    return incidents, len(statuses)


async def _published_alert_ids(session: AsyncSession, simulation_run_id: UUID) -> list[UUID]:
    """All published (active) high-impact alerts for a held-out run.

    Reproducible: alerts are deduplicated on publish, so counting the persisted
    active alerts for the frozen run is stable regardless of re-publishing.
    """
    result = await session.execute(
        text(
            "SELECT alert_id FROM alerts WHERE simulation_run_id = :sim AND state = 'active'"
        ),
        {"sim": simulation_run_id},
    )
    return [r[0] for r in result.all()]


async def _explanation_coverage(
    session: AsyncSession, alert_ids: list[UUID]
) -> tuple[int, int]:
    complete = 0
    total = 0
    for alert_id in alert_ids:
        total += 1
        row = await session.execute(
            text(
                """
                SELECT situation_text, evidence_text, uncertainty_text, next_step_text
                FROM alert_explanations
                WHERE alert_id = :id AND locale = 'en'
                """
            ),
            {"id": alert_id},
        )
        m = row.mappings().first()
        if m and all(
            (m[col] or "").strip()
            for col in ("situation_text", "evidence_text", "uncertainty_text", "next_step_text")
        ):
            complete += 1
    return complete, total


async def run_validation(
    session: AsyncSession, *, created_by_user_id: UUID | None = None
) -> dict:
    """Run the held-out evaluation and persist a completed validation run."""
    outlet_id = vcfg.DEFAULT_VALIDATION_OUTLET_ID
    rc = vcfg.release_candidate()
    configuration = {
        "dataset_split": "held_out",
        "release_candidate": rc,
        "seeds": {s.code.value: s.seed for s in vcfg.HELD_OUT_SCENARIOS},
        "outlet_id": str(outlet_id),
        "latency_iterations": vcfg.LATENCY_ITERATIONS,
        "thresholds": {
            "anomaly": analytics_cfg.ANOMALY_DEFAULT_CONFIG,
            "anomaly_suppression_modifier": analytics_cfg.ANOMALY_SUPPRESSION_MODIFIER,
            "liquidity_burn_window_minutes": analytics_cfg.LIQUIDITY_BURN_WINDOW_MINUTES,
        },
    }

    async with transaction(session):
        vr_id = await persistence.create_validation_run(
            session,
            name=vcfg.VALIDATION_RUN_NAME,
            dataset_split="held_out",
            engine_version=vcfg.VALIDATION_ENGINE_VERSION,
            configuration=configuration,
            created_by_user_id=created_by_user_id,
        )

    try:
        cells: list[metrics.AnomalyCell] = []
        shortage_input: tuple[datetime, datetime | None] | None = None
        dq_incidents = 0
        dq_total = 0
        sim_run_ids: dict[str, UUID] = {}

        for spec in vcfg.HELD_OUT_SCENARIOS:
            sim_id = await _frozen_held_out_run(
                session, scenario_code=spec.code, seed=spec.seed, outlet_id=outlet_id
            )
            sim_run_ids[spec.code.value] = sim_id

            async with transaction(session):
                liq = await analytics_runner.run_liquidity(
                    session, simulation_run_id=sim_id, outlet_id=outlet_id
                )
                ano = await analytics_runner.run_anomalies(
                    session, simulation_run_id=sim_id, outlet_id=outlet_id
                )

            labels = ground_truth.build_labels(
                scenario_code=spec.code,
                outlet_id=outlet_id,
                window_start=liq.input_window_start,
                window_end=liq.input_window_end,
            )
            async with transaction(session):
                await persistence.insert_labels(
                    session,
                    validation_run_id=vr_id,
                    simulation_run_id=sim_id,
                    labels=labels,
                )

            # Anomaly cells: one per provider-scoped label (anomaly/normal/dq).
            for label in labels:
                if label.provider_id is None:
                    continue
                cells.append(
                    metrics.AnomalyCell(
                        scenario=spec.code.value,
                        provider_code=_PROVIDER_CODE_BY_ID.get(label.provider_id, "unknown"),
                        ground_truth_anomaly=bool(
                            label.expected_value.get("alertable_anomaly", False)
                        ),
                        predicted_alertable=_provider_alertable(ano.flags, label.provider_id),
                    )
                )

            if spec.code is ScenarioCode.SCENARIO_A:
                shared = next(
                    (p for p in liq.projections if p.reserve_type is ReserveType.SHARED_CASH),
                    None,
                )
                if shared is not None:
                    shortage_input = (shared.as_of_at, shared.projected_shortage_at)

            inc, tot = await _dq_counts(session, sim_id)
            dq_incidents += inc
            dq_total += tot

        # Ensure the held-out Scenario B run has published alerts, then measure
        # explanation coverage over the persisted active alerts (reproducible —
        # publish deduplicates, so re-runs do not change the alert set).
        admin = get_demo_user(ADMIN)
        published_ids: list[UUID] = []
        b_sim = sim_run_ids.get(ScenarioCode.SCENARIO_B.value)
        if b_sim is not None and admin is not None:
            await alerts_service.publish_from_run(
                session, admin, simulation_run_id=b_sim, outlet_id=outlet_id
            )
            published_ids = await _published_alert_ids(session, b_sim)
        complete, total_alerts = await _explanation_coverage(session, published_ids)

        # ---- Assemble metrics (analytics + reliability + performance) ----------
        computed: list[metrics.MetricResult] = []
        computed.extend(metrics.anomaly_metrics(cells))
        if shortage_input is not None:
            lead = metrics.shortage_lead_time_metric(
                as_of_at=shortage_input[0],
                projected_shortage_at=shortage_input[1],
                sample_size=1,
            )
            if lead is not None:
                computed.append(lead)
        dq_metric = metrics.data_quality_incident_rate(
            incident_count=dq_incidents, total_assessments=dq_total
        )
        if dq_metric is not None:
            computed.append(dq_metric)
        coverage = metrics.alert_explanation_coverage(
            complete_alerts=complete,
            total_alerts=total_alerts,
            sections=_EXPLANATION_SECTIONS,
        )
        if coverage is not None:
            computed.append(coverage)
        computed.extend(
            await performance.measure_latency(
                session, outlet_id=outlet_id, iterations=vcfg.LATENCY_ITERATIONS
            )
        )

        async with transaction(session):
            await persistence.insert_metrics(
                session, validation_run_id=vr_id, metrics=computed
            )
            await persistence.finish_validation_run(
                session, validation_run_id=vr_id, status="completed"
            )

        return {
            "validation_run_id": str(vr_id),
            "dataset_split": "held_out",
            "status": "completed",
            "engine_version": vcfg.VALIDATION_ENGINE_VERSION,
            "release_candidate": rc,
            "metric_count": len(computed),
            "metrics": [
                {
                    "metric_code": m.metric_code,
                    "category": m.category.value,
                    "value": str(m.value),
                    "unit": m.unit,
                    "sample_size": m.sample_size,
                }
                for m in computed
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        async with transaction(session):
            await persistence.finish_validation_run(
                session, validation_run_id=vr_id, status="failed"
            )
        raise
