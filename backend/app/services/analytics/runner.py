"""Analytics orchestration: ledger reads -> engines -> persistence -> envelopes.

Each run creates an ``analytics_runs`` lineage row, computes data-quality
assessments, runs the domain engine per reserve/provider (never blended), and
persists explainable, reproducible artifacts. It then maps every result through
the ``ResultEnvelope -> AlertCandidate`` seam, respecting suppression guardrails.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.analytics_responses import (
    AnomalyRunResponse,
    LiquidityRunResponse,
)
from app.contracts.v1.anomaly import AnomalyEvidenceItem, AnomalyFlagOutput
from app.contracts.v1.common import EvidenceItem
from app.contracts.v1.enums import (
    AnalyticsEngine,
    AnomalyPattern,
    ProviderCode,
    ReserveType,
)
from app.contracts.v1.envelope import (
    AnomalyEngineSpecific,
    LiquidityEngineSpecific,
    ResultEnvelope,
)
from app.contracts.v1.liquidity import LiquidityProjectionOutput, LiquiditySignal
from app.contracts.v1.quality import QualityAssessmentInput, QualityIssueInput
from app.core.errors import AppError
from app.services.alert_candidate_adapter import envelope_to_alert_candidate
from app.services.analytics import config as cfg
from app.services.analytics import persistence
from app.services.anomaly.engine import (
    AnomalyInput,
    AnomalyRuleConfig,
    AnomalyResult,
    BalanceAnomalyInput,
    BalanceRuleConfig,
    BalanceSnapshotRecord,
    BehavioralAnomalyInput,
    BehavioralRuleConfig,
    TransactionRecord,
    VelocityAnomalyInput,
    VelocityRuleConfig,
    detect_balance_inconsistency,
    detect_behavioral_embedding,
    detect_near_identical_amounts,
    detect_velocity_spike,
)
from app.services.constants import DEFAULT_OUTLET_ID
from app.services.liquidity.engine import (
    BalancePoint,
    LiquidityReserveInput,
    forecast_reserve,
)
from app.services.quality.engine import (
    BalanceObservation,
    ProviderQualityInput,
    assess_provider_quality,
)


# --------------------------------------------------------------------------- #
# Ledger read helpers
# --------------------------------------------------------------------------- #
async def _accounts(session: AsyncSession, outlet_id: UUID) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT opa.outlet_provider_account_id, opa.provider_id, p.code AS provider_code
            FROM outlet_provider_accounts opa
            JOIN providers p ON p.provider_id = opa.provider_id
            WHERE opa.outlet_id = :outlet_id AND opa.is_active
            ORDER BY p.code
            """
        ),
        {"outlet_id": outlet_id},
    )
    return [dict(r) for r in result.mappings().all()]


async def _cash_observations(
    session: AsyncSession, run_id: UUID, outlet_id: UUID
) -> list[BalancePoint]:
    result = await session.execute(
        text(
            """
            SELECT observed_at, balance FROM cash_balance_snapshots
            WHERE simulation_run_id = :run_id AND outlet_id = :outlet_id
            ORDER BY observed_at
            """
        ),
        {"run_id": run_id, "outlet_id": outlet_id},
    )
    return [BalancePoint(observed_at=r["observed_at"], balance=r["balance"]) for r in result.mappings().all()]


async def _provider_observations(
    session: AsyncSession, run_id: UUID, account_id: UUID
) -> list[BalanceObservation]:
    result = await session.execute(
        text(
            """
            SELECT observed_at, received_at, balance FROM provider_balance_snapshots
            WHERE simulation_run_id = :run_id AND outlet_provider_account_id = :account_id
            ORDER BY observed_at
            """
        ),
        {"run_id": run_id, "account_id": account_id},
    )
    return [
        BalanceObservation(
            observed_at=r["observed_at"], balance=r["balance"], received_at=r["received_at"]
        )
        for r in result.mappings().all()
    ]


