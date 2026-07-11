from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.member1.schemas.common import ApiModel


class IngestionEventIn(ApiModel):
    event_type: str
    source_event_ref: str
    source_observed_at: datetime | None = None
    safe_payload: dict[str, Any]


class CreateIngestionBatchRequest(ApiModel):
    simulation_run_id: UUID
    outlet_id: UUID
    provider_id: UUID
    source_batch_ref: str
    source_generated_at: datetime | None = None
    events: list[IngestionEventIn] = Field(default_factory=list)


class IngestionBatchOut(ApiModel):
    ingestion_batch_id: UUID
    simulation_run_id: UUID
    outlet_id: UUID
    provider_id: UUID
    source_batch_ref: str
    received_at: datetime
    expected_event_count: int
    received_event_count: int
    rejected_event_count: int
    normalization_status: str


class DataQualityIssueOut(ApiModel):
    issue_type: str
    severity: str
    field_name: str | None = None


class FeedHealthOut(ApiModel):
    data_quality_assessment_id: UUID
    outlet_id: UUID
    provider_id: UUID
    status: str
    confidence_modifier: float
    sample_count: int
    latest_source_at: datetime | None = None
    assessed_at: datetime
    summary: str
    issues: list[DataQualityIssueOut] = Field(default_factory=list)
