"""Phase 4 analytics routes: liquidity projections and anomaly flags."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.analytics_responses import (
    AnalyticsRunRequest,
    AnomalyFlagListResponse,
    AnomalyRunResponse,
    LiquidityProjectionListResponse,
    LiquidityRunResponse,
)
from app.contracts.v1.anomaly import AnomalyFlagOutput
from app.core.auth import UserContext, require_authenticated
from app.core.authz import (
    SafeNotFoundError,
    authorized_provider_ids,
    can_access_scope,
    require_admin,
    require_outlet_access,
)
from app.db.session import get_db_session
from app.db.transaction import transaction
from app.services.analytics import reader as analytics_reader
from app.services.analytics import runner as analytics_runner

router = APIRouter(prefix="/api/v1", tags=["analytics"])


def _require_admin_user(user: Annotated[UserContext, Depends(require_authenticated)]) -> UserContext:
    require_admin(user)
    return user


def _filter_projections(response, allowed: list[UUID] | None):
    if allowed is None:
        return response
    allowed_set = set(allowed)
    filtered = [
        p
        for p in response.projections
        if p.provider_id is None or p.provider_id in allowed_set
    ]
    return response.model_copy(update={"projections": filtered})


def _filter_flags(response, allowed: list[UUID] | None):
    if allowed is None:
        return response
    allowed_set = set(allowed)
    filtered = [f for f in response.flags if f.provider_id in allowed_set]
    return response.model_copy(update={"flags": filtered})


@router.get(
    "/outlets/{outlet_id}/liquidity-projections",
    response_model=LiquidityProjectionListResponse,
)
async def liquidity_projections(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    await require_outlet_access(session, user, outlet_id=outlet_id)
    response = await analytics_reader.list_liquidity_projections(session, outlet_id)
    allowed = await authorized_provider_ids(session, user, outlet_id=outlet_id)
    return _filter_projections(response, allowed)


@router.post(
    "/internal/analytics/liquidity/run",
    response_model=LiquidityRunResponse,
    status_code=201,
    dependencies=[Depends(_require_admin_user)],
)
async def run_liquidity_analytics(
    request: AnalyticsRunRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    if request.outlet_id is not None:
        await require_outlet_access(session, user, outlet_id=request.outlet_id)
    async with transaction(session):
        return await analytics_runner.run_liquidity(
            session,
            simulation_run_id=request.simulation_run_id,
            outlet_id=request.outlet_id,
        )


@router.get(
    "/outlets/{outlet_id}/anomaly-flags",
    response_model=AnomalyFlagListResponse,
)
async def anomaly_flags(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    await require_outlet_access(session, user, outlet_id=outlet_id)
    response = await analytics_reader.list_anomaly_flags(session, outlet_id)
    allowed = await authorized_provider_ids(session, user, outlet_id=outlet_id)
    return _filter_flags(response, allowed)


@router.get("/anomaly-flags/{flag_id}", response_model=AnomalyFlagOutput)
async def anomaly_flag_detail(
    flag_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    flag = await analytics_reader.get_anomaly_flag(session, flag_id)
    if not await can_access_scope(
        session,
        user,
        outlet_id=flag.outlet_id,
        provider_id=flag.provider_id,
    ):
        raise SafeNotFoundError("Anomaly flag")
    return flag


@router.post(
    "/internal/analytics/anomalies/run",
    response_model=AnomalyRunResponse,
    status_code=201,
    dependencies=[Depends(_require_admin_user)],
)
async def run_anomaly_analytics(
    request: AnalyticsRunRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    if request.outlet_id is not None:
        await require_outlet_access(session, user, outlet_id=request.outlet_id)
    async with transaction(session):
        return await analytics_runner.run_anomalies(
            session,
            simulation_run_id=request.simulation_run_id,
            outlet_id=request.outlet_id,
        )
