"""AlertCandidate — the Member 1 -> Member 2 submission contract.

Owner: Member 1. This is what Member 1 hands off after validating/persisting
a ResultEnvelope (result_envelope.py). Member 2 turns an AlertCandidate into a
real `alerts` row and (if `requires_case`) opens a `cases` row — Member 1
never creates assignments or changes case state, and that boundary is
enforced by construction: there is intentionally no `status`, `owner`, or
`assignment` field anywhere on this model.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.member1.adapters.result_envelope import (
    AnomalyResultEnvelope,
    LiquidityResultEnvelope,
)
from app.shared.enums import AlertType, AnomalyDisposition, ConfidenceLevel, Severity


class AlertCandidate(BaseModel):
    """Structured, immutable analytical evidence for one candidate alert.

    Deliberately excludes: status, owner, assigned_to, escalation, resolution,
    or any other case-workflow field — those belong exclusively to Member 2's
    `cases` table (migration 004).
    """

    alert_type: AlertType
    outlet_id: UUID
    provider_id: UUID | None = Field(default=None, description="Null only for a shared-cash alert.")
    severity: Severity
    deduplication_key: str = Field(description="Prevents repeated active alerts for the same condition/window.")

    liquidity_projection_ids: list[UUID] = Field(default_factory=list)
    anomaly_flag_ids: list[UUID] = Field(default_factory=list)
    data_quality_assessment_ids: list[UUID] = Field(default_factory=list)

    situation: str
    evidence: str
    uncertainty: str
    next_step: str
    plausible_benign_explanation: str | None = None

    requires_case: bool

    @model_validator(mode="after")
    def _validate_has_source_link(self) -> "AlertCandidate":
        # Invariant #11 (schema.md 13): every published alert cites at least
        # one projection, anomaly flag, or data-quality assessment.
        if not (self.liquidity_projection_ids or self.anomaly_flag_ids or self.data_quality_assessment_ids):
            raise ValueError("an AlertCandidate must cite at least one liquidity projection, anomaly flag, or data-quality assessment")
        return self


def _confidence_to_severity(confidence_level: ConfidenceLevel, *, is_shortage_imminent: bool) -> Severity:
    """Simple, explainable severity heuristic (not Member 3's territory —
    this only maps an already-computed confidence level to a display
    severity for routing purposes)."""
    if not is_shortage_imminent:
        return Severity.INFO
    return {
        ConfidenceLevel.HIGH: Severity.HIGH,
        ConfidenceLevel.MEDIUM: Severity.MEDIUM,
        ConfidenceLevel.LOW: Severity.LOW,
        ConfidenceLevel.UNAVAILABLE: Severity.LOW,
    }[confidence_level]


def build_alert_candidate_from_liquidity(
    envelope: LiquidityResultEnvelope,
    *,
    liquidity_projection_id: UUID,
) -> AlertCandidate:
    """Turns a validated liquidity ResultEnvelope into an AlertCandidate.
    Concrete, working seam function (task Section 5.2 / 01:30 checkpoint)."""
    is_shortage_imminent = envelope.is_actionable and envelope.projected_shortage_at is not None
    severity = _confidence_to_severity(envelope.confidence_level, is_shortage_imminent=is_shortage_imminent)

    scope = "shared cash" if envelope.provider_id is None else "provider e-money"
    if is_shortage_imminent:
        situation = f"Possible liquidity pressure on {scope} requires review."
        evidence = (
            f"Current balance {envelope.current_balance} with a burn rate of "
            f"{envelope.burn_rate_per_hour}/hour projects a shortage around {envelope.projected_shortage_at}."
        )
        next_step = "Review the recent transactions and confirm with the outlet before any operational action."
    else:
        situation = f"{scope.capitalize()} balance is stable; no shortage currently projected."
        evidence = envelope.non_actionable_reason or "Insufficient signal to project a shortage."
        next_step = "No action required; continue routine monitoring."

    uncertainty = {
        ConfidenceLevel.HIGH: "This estimate has high confidence given stable, sufficient recent data.",
        ConfidenceLevel.MEDIUM: "This estimate has moderate confidence; treat the timing as approximate.",
        ConfidenceLevel.LOW: "This estimate has low confidence; treat the timing as a rough estimate only.",
        ConfidenceLevel.UNAVAILABLE: "Confidence is unavailable; data quality is currently degraded for this reserve.",
    }[envelope.confidence_level]

    dedup_scope = envelope.provider_id or "shared_cash"
    return AlertCandidate(
        alert_type=AlertType.LIQUIDITY,
        outlet_id=envelope.outlet_id,
        provider_id=envelope.provider_id,
        severity=severity,
        deduplication_key=f"liquidity:{envelope.outlet_id}:{dedup_scope}",
        liquidity_projection_ids=[liquidity_projection_id],
        situation=situation,
        evidence=evidence,
        uncertainty=uncertainty,
        next_step=next_step,
        plausible_benign_explanation=None,
        requires_case=is_shortage_imminent and severity in (Severity.HIGH, Severity.MEDIUM, Severity.CRITICAL),
    )


def build_alert_candidate_from_anomaly(
    envelope: AnomalyResultEnvelope,
    *,
    anomaly_flag_id: UUID,
) -> AlertCandidate:
    """Turns a validated anomaly ResultEnvelope into an AlertCandidate.
    Suppressed (data-quality-degraded) flags never produce a requires_case
    alert (schema.md invariant #10)."""
    is_suppressed = envelope.disposition == AnomalyDisposition.SUPPRESSED_DATA_QUALITY
    severity = Severity.INFO if is_suppressed else _confidence_to_severity(envelope.confidence_level, is_shortage_imminent=True)

    situation = (
        "Data quality issue detected; new unusual-activity flags are suppressed for this provider."
        if is_suppressed
        else f"Unusual activity detected ({envelope.anomaly_pattern.value.replace('_', ' ')}) — requires review."
    )

    return AlertCandidate(
        alert_type=AlertType.DATA_QUALITY if is_suppressed else AlertType.ANOMALY,
        outlet_id=envelope.outlet_id,
        provider_id=envelope.provider_id,
        severity=severity,
        deduplication_key=f"anomaly:{envelope.outlet_id}:{envelope.provider_id}:{envelope.anomaly_pattern.value}:{envelope.window_start.isoformat()}",
        anomaly_flag_ids=[anomaly_flag_id],
        situation=situation,
        evidence=envelope.evidence_summary,
        uncertainty=envelope.plausible_benign_explanation or "Data quality is currently degraded for this provider.",
        next_step=(
            "Verify the provider feed before drawing any conclusion."
            if is_suppressed
            else "Review the listed synthetic transactions before coordinating any operational follow-up."
        ),
        plausible_benign_explanation=envelope.plausible_benign_explanation,
        requires_case=not is_suppressed,
    )


__all__ = [
    "AlertCandidate",
    "build_alert_candidate_from_liquidity",
    "build_alert_candidate_from_anomaly",
]
