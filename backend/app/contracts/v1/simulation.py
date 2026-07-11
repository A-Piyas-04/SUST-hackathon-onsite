"""Simulation and fault injection API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, ensure_utc
from app.contracts.v1.enums import FaultType, ScenarioCode, SimulationRunStatus, ValidationSplit
from app.core.auth import OUTLET1


class ScenarioResponse(ContractModel):
    scenario_id: UUID
    code: ScenarioCode
    name: str
    description: str
    default_seed: int
    default_config: dict[str, Any]
    validation_split: ValidationSplit
    is_active: bool


class ScenarioListResponse(ContractModel):
    scenarios: list[ScenarioResponse]


class CreateRunRequest(ContractModel):
    scenario_code: ScenarioCode
    seed: int | None = None
    config_overrides: dict[str, Any] | None = None
    outlet_id: UUID = OUTLET1


class RunArtifactCounts(ContractModel):
    ingestion_batches: int = 0
    ingestion_events: int = 0
    transactions: int = 0
    cash_snapshots: int = 0
    provider_snapshots: int = 0


class FaultSummary(ContractModel):
    fault_injection_id: UUID
    fault_type: FaultType
    outlet_id: UUID
    provider_id: UUID | None = None
    parameters: dict[str, Any]
    is_enabled: bool
    scheduled_at: datetime
    applied_at: datetime | None = None
    ended_at: datetime | None = None

    @field_validator("scheduled_at", "applied_at", "ended_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)


class RunResponse(ContractModel):
    simulation_run_id: UUID
    scenario_id: UUID
    scenario_code: ScenarioCode
    seed: int
    config_snapshot: dict[str, Any]
    status: SimulationRunStatus
    started_by_user_id: UUID | None = None
    started_at: datetime
    completed_at: datetime | None = None
    error_summary: str | None = None
    faults: list[FaultSummary] = Field(default_factory=list)
    artifacts: RunArtifactCounts = Field(default_factory=RunArtifactCounts)

    @field_validator("started_at", "completed_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)


class CreateFaultRequest(ContractModel):
    fault_type: FaultType
    outlet_id: UUID
    provider_id: UUID | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    scheduled_at: datetime | None = None

    @field_validator("scheduled_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)


class PatchFaultRequest(ContractModel):
    is_enabled: bool
