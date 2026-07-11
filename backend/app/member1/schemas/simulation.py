from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.member1.schemas.common import ApiModel


class ScenarioOut(ApiModel):
    scenario_id: UUID
    code: str
    name: str
    description: str
    default_seed: int
    is_active: bool


class SimulationRunOut(ApiModel):
    simulation_run_id: UUID
    scenario_id: UUID
    seed: int
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_summary: str | None = None


class CreateSimulationRunRequest(ApiModel):
    scenario_code: str = Field(description="One of the codes returned by GET /simulations/scenarios.")
    seed: int | None = Field(default=None, description="Defaults to the scenario's default_seed when omitted.")
    config: dict[str, Any] = Field(default_factory=dict)


class FaultInjectionOut(ApiModel):
    fault_injection_id: UUID
    simulation_run_id: UUID
    outlet_id: UUID
    provider_id: UUID | None = None
    fault_type: str
    parameters: dict[str, Any]
    scheduled_at: datetime
    applied_at: datetime | None = None
    ended_at: datetime | None = None
    is_enabled: bool


class CreateFaultInjectionRequest(ApiModel):
    simulation_run_id: UUID
    outlet_id: UUID
    provider_id: UUID | None = None
    fault_type: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    scheduled_at: datetime | None = Field(default=None, description="Defaults to now() when omitted.")


class UpdateFaultInjectionRequest(ApiModel):
    is_enabled: bool
