"""Read repositories for persisted analytical results (projections, flags)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.analytics_responses import (
    AnomalyFlagListResponse,
    LiquidityProjectionListResponse,
)
from app.contracts.v1.anomaly import AnomalyEvidenceItem, AnomalyFlagOutput
from app.contracts.v1.enums import (
    AnomalyDisposition,
    AnomalyPattern,
    ConfidenceLevel,
    ReserveType,
)
from app.contracts.v1.liquidity import LiquidityProjectionOutput, LiquiditySignal
from app.core.errors import AppError


async def _signals_for(session: AsyncSession, projection_id: UUID) -> list[LiquiditySignal]:
    result = await session.execute(
        text(
            """
            SELECT signal_code, label, numeric_value, unit, direction, details, display_order
            FROM liquidity_signals
            WHERE liquidity_projection_id = :id
            ORDER BY display_order
            """
        ),
        {"id": projection_id},
    )
    return [
        LiquiditySignal(
            signal_code=r["signal_code"],
            label=r["label"],
            numeric_value=r["numeric_value"],
            unit=r["unit"],
            direction=r["direction"],
            details=r["details"],
            display_order=r["display_order"],
        )
        for r in result.mappings().all()
    ]


async def list_liquidity_projections(
    session: AsyncSession, outlet_id: UUID
) -> LiquidityProjectionListResponse:
    result = await session.execute(
        text(
            """
            SELECT * FROM v_latest_liquidity_projections
            WHERE outlet_id = :outlet_id
            ORDER BY reserve_type, provider_id NULLS FIRST
            """
        ),
        {"outlet_id": outlet_id},
    )
    projections: list[LiquidityProjectionOutput] = []
    for r in result.mappings().all():
        signals = await _signals_for(session, r["liquidity_projection_id"])
        projections.append(
            LiquidityProjectionOutput(
                liquidity_projection_id=r["liquidity_projection_id"],
                analytics_run_id=r["analytics_run_id"],
                outlet_id=r["outlet_id"],
                reserve_type=ReserveType(r["reserve_type"]),
                outlet_provider_account_id=r["outlet_provider_account_id"],
                provider_id=r["provider_id"],
                as_of_at=r["as_of_at"],
                current_balance=r["current_balance"],
                burn_rate_per_hour=r["burn_rate_per_hour"],
                projected_shortage_at=r["projected_shortage_at"],
                lower_bound_at=r["lower_bound_at"],
                upper_bound_at=r["upper_bound_at"],
                confidence_score=r["confidence_score"],
                confidence_level=ConfidenceLevel(r["confidence_level"]),
                sample_count=r["sample_count"],
                is_actionable=r["is_actionable"],
                non_actionable_reason=r["non_actionable_reason"],
                signals=signals,
            )
        )
    return LiquidityProjectionListResponse(
        outlet_id=outlet_id,
        projections=projections,
        generated_at=datetime.now(timezone.utc),
    )


async def _build_flag(session: AsyncSession, row) -> AnomalyFlagOutput:
    evidence_result = await session.execute(
        text(
            """
            SELECT evidence_type, label, value, display_order
            FROM anomaly_evidence_items
            WHERE anomaly_flag_id = :id
            ORDER BY display_order
            """
        ),
        {"id": row["anomaly_flag_id"]},
    )
    evidence_items = [
        AnomalyEvidenceItem(
            evidence_type=e["evidence_type"],
            label=e["label"],
            value=e["value"],
            display_order=e["display_order"],
        )
        for e in evidence_result.mappings().all()
    ]
    txn_result = await session.execute(
        text(
            "SELECT transaction_id FROM anomaly_flag_transactions WHERE anomaly_flag_id = :id"
        ),
        {"id": row["anomaly_flag_id"]},
    )
    transaction_ids = [t["transaction_id"] for t in txn_result.mappings().all()]
    return AnomalyFlagOutput(
        anomaly_flag_id=row["anomaly_flag_id"],
        analytics_run_id=row["analytics_run_id"],
        anomaly_rule_id=row["anomaly_rule_id"],
        outlet_id=row["outlet_id"],
        provider_id=row["provider_id"],
        outlet_provider_account_id=row["outlet_provider_account_id"],
        data_quality_assessment_id=row["data_quality_assessment_id"],
        window_start=row["window_start"],
        window_end=row["window_end"],
        pattern=AnomalyPattern(row["pattern"]),
        confidence_score=row["confidence_score"],
        confidence_level=ConfidenceLevel(row["confidence_level"]),
        disposition=AnomalyDisposition(row["disposition"]),
        reason_code=row["reason_code"],
        evidence_summary=row["evidence_summary"],
        plausible_benign_explanation=row["plausible_benign_explanation"] or "",
        suppression_reason=row["suppression_reason"],
        evidence_items=evidence_items,
        transaction_ids=transaction_ids,
    )


_FLAG_SELECT = """
    SELECT af.*, ar.pattern AS pattern
    FROM anomaly_flags af
    JOIN anomaly_rules ar ON ar.anomaly_rule_id = af.anomaly_rule_id
"""


async def list_anomaly_flags(
    session: AsyncSession, outlet_id: UUID
) -> AnomalyFlagListResponse:
    result = await session.execute(
        text(_FLAG_SELECT + " WHERE af.outlet_id = :outlet_id ORDER BY af.window_end DESC"),
        {"outlet_id": outlet_id},
    )
    flags = [await _build_flag(session, r) for r in result.mappings().all()]
    return AnomalyFlagListResponse(
        outlet_id=outlet_id, flags=flags, generated_at=datetime.now(timezone.utc)
    )


async def get_anomaly_flag(session: AsyncSession, flag_id: UUID) -> AnomalyFlagOutput:
    result = await session.execute(
        text(_FLAG_SELECT + " WHERE af.anomaly_flag_id = :id"),
        {"id": flag_id},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError("not_found", f"Anomaly flag {flag_id} not found.", status_code=404)
    return await _build_flag(session, row)
