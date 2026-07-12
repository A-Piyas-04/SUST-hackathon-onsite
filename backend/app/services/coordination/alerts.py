"""Candidate-to-alert publication and alert reads (docs Phase 5, §10.1-10.4).

Publication validates alertable candidates, deduplicates active alerts, persists
typed analytical source links WITHOUT recomputing evidence, freezes the immutable
analytical payload, and renders localized explanations. Reads enforce provider
boundaries with a uniform safe not-found response.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.alert_candidate import AlertCandidate
from app.contracts.v1.coordination import (
    AlertExplanationOutput,
    AlertExplanationsResponse,
    AlertListResponse,
    AlertOutput,
    PublishResponse,
)
from app.core.auth import UserContext
from app.core.authz import SafeNotFoundError, can_access_scope
from app.db.transaction import transaction
from app.services.analytics import runner as analytics_runner
from app.services.coordination import audit, explanations
from app.services.constants import DEFAULT_OUTLET_ID


# --------------------------------------------------------------------------- #
# Publication
# --------------------------------------------------------------------------- #
async def _existing_active_alert(session: AsyncSession, dedup_key: str) -> UUID | None:
    result = await session.execute(
        text(
            "SELECT alert_id FROM alerts WHERE deduplication_key = :k AND state = 'active' LIMIT 1"
        ),
        {"k": dedup_key},
    )
    row = result.first()
    return row[0] if row else None


async def _display_context(
    session: AsyncSession, *, outlet_id: UUID, provider_id: UUID | None, candidate: AlertCandidate
) -> dict[str, Any]:
    outlet_name = (
        await session.execute(
            text("SELECT display_name FROM outlets WHERE outlet_id = :id"),
            {"id": outlet_id},
        )
    ).scalar()
    provider_name = "shared cash"
    if provider_id is not None:
        provider_name = (
            await session.execute(
                text("SELECT display_name FROM providers WHERE provider_id = :id"),
                {"id": provider_id},
            )
        ).scalar() or "the provider"
    shortage_at = None
    for item in candidate.structured_evidence:
        if item.signal_code in {"projected_shortage_at", "shortage_at"}:
            shortage_at = item.value or item.label
    return {
        "outlet": outlet_name or "the outlet",
        "provider": provider_name,
        "evidence_summary": candidate.evidence_summary,
        "shortage_at": shortage_at or "the projected time",
        "status": candidate.confidence_level.value,
        "plausible_benign_explanation": candidate.plausible_benign_explanation,
    }


async def _publish_one(
    session: AsyncSession,
    actor: UserContext,
    candidate: AlertCandidate,
    *,
    simulation_run_id: UUID,
    liquidity_projection_id: UUID | None,
    anomaly_flag_id: UUID | None,
    quality_ids: tuple[UUID, ...],
) -> tuple[str, UUID]:
    # Dedup is scoped to the simulation run: analytics artifacts (projections,
    # flags, assessments) are all run-scoped and each alert cites a run, so
    # re-publishing the same run deduplicates while distinct runs (distinct
    # datasets) keep their own alerts.
    dedup_key = f"{simulation_run_id}:{candidate.deduplication_key}"
    dup = await _existing_active_alert(session, dedup_key)
    if dup is not None:
        return ("deduplicated", dup)

    alert_id = uuid4()
    payload: dict[str, Any] = {
        "evidence_summary": candidate.evidence_summary,
        "recommended_next_step": candidate.recommended_next_step,
        "confidence": str(candidate.confidence),
        "confidence_level": candidate.confidence_level.value,
        "plausible_benign_explanation": candidate.plausible_benign_explanation,
        "evidence": [e.model_dump(mode="json") for e in candidate.structured_evidence],
    }
    await session.execute(
        text(
            """
            INSERT INTO alerts (
              alert_id, simulation_run_id, outlet_id, provider_id, alert_type,
              severity, state, deduplication_key, title_key, structured_payload,
              requires_case, detected_at
            ) VALUES (
              :id, :sim_run_id, :outlet_id, :provider_id, :alert_type,
              :severity, 'active', :dedup, :title_key, CAST(:payload AS jsonb),
              :requires_case, :detected_at
            )
            """
        ),
        {
            "id": alert_id,
            "sim_run_id": simulation_run_id,
            "outlet_id": candidate.outlet_id,
            "provider_id": candidate.provider_id,
            "alert_type": candidate.alert_type.value,
            "severity": candidate.severity.value,
            "dedup": dedup_key,
            "title_key": candidate.title_key,
            "payload": json.dumps(payload),
            "requires_case": candidate.requires_case,
            "detected_at": candidate.detected_at,
        },
    )

    # Typed analytical source links (no evidence recomputation drift).
    if liquidity_projection_id is not None:
        await session.execute(
            text(
                """
                INSERT INTO alert_liquidity_projections (alert_id, liquidity_projection_id)
                VALUES (:a, :p) ON CONFLICT DO NOTHING
                """
            ),
            {"a": alert_id, "p": liquidity_projection_id},
        )
    if anomaly_flag_id is not None:
        await session.execute(
            text(
                """
                INSERT INTO alert_anomaly_flags (alert_id, anomaly_flag_id)
                VALUES (:a, :f) ON CONFLICT DO NOTHING
                """
            ),
            {"a": alert_id, "f": anomaly_flag_id},
        )
    for qid in quality_ids:
        await session.execute(
            text(
                """
                INSERT INTO alert_quality_assessments (alert_id, data_quality_assessment_id)
                VALUES (:a, :q) ON CONFLICT DO NOTHING
                """
            ),
            {"a": alert_id, "q": qid},
        )

    context = await _display_context(
        session,
        outlet_id=candidate.outlet_id,
        provider_id=candidate.provider_id,
        candidate=candidate,
    )
    await explanations.render_and_persist(
        session, alert_id=alert_id, alert_type=candidate.alert_type.value, context=context
    )
    await audit.write_audit_event(
        session,
        action="alert_published",
        actor=actor,
        actor_type="analytics_engine",
        alert_id=alert_id,
        provider_id=candidate.provider_id,
        outlet_id=candidate.outlet_id,
        entity_type="alert",
        entity_id=alert_id,
        new_values={"alert_type": candidate.alert_type.value, "severity": candidate.severity.value},
    )
    return ("published", alert_id)


def _match_liquidity_projection(projections, candidate: AlertCandidate):
    for p in projections:
        if p.provider_id == candidate.provider_id and p.projected_shortage_at is not None:
            return p
    return None


def _match_anomaly_flag(flags, candidate: AlertCandidate):
    for f in flags:
        if f.provider_id == candidate.provider_id and f.disposition.value == "requires_review":
            return f
    return None


async def publish_from_run(
    session: AsyncSession,
    actor: UserContext,
    *,
    simulation_run_id: UUID,
    outlet_id: UUID | None = None,
) -> PublishResponse:
    """Run analytics for a simulation run/outlet and publish alertable candidates.

    Internal/thin control so Scenario D is executable through the API only.
    """
    outlet_id = outlet_id or DEFAULT_OUTLET_ID
    published: list[UUID] = []
    deduplicated: list[UUID] = []
    async with transaction(session):
        liq = await analytics_runner.run_liquidity(
            session, simulation_run_id=simulation_run_id, outlet_id=outlet_id
        )
        ano = await analytics_runner.run_anomalies(
            session, simulation_run_id=simulation_run_id, outlet_id=outlet_id
        )
        for cand in liq.candidates:
            proj = _match_liquidity_projection(liq.projections, cand)
            projection_id = cand.source_links.liquidity_projection_id
            if projection_id is None and proj is not None:
                projection_id = proj.liquidity_projection_id
            status, aid = await _publish_one(
                session,
                actor,
                cand,
                simulation_run_id=simulation_run_id,
                liquidity_projection_id=projection_id,
                anomaly_flag_id=None,
                quality_ids=cand.source_links.quality_assessment_ids,
            )
            (published if status == "published" else deduplicated).append(aid)
        for cand in ano.candidates:
            flag = _match_anomaly_flag(ano.flags, cand)
            quality_ids: tuple[UUID, ...] = ()
            if flag is not None and flag.data_quality_assessment_id is not None:
                quality_ids = (flag.data_quality_assessment_id,)
            status, aid = await _publish_one(
                session,
                actor,
                cand,
                simulation_run_id=simulation_run_id,
                liquidity_projection_id=None,
                anomaly_flag_id=(
                    cand.source_links.anomaly_flag_id
                    or (flag.anomaly_flag_id if flag else None)
                ),
                quality_ids=quality_ids,
            )
            (published if status == "published" else deduplicated).append(aid)

    now = datetime.now(timezone.utc)
    published_alerts = [await get_alert(session, actor, aid) for aid in published]
    return PublishResponse(
        published=published_alerts,
        deduplicated_alert_ids=deduplicated,
        generated_at=now,
    )


# --------------------------------------------------------------------------- #
# Reads
# --------------------------------------------------------------------------- #
async def _source_links(session: AsyncSession, alert_id: UUID) -> dict[str, Any]:
    lp = await session.execute(
        text("SELECT liquidity_projection_id FROM alert_liquidity_projections WHERE alert_id = :a"),
        {"a": alert_id},
    )
    af = await session.execute(
        text("SELECT anomaly_flag_id FROM alert_anomaly_flags WHERE alert_id = :a"),
        {"a": alert_id},
    )
    aq = await session.execute(
        text("SELECT data_quality_assessment_id FROM alert_quality_assessments WHERE alert_id = :a"),
        {"a": alert_id},
    )
    return {
        "liquidity_projection_ids": [str(r[0]) for r in lp.all()],
        "anomaly_flag_ids": [str(r[0]) for r in af.all()],
        "quality_assessment_ids": [str(r[0]) for r in aq.all()],
    }


async def _to_output(session: AsyncSession, row) -> AlertOutput:
    case_row = await session.execute(
        text("SELECT case_id FROM cases WHERE alert_id = :a"), {"a": row["alert_id"]}
    )
    case = case_row.first()
    return AlertOutput(
        alert_id=row["alert_id"],
        simulation_run_id=row["simulation_run_id"],
        outlet_id=row["outlet_id"],
        provider_id=row["provider_id"],
        alert_type=row["alert_type"],
        severity=row["severity"],
        state=row["state"],
        deduplication_key=row["deduplication_key"],
        title_key=row["title_key"],
        requires_case=row["requires_case"],
        detected_at=row["detected_at"],
        created_at=row["created_at"],
        structured_payload=row["structured_payload"] or {},
        source_links=await _source_links(session, row["alert_id"]),
        has_case=case is not None,
        case_id=case[0] if case else None,
    )


async def _load_alert_row(session: AsyncSession, alert_id: UUID):
    result = await session.execute(
        text("SELECT * FROM alerts WHERE alert_id = :id"), {"id": alert_id}
    )
    return result.mappings().first()


async def require_alert(session: AsyncSession, user: UserContext, alert_id: UUID):
    """Load an alert row enforcing provider boundaries with safe not-found."""
    row = await _load_alert_row(session, alert_id)
    if row is None:
        raise SafeNotFoundError("Alert")
    if not await can_access_scope(
        session, user, outlet_id=row["outlet_id"], provider_id=row["provider_id"]
    ):
        raise SafeNotFoundError("Alert")
    return row


async def get_alert(session: AsyncSession, user: UserContext, alert_id: UUID) -> AlertOutput:
    row = await require_alert(session, user, alert_id)
    return await _to_output(session, row)


async def list_alerts(
    session: AsyncSession,
    user: UserContext,
    *,
    outlet_id: UUID | None = None,
    state: str | None = "active",
) -> AlertListResponse:
    clauses = []
    params: dict[str, Any] = {}
    if outlet_id is not None:
        clauses.append("outlet_id = :outlet_id")
        params["outlet_id"] = outlet_id
    if state is not None:
        clauses.append("state = :state")
        params["state"] = state
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    result = await session.execute(
        text(f"SELECT * FROM alerts{where} ORDER BY detected_at DESC"), params
    )
    alerts: list[AlertOutput] = []
    for row in result.mappings().all():
        if await can_access_scope(
            session, user, outlet_id=row["outlet_id"], provider_id=row["provider_id"]
        ):
            alerts.append(await _to_output(session, row))
    return AlertListResponse(alerts=alerts, generated_at=datetime.now(timezone.utc))


async def get_explanations(
    session: AsyncSession, user: UserContext, alert_id: UUID
) -> AlertExplanationsResponse:
    await require_alert(session, user, alert_id)  # authz + safe not-found
    result = await session.execute(
        text(
            """
            SELECT * FROM alert_explanations
            WHERE alert_id = :a
            ORDER BY locale
            """
        ),
        {"a": alert_id},
    )
    explanations_out = [
        AlertExplanationOutput(
            alert_explanation_id=r["alert_explanation_id"],
            alert_id=r["alert_id"],
            locale=r["locale"],
            situation_text=r["situation_text"],
            evidence_text=r["evidence_text"],
            uncertainty_text=r["uncertainty_text"],
            next_step_text=r["next_step_text"],
            benign_context_text=r["benign_context_text"],
            rendered_at=r["rendered_at"],
        )
        for r in result.mappings().all()
    ]
    return AlertExplanationsResponse(
        alert_id=alert_id,
        explanations=explanations_out,
        generated_at=datetime.now(timezone.utc),
    )
