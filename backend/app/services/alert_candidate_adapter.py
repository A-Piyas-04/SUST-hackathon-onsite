"""Transform ResultEnvelope into AlertCandidate — pure seam adapter."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from app.contracts.v1.alert_candidate import AlertCandidate, AlertSourceLinks
from app.contracts.v1.common import EvidenceItem
from app.contracts.v1.enums import (
    AlertType,
    AnalyticsEngine,
    ConfidenceLevel,
    ReserveType,
    Severity,
)
from app.contracts.v1.envelope import AnomalyEngineSpecific, LiquidityEngineSpecific, ResultEnvelope

_PROVIDER_CODE_TO_ID = {
    "bkash": UUID("11111111-1111-1111-1111-111111111111"),
    "nagad": UUID("22222222-2222-2222-2222-222222222222"),
    "rocket": UUID("33333333-3333-3333-3333-333333333333"),
}


def _severity_for_confidence(level: ConfidenceLevel) -> Severity:
    return {
        ConfidenceLevel.HIGH: Severity.HIGH,
        ConfidenceLevel.MEDIUM: Severity.MEDIUM,
        ConfidenceLevel.LOW: Severity.LOW,
        ConfidenceLevel.UNAVAILABLE: Severity.INFO,
    }[level]


def _liquidity_candidate(
    envelope: ResultEnvelope,
    *,
    outlet_id: UUID,
    provider_id: UUID | None,
) -> AlertCandidate | None:
    specific = LiquidityEngineSpecific.model_validate(envelope.engine_specific)
    if not specific.is_actionable or specific.projected_shortage_at is None:
        return None
    reserve_key = (
        f"provider:{provider_id}" if provider_id else "shared_cash"
    )
    dedup = (
        f"liquidity:{outlet_id}:{reserve_key}:"
        f"{envelope.input_window_end.isoformat()}"
    )
    return AlertCandidate(
        outlet_id=outlet_id,
        provider_id=provider_id,
        alert_type=AlertType.LIQUIDITY,
        severity=_severity_for_confidence(envelope.confidence_level),
        confidence=Decimal(str(envelope.confidence)),
        confidence_level=envelope.confidence_level,
        detected_at=envelope.generated_at,
        deduplication_key=dedup,
        requires_case=True,
        is_alertable=True,
        evidence_summary=(
            f"Projected reserve shortage based on recent outflow rate of "
            f"{specific.burn_rate_per_hour} per hour."
        ),
        recommended_next_step=(
            "Review the liquidity projection and coordinate operational support "
            "through the authorized process."
        ),
        source_links=AlertSourceLinks(quality_assessment_ids=envelope.quality_assessment_ids),
        structured_evidence=envelope.evidence,
        title_key="alert.liquidity.shortage",
    )


def _anomaly_candidate(
    envelope: ResultEnvelope,
    *,
    outlet_id: UUID,
) -> AlertCandidate | None:
    specific = AnomalyEngineSpecific.model_validate(envelope.engine_specific)
    if specific.disposition in {"inconclusive", "suppressed_data_quality"}:
        return None
    if specific.disposition != "requires_review":
        return None
    provider_id = _PROVIDER_CODE_TO_ID.get(specific.provider_code)
    dedup = (
        f"anomaly:{outlet_id}:{specific.provider_code}:"
        f"{specific.pattern}:{envelope.input_window_end.isoformat()}"
    )
    return AlertCandidate(
        outlet_id=outlet_id,
        provider_id=provider_id,
        alert_type=AlertType.ANOMALY,
        severity=_severity_for_confidence(envelope.confidence_level),
        confidence=Decimal(str(envelope.confidence)),
        confidence_level=envelope.confidence_level,
        detected_at=envelope.generated_at,
        deduplication_key=dedup,
        requires_case=True,
        is_alertable=True,
        evidence_summary=specific.evidence_summary,
        recommended_next_step=(
            "Review the listed synthetic transactions and contact the outlet "
            "through the authorized process."
        ),
        plausible_benign_explanation=specific.plausible_benign_explanation,
        source_links=AlertSourceLinks(quality_assessment_ids=envelope.quality_assessment_ids),
        structured_evidence=envelope.evidence,
        title_key="alert.anomaly.unusual_activity",
    )


def envelope_to_alert_candidate(
    envelope: ResultEnvelope,
    *,
    outlet_id: UUID,
    provider_id: UUID | None = None,
) -> AlertCandidate | None:
    """Map an engine ResultEnvelope to a pre-alert candidate without case fields."""
    if envelope.engine == AnalyticsEngine.LIQUIDITY:
        specific = LiquidityEngineSpecific.model_validate(envelope.engine_specific)
        resolved_provider = provider_id
        if specific.reserve_type == ReserveType.PROVIDER_E_MONEY and specific.provider_code:
            resolved_provider = _PROVIDER_CODE_TO_ID.get(specific.provider_code, provider_id)
        elif specific.reserve_type == ReserveType.SHARED_CASH:
            resolved_provider = None
        return _liquidity_candidate(envelope, outlet_id=outlet_id, provider_id=resolved_provider)
    if envelope.engine == AnalyticsEngine.ANOMALY:
        return _anomaly_candidate(envelope, outlet_id=outlet_id)
    return None