async def _provider_transactions(
    session: AsyncSession, run_id: UUID, account_id: UUID
) -> list[TransactionRecord]:
    result = await session.execute(
        text(
            """
            SELECT transaction_id, synthetic_party_ref, amount, occurred_at,
                   transaction_type, status
            FROM transactions
            WHERE simulation_run_id = :run_id AND outlet_provider_account_id = :account_id
            ORDER BY occurred_at
            """
        ),
        {"run_id": run_id, "account_id": account_id},
    )
    return [
        TransactionRecord(
            transaction_id=r["transaction_id"],
            party_ref=r["synthetic_party_ref"],
            amount=r["amount"],
            occurred_at=r["occurred_at"],
            transaction_type=r["transaction_type"],
            status=r["status"],
        )
        for r in result.mappings().all()
    ]


async def _rejected_counts(session: AsyncSession, run_id: UUID, outlet_id: UUID) -> dict[str, int]:
    result = await session.execute(
        text(
            """
            SELECT p.code AS provider_code, count(*) AS rejected
            FROM ingestion_events ie
            JOIN ingestion_batches ib ON ib.ingestion_batch_id = ie.ingestion_batch_id
            JOIN providers p ON p.provider_id = ib.provider_id
            WHERE ib.simulation_run_id = :run_id AND ib.outlet_id = :outlet_id
              AND ie.normalization_status = 'rejected'
            GROUP BY p.code
            """
        ),
        {"run_id": run_id, "outlet_id": outlet_id},
    )
    return {r["provider_code"]: int(r["rejected"]) for r in result.mappings().all()}


async def _compute_window(
    session: AsyncSession, run_id: UUID, outlet_id: UUID
) -> tuple[datetime, datetime]:
    result = await session.execute(
        text(
            """
            SELECT min(ts) AS start, max(ts) AS end FROM (
              SELECT occurred_at AS ts FROM transactions
                WHERE simulation_run_id = :run_id AND outlet_id = :outlet_id
              UNION ALL
              SELECT observed_at FROM provider_balance_snapshots
                WHERE simulation_run_id = :run_id AND outlet_id = :outlet_id
              UNION ALL
              SELECT observed_at FROM cash_balance_snapshots
                WHERE simulation_run_id = :run_id AND outlet_id = :outlet_id
            ) t
            """
        ),
        {"run_id": run_id, "outlet_id": outlet_id},
    )
    row = result.mappings().one()
    now = datetime.now(timezone.utc)
    return (row["start"] or now, row["end"] or now)


async def _validate_run(session: AsyncSession, run_id: UUID) -> None:
    result = await session.execute(
        text("SELECT 1 FROM simulation_runs WHERE simulation_run_id = :id"),
        {"id": run_id},
    )
    if result.first() is None:
        raise AppError("not_found", f"Simulation run {run_id} not found.", status_code=404)


async def _existing_analytics_run(
    session: AsyncSession, simulation_run_id: UUID, engine: AnalyticsEngine
) -> UUID | None:
    """Return the earliest analytics run of this engine already persisted for the
    simulation run, if any.

    Analytics on a completed simulation run is deterministic and append-only, so
    re-running the same engine for the same run would only duplicate flags,
    evidence, quality assessments and projections (identical values at identical
    timestamps). Callers use this to recompute the response in-memory while
    skipping the redundant writes — one analytics cycle per run, idempotently.
    """
    result = await session.execute(
        text(
            """
            SELECT analytics_run_id
            FROM analytics_runs
            WHERE simulation_run_id = :run_id AND engine = :engine
            ORDER BY started_at
            LIMIT 1
            """
        ),
        {"run_id": simulation_run_id, "engine": engine.value},
    )
    row = result.first()
    return row[0] if row else None


