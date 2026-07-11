"""Ingestion batch API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, ensure_utc
from app.contracts.v1.enums import FeedEventType, NormalizationStatus, ProviderCode, RejectionCode


class IngestEventInput(ContractModel):
    event_type: FeedEventType
    source_event_ref: str
    source_observed_at: datetime | None = None
    payload: dict[str, Any]

    @field_validator("source_observed_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)


class IngestBatchRequest(ContractModel):
    simulation_run_id: UUID
    outlet_id: UUID
    provider_code: ProviderCode
    source_batch_ref: str
    source_generated_at: datetime | None = None
    events: Annotated[list[IngestEventInput], Field(min_length=1)]

    @field_validator("source_generated_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)


class IngestEventSummary(ContractModel):
    ingestion_event_id: UUID
    source_event_ref: str
    event_type: FeedEventType
    normalization_status: NormalizationStatus
    rejection_code: RejectionCode | None = None
    rejection_detail: str | None = None


class IngestBatchResponse(ContractModel):
    ingestion_batch_id: UUID
    simulation_run_id: UUID
    outlet_id: UUID
    provider_code: ProviderCode
    source_batch_ref: str
    expected_event_count: int
    received_event_count: int
    rejected_event_count: int
    normalization_status: NormalizationStatus
    events: list[IngestEventSummary]
