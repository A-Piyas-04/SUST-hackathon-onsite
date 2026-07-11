"""ResultEnvelope — the Member 3 -> Member 1 ingestion contract.

Owner: Member 1 (contract + acceptance/validation). Member 3 owns the real
forecasting/anomaly/data-quality formulas that produce the *values* carried
inside these envelopes; this module only freezes the *shape*, matching the
tables written in migrations/003_intelligence.sql (schema.md Section 9)
exactly, so Member 3 can start producing real output without a redesign.

# TODO(owner=Member3): populate real `configuration` keys, real computed
# values, and real evidence for LiquidityResultEnvelope / AnomalyResultEnvelope
# / DataQualityResultEnvelope. Everything below is a stub validator + example
# fixture, not a real computation.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field, TypeAdapter, model_validator

from app.shared.enums import (
    AnalyticsEngine,
    AnomalyDisposition,
    AnomalyPattern,
    ConfidenceLevel,
    QualityIssueType,
    ReserveType,
    Severity,
)


class ResultEnvelopeBase(BaseModel):
    """Common reproducibility envelope fields shared by every engine
    (schema.md Section 9.3 `analytics_runs`)."""

    engine_version: str
    simulation_run_id: UUID
    configuration: dict[str, Any] = Field(default_factory=dict)
    input_window_start: datetime
    input_window_end: datetime

    @model_validator(mode="after")
    def _validate_window(self) -> "ResultEnvelopeBase":
        if self.input_window_end < self.input_window_start:
            raise ValueError("input_window_end must be >= input_window_start")
        return self


class LiquidityResultEnvelope(ResultEnvelopeBase):
    """Maps directly onto `liquidity_projections` (schema.md Section 9.4)."""

    engine: Literal[AnalyticsEngine.LIQUIDITY] = AnalyticsEngine.LIQUIDITY
    outlet_id: UUID
    reserve_type: ReserveType
    provider_id: UUID | None = None
    outlet_provider_account_id: UUID | None = None
    current_balance: Decimal = Field(ge=0)
    burn_rate_per_hour: Decimal
    projected_shortage_at: datetime | None = None
    lower_bound_at: datetime | None = None
    upper_bound_at: datetime | None = None
    confidence_score: Decimal = Field(ge=0, le=1)
    confidence_level: ConfidenceLevel
    sample_count: int = Field(ge=0)
    is_actionable: bool
    non_actionable_reason: str | None = None
    primary_data_quality_assessment_id: UUID | None = None

    @model_validator(mode="after")
    def _validate_reserve_scope(self) -> "LiquidityResultEnvelope":
        if self.reserve_type == ReserveType.SHARED_CASH:
            if self.provider_id is not None or self.outlet_provider_account_id is not None:
                raise ValueError("shared_cash projections must not carry a provider_id/outlet_provider_account_id")
        else:
            if self.provider_id is None or self.outlet_provider_account_id is None:
                raise ValueError("provider_e_money projections require both provider_id and outlet_provider_account_id")
        if not self.is_actionable and not self.non_actionable_reason:
            raise ValueError("non_actionable_reason is required when is_actionable=False")
        if self.burn_rate_per_hour <= 0 and (
            self.projected_shortage_at or self.lower_bound_at or self.upper_bound_at
        ):
            raise ValueError("flat/replenishing burn rate (<=0) must not carry a shortage time or confidence bounds")
        return self


class AnomalyResultEnvelope(ResultEnvelopeBase):
    """Maps directly onto `anomaly_flags` (schema.md Section 9.8)."""

    engine: Literal[AnalyticsEngine.ANOMALY] = AnalyticsEngine.ANOMALY
    outlet_id: UUID
    provider_id: UUID
    outlet_provider_account_id: UUID
    anomaly_pattern: AnomalyPattern
    window_start: datetime
    window_end: datetime
    confidence_score: Decimal = Field(ge=0, le=1)
    confidence_level: ConfidenceLevel
    disposition: AnomalyDisposition
    reason_code: str | None = None
    evidence_summary: str
    plausible_benign_explanation: str | None = None
    suppression_reason: str | None = None
    data_quality_assessment_id: UUID
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)
    transaction_ids: list[UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_disposition_fields(self) -> "AnomalyResultEnvelope":
        if self.window_end < self.window_start:
            raise ValueError("window_end must be >= window_start")
        if self.disposition == AnomalyDisposition.SUPPRESSED_DATA_QUALITY and not self.suppression_reason:
            raise ValueError("suppression_reason is required when disposition=suppressed_data_quality")
        if self.disposition != AnomalyDisposition.SUPPRESSED_DATA_QUALITY and not self.plausible_benign_explanation:
            raise ValueError("plausible_benign_explanation is required for actionable (non-suppressed) flags")
        return self


class DataQualityResultEnvelope(ResultEnvelopeBase):
    """Maps directly onto `data_quality_assessments` (+ issues), schema.md
    Section 9.1-9.2."""

    engine: Literal[AnalyticsEngine.DATA_QUALITY] = AnalyticsEngine.DATA_QUALITY
    outlet_id: UUID
    provider_id: UUID
    ingestion_batch_id: UUID | None = None
    status: str = Field(description="feed_health_status: fresh | stale | missing | conflicting")
    confidence_modifier: Decimal = Field(ge=0, le=1)
    sample_count: int = Field(ge=0)
    latest_source_at: datetime | None = None
    summary: str
    issues: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_status(self) -> "DataQualityResultEnvelope":
        allowed = {"fresh", "stale", "missing", "conflicting"}
        if self.status not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return self


ResultEnvelope = Annotated[
    Union[LiquidityResultEnvelope, AnomalyResultEnvelope, DataQualityResultEnvelope],
    Field(discriminator="engine"),
]

_result_envelope_adapter: TypeAdapter[ResultEnvelope] = TypeAdapter(ResultEnvelope)


def validate_result_envelope(raw: dict[str, Any]) -> ResultEnvelope:
    """Stub validator (task Section 5.1 / 01:15 checkpoint). Raises
    `pydantic.ValidationError` on a malformed envelope. Member 1's routers and
    services call this before ever persisting Member 3's output; no
    persistence logic runs here."""
    return _result_envelope_adapter.validate_python(raw)


__all__ = [
    "ResultEnvelopeBase",
    "LiquidityResultEnvelope",
    "AnomalyResultEnvelope",
    "DataQualityResultEnvelope",
    "ResultEnvelope",
    "validate_result_envelope",
]