# --------------------------------------------------------------------------- #
# Envelope builders (seam)
# --------------------------------------------------------------------------- #
def _signal_evidence(signals: list[LiquiditySignal]) -> tuple[EvidenceItem, ...]:
    return tuple(
        EvidenceItem(
            signal_code=s.signal_code,
            label=s.label,
            numeric_value=s.numeric_value,
            unit=s.unit,
            direction=s.direction,
            display_order=s.display_order,
        )
        for s in signals
    )


def _liquidity_envelope(
    projection: LiquidityProjectionOutput,
    *,
    window_start: datetime,
    window_end: datetime,
    quality_assessment_ids: tuple[UUID, ...],
    provider_code: str | None,
) -> ResultEnvelope:
    specific = LiquidityEngineSpecific(
        reserve_type=projection.reserve_type,
        provider_code=provider_code,
        current_balance=projection.current_balance,
        burn_rate_per_hour=projection.burn_rate_per_hour,
        projected_shortage_at=projection.projected_shortage_at,
        lower_bound_at=projection.lower_bound_at,
        upper_bound_at=projection.upper_bound_at,
        sample_count=projection.sample_count,
        is_actionable=projection.is_actionable,
        non_actionable_reason=projection.non_actionable_reason,
    )
    return ResultEnvelope(
        engine=AnalyticsEngine.LIQUIDITY,
        engine_version=cfg.LIQUIDITY_ENGINE_VERSION,
        input_window_start=window_start,
        input_window_end=window_end,
        quality_assessment_ids=quality_assessment_ids,
        confidence=float(projection.confidence_score),
        confidence_level=projection.confidence_level,
        evidence=_signal_evidence(projection.signals),
        generated_at=datetime.now(timezone.utc),
        engine_specific=specific.model_dump(),
    )


def _anomaly_envelope(
    flag: AnomalyFlagOutput,
    *,
    window_start: datetime,
    window_end: datetime,
    provider_code: str,
    quality_assessment_ids: tuple[UUID, ...],
) -> ResultEnvelope:
    specific = AnomalyEngineSpecific(
        pattern=flag.pattern.value,
        provider_code=provider_code,
        window_start=flag.window_start,
        window_end=flag.window_end,
        disposition=flag.disposition.value,
        reason_code=flag.reason_code,
        evidence_summary=flag.evidence_summary,
        plausible_benign_explanation=flag.plausible_benign_explanation,
        suppression_disposition=flag.suppression_reason or "none",
    )
    evidence = tuple(
        EvidenceItem(
            evidence_type=item.evidence_type,
            label=item.label,
            value=item.value,
            display_order=item.display_order,
        )
        for item in flag.evidence_items
    )
    return ResultEnvelope(
        engine=AnalyticsEngine.ANOMALY,
        engine_version=cfg.ANOMALY_ENGINE_VERSION,
        input_window_start=window_start,
        input_window_end=window_end,
        quality_assessment_ids=quality_assessment_ids,
        confidence=float(flag.confidence_score),
        confidence_level=flag.confidence_level,
        evidence=evidence,
        generated_at=datetime.now(timezone.utc),
        engine_specific=specific.model_dump(),
    )


