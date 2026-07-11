"""Phase 4 analytics API request/response envelopes."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.alert_candidate import AlertCandidate
from app.contracts.v1.anomaly import AnomalyFlagOutput
from app.contracts.v1.common import ContractModel, ensure_utc
from app.contracts.v1.liquidity import LiquidityProjectionOutput


class AnalyticsRunRequest(ContractModel):
    simulation_run_id: UUID
    outlet_id: UUID | None = None


class LiquidityProjectionListResponse(ContractModel):
    outlet_id: UUID
    projections: list[LiquidityProjectionOutput] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class LiquidityRunResponse(ContractModel):
    analytics_run_id: UUID
    simulation_run_id: UUID
    engine_version: str
    input_window_start: datetime
    input_window_end: datetime
    projections: list[LiquidityProjectionOutput] = Field(default_factory=list)
    candidates: list[AlertCandidate] = Field(default_factory=list)

    @field_validator("input_window_start", "input_window_end")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class AnomalyFlagListResponse(ContractModel):
    outlet_id: UUID
    flags: list[AnomalyFlagOutput] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class AnomalyRunResponse(ContractModel):
    analytics_run_id: UUID
    simulation_run_id: UUID
    engine_version: str
    input_window_start: datetime
    input_window_end: datetime
    flags: list[AnomalyFlagOutput] = Field(default_factory=list)
    suppressed_count: int = 0
    candidates: list[AlertCandidate] = Field(default_factory=list)

    @field_validator("input_window_start", "input_window_end")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)
