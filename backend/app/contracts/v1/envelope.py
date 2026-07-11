"""ResultEnvelope seam contract — engine output before persistence."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, EvidenceItem, ensure_utc
from app.contracts.v1.enums import AnalyticsEngine, ConfidenceLevel, ReserveType


class LiquidityEngineSpecific(ContractModel):
    reserve_type: ReserveType
    provider_code: str | None = None
    current_balance: Decimal
    burn_rate_per_hour: Decimal
    projected_shortage_at: datetime | None = None
    lower_bound_at: datetime | None = None
    upper_bound_at: datetime | None = None
    sample_count: Annotated[int, Field(ge=0)]
    is_actionable: bool
    non_actionable_reason: str | None = None

    @field_validator(
        "projected_shortage_at", "lower_bound_at", "upper_bound_at", mode="before"
    )
    @classmethod
    def _utc_optional(cls, value: datetime | str | None) -> datetime | None:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return ensure_utc(value)


class AnomalyEngineSpecific(ContractModel):
    pattern: str
    provider_code: str
    window_start: datetime
    window_end: datetime
    disposition: str
    reason_code: str
    evidence_summary: str
    plausible_benign_explanation: str
    suppression_disposition: str
    account_refs: tuple[str, ...] = ()

    @field_validator("window_start", "window_end")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class ResultEnvelope(ContractModel):
    engine: AnalyticsEngine
    engine_version: str
    input_window_start: datetime
    input_window_end: datetime
    quality_assessment_ids: tuple[UUID, ...]
    confidence: Annotated[float, Field(ge=0, le=1)]
    confidence_level: ConfidenceLevel
    evidence: tuple[EvidenceItem, ...]
    generated_at: datetime
    engine_specific: dict[str, Any]

    @field_validator("input_window_start", "input_window_end", "generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)