# --------------------------------------------------------------------------- #
# Liquidity run
# --------------------------------------------------------------------------- #
async def run_liquidity(
    session: AsyncSession, *, simulation_run_id: UUID, outlet_id: UUID | None = None
) -> LiquidityRunResponse:
    outlet_id = outlet_id or DEFAULT_OUTLET_ID
    await _validate_run(session, simulation_run_id)
    window_start, window_end = await _compute_window(session, simulation_run_id, outlet_id)
    as_of = window_end

    # Idempotent re-run guard: if liquidity analytics already ran for this
    # simulation run, recompute the (deterministic) response but skip the writes
    # so evidence/projections/quality are not duplicated on repeat invocation.
    analytics_run_id = await _existing_analytics_run(
        session, simulation_run_id, AnalyticsEngine.LIQUIDITY
    )
    persist = analytics_run_id is None
    if persist:
        analytics_run_id = await persistence.create_analytics_run(
            session,
            simulation_run_id=simulation_run_id,
            engine=AnalyticsEngine.LIQUIDITY,
            engine_version=cfg.LIQUIDITY_ENGINE_VERSION,
            configuration={
                "burn_window_minutes": cfg.LIQUIDITY_BURN_WINDOW_MINUTES,
                "min_samples": cfg.LIQUIDITY_MIN_SAMPLES,
                "target_samples": cfg.LIQUIDITY_TARGET_SAMPLES,
                "bound_factor": cfg.LIQUIDITY_BOUND_FACTOR,
                "outlet_id": str(outlet_id),
            },
            input_window_start=window_start,
            input_window_end=window_end,
        )

    projections: list[LiquidityProjectionOutput] = []
    candidates = []

    # --- Shared physical cash (independent; provider-less quality) -------------
    cash_obs = await _cash_observations(session, simulation_run_id, outlet_id)
    cash_quality = assess_provider_quality(
        ProviderQualityInput(
            provider_code="shared_cash",
            observations=[
                BalanceObservation(observed_at=o.observed_at, balance=o.balance) for o in cash_obs
            ],
            transaction_count=0,
            rejected_event_count=0,
            as_of=as_of,
        )
    )
    cash_forecast = forecast_reserve(
        LiquidityReserveInput(
            reserve_type=ReserveType.SHARED_CASH,
            observations=cash_obs,
            as_of=as_of,
            quality_modifier=cash_quality.confidence_modifier,
            quality_status=cash_quality.status.value,
        )
    )
    cash_projection = _forecast_to_projection(cash_forecast, outlet_id=outlet_id)
    if persist:
        cash_pid = await persistence.insert_liquidity_projection(
            session, cash_projection, analytics_run_id=analytics_run_id, primary_assessment_id=None
        )
    else:
        cash_pid = cash_projection.liquidity_projection_id or uuid4()
    cash_projection.liquidity_projection_id = cash_pid
    cash_projection.analytics_run_id = analytics_run_id
    projections.append(cash_projection)
    cash_envelope = _liquidity_envelope(
        cash_projection,
        window_start=window_start,
        window_end=window_end,
        quality_assessment_ids=(),
        provider_code=None,
    )
    cand = envelope_to_alert_candidate(cash_envelope, outlet_id=outlet_id, provider_id=None)
    if cand is not None:
        candidates.append(cand)

    # --- Each provider e-money reserve (independent) ---------------------------
    accounts = await _accounts(session, outlet_id)
    rejected = await _rejected_counts(session, simulation_run_id, outlet_id)
    for acct in accounts:
        code = acct["provider_code"]
        obs = await _provider_observations(session, simulation_run_id, acct["outlet_provider_account_id"])
        txns = await _provider_transactions(session, simulation_run_id, acct["outlet_provider_account_id"])
        quality = assess_provider_quality(
            ProviderQualityInput(
                provider_code=code,
                observations=obs,
                transaction_count=len(txns),
                rejected_event_count=rejected.get(code, 0),
                as_of=as_of,
            )
        )
        if persist:
            assessment_id = await persistence.insert_quality_assessment(
                session,
                _quality_to_input(
                    quality,
                    simulation_run_id=simulation_run_id,
                    outlet_id=outlet_id,
                    provider_id=acct["provider_id"],
                ),
            )
        else:
            assessment_id = uuid4()
        forecast = forecast_reserve(
            LiquidityReserveInput(
                reserve_type=ReserveType.PROVIDER_E_MONEY,
                observations=[BalancePoint(observed_at=o.observed_at, balance=o.balance) for o in obs],
                as_of=as_of,
                quality_modifier=quality.confidence_modifier,
                quality_status=quality.status.value,
                provider_code=code,
            )
        )
        projection = _forecast_to_projection(
            forecast,
            outlet_id=outlet_id,
            provider_id=acct["provider_id"],
            account_id=acct["outlet_provider_account_id"],
        )
        if persist:
            pid = await persistence.insert_liquidity_projection(
                session,
                projection,
                analytics_run_id=analytics_run_id,
                primary_assessment_id=assessment_id,
                linked_assessment_ids=(assessment_id,),
            )
        else:
            pid = projection.liquidity_projection_id or uuid4()
        projection.liquidity_projection_id = pid
        projection.analytics_run_id = analytics_run_id
        projections.append(projection)
        envelope = _liquidity_envelope(
            projection,
            window_start=window_start,
            window_end=window_end,
            quality_assessment_ids=(assessment_id,),
            provider_code=code,
        )
        cand = envelope_to_alert_candidate(
            envelope, outlet_id=outlet_id, provider_id=acct["provider_id"]
        )
        if cand is not None:
            candidates.append(cand)

    if persist:
        await persistence.complete_analytics_run(session, analytics_run_id)
    return LiquidityRunResponse(
        analytics_run_id=analytics_run_id,
        simulation_run_id=simulation_run_id,
        engine_version=cfg.LIQUIDITY_ENGINE_VERSION,
        input_window_start=window_start,
        input_window_end=window_end,
        projections=projections,
        candidates=candidates,
    )


