from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories import simulation as simulation_repo
from app.member1.schemas.simulation import FaultInjectionOut, ScenarioOut, SimulationRunOut


async def list_scenarios(session: AsyncSession) -> list[ScenarioOut]:
    rows = await simulation_repo.list_scenarios(session)
    return [ScenarioOut(**row) for row in rows]


async def create_simulation_run(session: AsyncSession, *, scenario_code: str, seed: int | None, config: dict[str, Any]) -> SimulationRunOut:
    scenario = await simulation_repo.get_scenario_by_code(session, scenario_code)
    if scenario is None:
        raise HTTPException(status_code=404, detail={"code": "scenario_not_found", "message": f"Unknown scenario_code '{scenario_code}'"})
    row = await simulation_repo.create_simulation_run(
        session,
        scenario_id=scenario["scenario_id"],
        seed=seed if seed is not None else scenario["default_seed"],
        config=config,
    )
    return SimulationRunOut(**row)


async def get_simulation_run(session: AsyncSession, run_id: UUID) -> SimulationRunOut | None:
    row = await simulation_repo.get_simulation_run(session, run_id)
    return SimulationRunOut(**row) if row else None


async def reset_simulation_run(session: AsyncSession, run_id: UUID) -> SimulationRunOut | None:
    # TODO(owner=Member1, Phase 3+): also clear/rewind associated ledger rows
    # for this simulation_run_id once the generator writes real per-run data.
    row = await simulation_repo.mark_simulation_run_reset(session, run_id)
    return SimulationRunOut(**row) if row else None


async def create_fault_injection(
    session: AsyncSession,
    *,
    simulation_run_id: UUID,
    outlet_id: UUID,
    provider_id: UUID | None,
    fault_type: str,
    parameters: dict[str, Any],
    scheduled_at: datetime | None,
) -> FaultInjectionOut:
    row = await simulation_repo.create_fault_injection(
        session,
        simulation_run_id=simulation_run_id,
        outlet_id=outlet_id,
        provider_id=provider_id,
        fault_type=fault_type,
        parameters=parameters,
        scheduled_at=scheduled_at or datetime.now(timezone.utc),
    )
    return FaultInjectionOut(**row)


async def set_fault_injection_enabled(session: AsyncSession, fault_injection_id: UUID, is_enabled: bool) -> FaultInjectionOut | None:
    row = await simulation_repo.set_fault_injection_enabled(session, fault_injection_id, is_enabled)
    return FaultInjectionOut(**row) if row else None
