"""Anomaly flag and evidence contracts — docs/schema.md §9.8–9.9."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, ensure_utc, validate_safe_language
from app.contracts.v1.enums import AnomalyDisposition, AnomalyPattern, ConfidenceLevel


class AnomalyEvidenceItem(ContractModel):
    evidence_type: str
    label: str
    value: Any
    display_order: Annotated[int, Field(ge=0)] = 0


class AnomalyFlagOutput(ContractModel):
    anomaly_flag_id: UUID | None = None
    analytics_run_id: UUID | None = None
    anomaly_rule_id: UUID | None = None
    outlet_id: UUID
    provider_id: UUID
    outlet_provider_account_id: UUID
    data_quality_assessment_id: UUID
    window_start: datetime
    window_end: datetime
    pattern: AnomalyPattern
    confidence_score: Annotated[Decimal, Field(ge=0, le=1, decimal_places=4, max_digits=6)]
    confidence_level: ConfidenceLevel
    disposition: AnomalyDisposition
    reason_code: str
    evidence_summary: str
    plausible_benign_explanation: str
    suppression_reason: str | None = None
    evidence_items: list[AnomalyEvidenceItem] = Field(default_factory=list)
    transaction_ids: list[UUID] = Field(default_factory=list)

    @field_validator("window_start", "window_end")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("evidence_summary", "plausible_benign_explanation")
    @classmethod
    def _safe_language(cls, value: str) -> str:
        return validate_safe_language(value, "anomaly text")