# --------------------------------------------------------------------------- #
# Anomaly run
# --------------------------------------------------------------------------- #
async def _active_rules(session: AsyncSession) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT anomaly_rule_id, pattern, configuration
            FROM anomaly_rules
            WHERE is_active
            ORDER BY created_at
            """
        )
    )
    rows = [dict(r) for r in result.mappings().all()]
    if not rows:
        raise AppError("configuration_error", "No active anomaly rules.", status_code=500)
    return rows


_PATTERN_TO_ENUM = {
    "near_identical_amounts": AnomalyPattern.NEAR_IDENTICAL_AMOUNTS,
    "velocity_spike": AnomalyPattern.VELOCITY_SPIKE,
    "balance_inconsistency": AnomalyPattern.BALANCE_INCONSISTENCY,
    "behavioral_embedding": AnomalyPattern.BEHAVIORAL_EMBEDDING,
}


def _run_anomaly_detector(
    pattern: str,
    *,
    provider_code: str,
    transactions: list[TransactionRecord],
    observations: list[BalanceObservation],
    quality_status: str,
    quality_modifier: Decimal,
    as_of: datetime,
    configuration: dict,
) -> AnomalyResult:
    if pattern == "near_identical_amounts":
        return detect_near_identical_amounts(
            AnomalyInput(
                provider_code=provider_code,
                transactions=transactions,
                quality_status=quality_status,
                quality_modifier=quality_modifier,
                rule_config=AnomalyRuleConfig.from_dict(configuration),
            )
        )
    if pattern == "velocity_spike":
        return detect_velocity_spike(
            VelocityAnomalyInput(
                provider_code=provider_code,
                transactions=transactions,
                quality_status=quality_status,
                quality_modifier=quality_modifier,
                as_of=as_of,
                rule_config=VelocityRuleConfig.from_dict(configuration),
            )
        )
    if pattern == "balance_inconsistency":
        return detect_balance_inconsistency(
            BalanceAnomalyInput(
                provider_code=provider_code,
                transactions=transactions,
                observations=[
                    BalanceSnapshotRecord(
                        observed_at=o.observed_at,
                        balance=o.balance,
                        received_at=o.received_at,
                    )
                    for o in observations
                ],
                quality_status=quality_status,
                quality_modifier=quality_modifier,
                as_of=as_of,
                rule_config=BalanceRuleConfig.from_dict(configuration),
            )
        )
    if pattern == "behavioral_embedding":
        return detect_behavioral_embedding(
            BehavioralAnomalyInput(
                provider_code=provider_code,
                transactions=transactions,
                quality_status=quality_status,
                quality_modifier=quality_modifier,
                as_of=as_of,
                rule_config=BehavioralRuleConfig.from_dict(configuration),
            )
        )
    raise AppError("configuration_error", f"Unsupported anomaly pattern: {pattern}", status_code=500)


def _result_to_flag(
    result: AnomalyResult,
    *,
    outlet_id: UUID,
    provider_id: UUID,
    account_id: UUID,
    assessment_id: UUID,
    pattern: AnomalyPattern,
) -> AnomalyFlagOutput:
    return AnomalyFlagOutput(
        outlet_id=outlet_id,
        provider_id=provider_id,
        outlet_provider_account_id=account_id,
        data_quality_assessment_id=assessment_id,
        window_start=result.window_start or datetime.now(timezone.utc),
        window_end=result.window_end or datetime.now(timezone.utc),
        pattern=pattern,
        confidence_score=result.confidence_score,
        confidence_level=result.confidence_level,
        disposition=result.disposition,
        reason_code=result.reason_code,
        evidence_summary=result.evidence_summary,
        plausible_benign_explanation=result.plausible_benign_explanation,
        suppression_reason=result.suppression_reason,
        evidence_items=[
            AnomalyEvidenceItem(
                evidence_type=e.evidence_type,
                label=e.label,
                value=e.value,
                display_order=e.display_order,
            )
            for e in result.evidence_items
        ],
        transaction_ids=list(result.transaction_ids),
    )


async def run_anomalies(
    session: AsyncSession, *, simulation_run_id: UUID, outlet_id: UUID | None = None
) -> AnomalyRunResponse:
    outlet_id = outlet_id or DEFAULT_OUTLET_ID
    await _validate_run(session, simulation_run_id)
    window_start, window_end = await _compute_window(session, simulation_run_id, outlet_id)
    as_of = window_end
    rules = await _active_rules(session)

    # Idempotent re-run guard: if anomaly analytics already ran for this
    # simulation run, recompute the (deterministic) response but skip the writes
    # so flags/evidence/quality are not duplicated on repeat invocation.
    analytics_run_id = await _existing_analytics_run(
        session, simulation_run_id, AnalyticsEngine.ANOMALY
    )
    persist = analytics_run_id is None
    if persist:
        analytics_run_id = await persistence.create_analytics_run(
            session,
            simulation_run_id=simulation_run_id,
            engine=AnalyticsEngine.ANOMALY,
            engine_version=cfg.ANOMALY_ENGINE_VERSION,
            configuration={
                "rules": [
                    {
                        "anomaly_rule_id": str(r["anomaly_rule_id"]),
                        "pattern": r["pattern"],
                        "configuration": r["configuration"],
                    }
                    for r in rules
                ],
                "outlet_id": str(outlet_id),
            },
            input_window_start=window_start,
            input_window_end=window_end,
        )

    flags: list[AnomalyFlagOutput] = []
    candidates = []
    suppressed_count = 0

    accounts = await _accounts(session, outlet_id)
    rejected = await _rejected_counts(session, simulation_run_id, outlet_id)
    for acct in accounts:
        code = acct["provider_code"]
        obs = await _provider_observations(session, simulation_run_id, acct["outlet_provider_account_id"])
        txns = await _provider_transactions(session, simulation_run_id, acct["outlet_provider_account_id"])
        quality = assess_provider_quality(
            ProviderQualityInput(
                provider_code=code,
                observations=obs,
                transaction_count=len(txns),
                rejected_event_count=rejected.get(code, 0),
                as_of=as_of,
            )
        )
        if persist:
            assessment_id = await persistence.insert_quality_assessment(
                session,
                _quality_to_input(
                    quality,
                    simulation_run_id=simulation_run_id,
                    outlet_id=outlet_id,
                    provider_id=acct["provider_id"],
                ),
            )
        else:
            assessment_id = uuid4()
        for rule in rules:
            pattern = rule["pattern"]
            pattern_enum = _PATTERN_TO_ENUM.get(pattern)
            if pattern_enum is None:
                continue
            result = _run_anomaly_detector(
                pattern,
                provider_code=code,
                transactions=txns,
                observations=obs,
                quality_status=quality.status.value,
                quality_modifier=quality.confidence_modifier,
                as_of=as_of,
                configuration=rule["configuration"],
            )
            if not result.persist:
                continue

            flag = _result_to_flag(
                result,
                outlet_id=outlet_id,
                provider_id=acct["provider_id"],
                account_id=acct["outlet_provider_account_id"],
                assessment_id=assessment_id,
                pattern=pattern_enum,
            )
            if persist:
                flag_id = await persistence.insert_anomaly_flag(
                    session, flag, analytics_run_id=analytics_run_id, anomaly_rule_id=rule["anomaly_rule_id"]
                )
            else:
                flag_id = flag.anomaly_flag_id or uuid4()
            flag.anomaly_flag_id = flag_id
            flag.analytics_run_id = analytics_run_id
            flag.anomaly_rule_id = rule["anomaly_rule_id"]
            flags.append(flag)
            if result.disposition.value == "suppressed_data_quality":
                suppressed_count += 1
            envelope = _anomaly_envelope(
                flag,
                window_start=window_start,
                window_end=window_end,
                provider_code=code,
                quality_assessment_ids=(assessment_id,),
            )
            cand = envelope_to_alert_candidate(envelope, outlet_id=outlet_id)
            if cand is not None:
                candidates.append(cand)

    if persist:
        await persistence.complete_analytics_run(session, analytics_run_id)
    return AnomalyRunResponse(
        analytics_run_id=analytics_run_id,
        simulation_run_id=simulation_run_id,
        engine_version=cfg.ANOMALY_ENGINE_VERSION,
        input_window_start=window_start,
        input_window_end=window_end,
        flags=flags,
        suppressed_count=suppressed_count,
        candidates=candidates,
    )


# --------------------------------------------------------------------------- #
# Mappers
# --------------------------------------------------------------------------- #
def _forecast_to_projection(
    forecast,
    *,
    outlet_id: UUID,
    provider_id: UUID | None = None,
    account_id: UUID | None = None,
) -> LiquidityProjectionOutput:
    signals = [
        LiquiditySignal(
            signal_code=s.signal_code,
            label=s.label,
            numeric_value=s.numeric_value,
            unit=s.unit,
            direction=s.direction,
            details=s.details,
            display_order=s.display_order,
        )
        for s in forecast.signals
    ]
    return LiquidityProjectionOutput(
        outlet_id=outlet_id,
        reserve_type=forecast.reserve_type,
        outlet_provider_account_id=account_id,
        provider_id=provider_id,
        as_of_at=forecast.as_of_at,
        current_balance=forecast.current_balance,
        burn_rate_per_hour=forecast.burn_rate_per_hour,
        projected_shortage_at=forecast.projected_shortage_at,
        lower_bound_at=forecast.lower_bound_at,
        upper_bound_at=forecast.upper_bound_at,
        confidence_score=forecast.confidence_score,
        confidence_level=forecast.confidence_level,
        sample_count=forecast.sample_count,
        is_actionable=forecast.is_actionable,
        non_actionable_reason=forecast.non_actionable_reason,
        signals=signals,
    )


def _quality_to_input(
    result,
    *,
    simulation_run_id: UUID,
    outlet_id: UUID,
    provider_id: UUID,
) -> QualityAssessmentInput:
    return QualityAssessmentInput(
        simulation_run_id=simulation_run_id,
        outlet_id=outlet_id,
        provider_id=provider_id,
        status=result.status,
        confidence_modifier=float(result.confidence_modifier),
        sample_count=result.sample_count,
        latest_source_at=result.latest_source_at,
        assessed_at=datetime.now(timezone.utc),
        engine_version=cfg.QUALITY_ENGINE_VERSION,
        summary=result.summary,
        issues=[
            QualityIssueInput(
                issue_type=i.issue_type,
                severity=i.severity,
                field_name=i.field_name,
                evidence=i.evidence,
            )
            for i in result.issues
        ],
    )
