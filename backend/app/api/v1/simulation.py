"""Phase 3 simulation routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.simulation import (
    CreateFaultRequest,
    CreateRunRequest,
    FaultSummary,
    PatchFaultRequest,
    RunResponse,
    ScenarioListResponse,
)
from app.core.auth import UserContext, require_authenticated
from app.core.authz import require_admin, require_outlet_access
from app.db.session import get_db_session
from app.db.transaction import transaction
from app.services.simulation import fault_service, run_service

router = APIRouter(prefix="/api/v1/simulations", tags=["simulation"])


@router.get("/scenarios", response_model=ScenarioListResponse)
async def list_scenarios(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    require_admin(user)
    return await run_service.list_scenarios(session)


@router.post("/runs", response_model=RunResponse, status_code=201)
async def start_simulation(
    request: CreateRunRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    require_admin(user)
    if request.outlet_id is not None:
        await require_outlet_access(session, user, outlet_id=request.outlet_id)
    async with transaction(session):
        return await run_service.create_run(session, request, user)


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_simulation_run(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    require_admin(user)
    return await run_service.get_run(session, run_id)


@router.post("/runs/{run_id}/reset", response_model=RunResponse)
async def reset_simulation_run(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    require_admin(user)
    async with transaction(session):
        return await run_service.reset_run(session, run_id)


@router.post("/runs/{run_id}/faults", response_model=FaultSummary, status_code=201)
async def create_fault(
    run_id: UUID,
    request: CreateFaultRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    require_admin(user)
    async with transaction(session):
        return await fault_service.create_fault(session, run_id, request, actor_user_id=user.user_id)


@router.patch("/runs/{run_id}/faults/{fault_id}", response_model=FaultSummary)
async def patch_fault(
    run_id: UUID,
    fault_id: UUID,
    request: PatchFaultRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    require_admin(user)
    async with transaction(session):
        return await fault_service.patch_fault(session, run_id, fault_id, request)
