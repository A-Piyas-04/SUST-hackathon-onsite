"""Validation metric payload contracts — docs/schema.md §11.3."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, ensure_utc
from app.contracts.v1.enums import MetricCategory, ValidationSplit


class ValidationResultsResponse(ContractModel):
    """List envelope for GET /api/v1/validation/results."""

    runs: list["ValidationMetricPayload"] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class ProcessCounters(ContractModel):
    request_count: int
    error_count: int


class MetricsSummaryResponse(ContractModel):
    """Protected JSON summary for GET /metrics (admin/management only)."""

    contract_version: str
    release_candidate: dict[str, Any]
    process: ProcessCounters
    validation_metrics: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc_summary(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class MetricResultDetail(ContractModel):
    metric_code: str
    category: MetricCategory
    value: Decimal
    unit: str
    sample_size: Annotated[int, Field(gt=0)]
    method: str
    limitations: str
    details: dict[str, Any] | None = None
    computed_at: datetime

    @field_validator("computed_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class ValidationMetricPayload(ContractModel):
    validation_run_id: UUID
    name: str
    dataset_split: ValidationSplit
    engine_version: str
    configuration: dict[str, Any]
    status: Annotated[str, Field(pattern=r"^(running|completed|failed)$")]
    started_at: datetime
    completed_at: datetime | None = None
    metrics: list[MetricResultDetail]

    @field_validator("started_at", "completed_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)


# Resolve the forward reference in ValidationResultsResponse.runs.
ValidationResultsResponse.model_rebuild()
