"""Data quality assessment contracts — docs/schema.md §9.1–9.2."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, ensure_utc
from app.contracts.v1.enums import FeedHealthStatus, QualityIssueType, Severity


class QualityIssueInput(ContractModel):
    issue_type: QualityIssueType
    severity: Severity
    field_name: str | None = None
    evidence: dict[str, Any] | None = None


class QualityAssessmentInput(ContractModel):
    data_quality_assessment_id: UUID | None = None
    simulation_run_id: UUID
    ingestion_batch_id: UUID | None = None
    outlet_id: UUID
    provider_id: UUID | None = None
    status: FeedHealthStatus
    confidence_modifier: Annotated[float, Field(ge=0, le=1)]
    sample_count: Annotated[int, Field(ge=0)]
    latest_source_at: datetime | None = None
    assessed_at: datetime
    engine_version: str
    summary: str
    issues: list[QualityIssueInput] = Field(default_factory=list)

    @field_validator("assessed_at")
    @classmethod
    def _utc_assessed(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("latest_source_at")
    @classmethod
    def _utc_latest(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)
