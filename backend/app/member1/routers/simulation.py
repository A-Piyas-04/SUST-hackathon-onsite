"""Simulation control-plane (schema.md Section 16.3)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.member1.schemas.simulation import (
    CreateFaultInjectionRequest,
    CreateSimulationRunRequest,
    FaultInjectionOut,
    ScenarioOut,
    SimulationRunOut,
    UpdateFaultInjectionRequest,
)
from app.member1.services import simulation_service
from app.shared.deps import get_current_user_stub

router = APIRouter(prefix="/api/v1/simulations", tags=["simulation"])


@router.get("/scenarios", response_model=list[ScenarioOut])
async def list_scenarios(
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[ScenarioOut]:
    return await simulation_service.list_scenarios(session)


@router.post("/runs", response_model=SimulationRunOut, status_code=201)
async def create_simulation_run(
    payload: CreateSimulationRunRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> SimulationRunOut:
    # TODO(owner=Member1, Phase 3+): honor Idempotency-Key by looking up a
    # prior response for this key before creating a new run.
    return await simulation_service.create_simulation_run(session, scenario_code=payload.scenario_code, seed=payload.seed, config=payload.config)


@router.get("/runs/{run_id}", response_model=SimulationRunOut)
async def get_simulation_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> SimulationRunOut:
    run = await simulation_service.get_simulation_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail={"code": "simulation_run_not_found", "message": "Simulation run not found"})
    return run


@router.post("/runs/{run_id}/reset", response_model=SimulationRunOut)
async def reset_simulation_run(
    run_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> SimulationRunOut:
    run = await simulation_service.reset_simulation_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail={"code": "simulation_run_not_found", "message": "Simulation run not found"})
    return run


@router.post("/runs/{run_id}/faults", response_model=FaultInjectionOut, status_code=201)
async def create_fault_injection(
    run_id: UUID,
    payload: CreateFaultInjectionRequest,
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> FaultInjectionOut:
    if payload.simulation_run_id != run_id:
        raise HTTPException(status_code=400, detail={"code": "run_id_mismatch", "message": "Path run_id must match body simulation_run_id"})
    return await simulation_service.create_fault_injection(
        session,
        simulation_run_id=payload.simulation_run_id,
        outlet_id=payload.outlet_id,
        provider_id=payload.provider_id,
        fault_type=payload.fault_type,
        parameters=payload.parameters,
        scheduled_at=payload.scheduled_at,
    )


@router.patch("/runs/{run_id}/faults/{fault_id}", response_model=FaultInjectionOut)
async def update_fault_injection(
    run_id: UUID,  # noqa: ARG001 - present for URL symmetry with schema.md; scope check is a TODO for Member2's RBAC layer
    fault_id: UUID,
    payload: UpdateFaultInjectionRequest,
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> FaultInjectionOut:
    fault = await simulation_service.set_fault_injection_enabled(session, fault_id, payload.is_enabled)
    if fault is None:
        raise HTTPException(status_code=404, detail={"code": "fault_injection_not_found", "message": "Fault injection not found"})
    return fault
