"""Phase 5 alert routes: list/detail/explanations and internal publication."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.coordination import (
    AlertExplanationsResponse,
    AlertListResponse,
    AlertOutput,
    PublishRequest,
    PublishResponse,
)
from app.core.auth import UserContext, require_authenticated
from app.core.authz import require_admin, require_outlet_access
from app.db.session import get_db_session
from app.services.coordination import alerts as alerts_service

router = APIRouter(prefix="/api/v1", tags=["alerts"])


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
    outlet_id: UUID | None = None,
    state: str | None = Query(default="active"),
):
    return await alerts_service.list_alerts(session, user, outlet_id=outlet_id, state=state)


@router.get("/alerts/{alert_id}", response_model=AlertOutput)
async def get_alert(
    alert_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await alerts_service.get_alert(session, user, alert_id)


@router.get("/alerts/{alert_id}/explanations", response_model=AlertExplanationsResponse)
async def get_alert_explanations(
    alert_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await alerts_service.get_explanations(session, user, alert_id)


@router.post(
    "/internal/alerts/publish",
    response_model=PublishResponse,
    status_code=201,
)
async def publish_alerts(
    request: PublishRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    require_admin(user)
    if request.outlet_id is not None:
        await require_outlet_access(session, user, outlet_id=request.outlet_id)
    return await alerts_service.publish_from_run(
        session, user, simulation_run_id=request.simulation_run_id, outlet_id=request.outlet_id
    )
