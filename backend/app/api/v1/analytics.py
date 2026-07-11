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
from app.db.session import get_db_session
from app.db.transaction import transaction
from app.services.analytics import reader as analytics_reader
from app.services.analytics import runner as analytics_runner

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get(
    "/outlets/{outlet_id}/liquidity-projections",
    response_model=LiquidityProjectionListResponse,
)
async def liquidity_projections(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await analytics_reader.list_liquidity_projections(session, outlet_id)


@router.post(
    "/internal/analytics/liquidity/run",
    response_model=LiquidityRunResponse,
    status_code=201,
)
async def run_liquidity_analytics(
    request: AnalyticsRunRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
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
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await analytics_reader.list_anomaly_flags(session, outlet_id)


@router.get("/anomaly-flags/{flag_id}", response_model=AnomalyFlagOutput)
async def anomaly_flag_detail(
    flag_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await analytics_reader.get_anomaly_flag(session, flag_id)


@router.post(
    "/internal/analytics/anomalies/run",
    response_model=AnomalyRunResponse,
    status_code=201,
)
async def run_anomaly_analytics(
    request: AnalyticsRunRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    async with transaction(session):
        return await analytics_runner.run_anomalies(
            session,
            simulation_run_id=request.simulation_run_id,
            outlet_id=request.outlet_id,
        )
