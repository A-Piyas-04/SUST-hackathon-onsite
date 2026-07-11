"""Phase 5 notification routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.coordination import (
    NotificationListResponse,
    NotificationOutput,
)
from app.core.auth import UserContext, require_authenticated
from app.db.session import get_db_session
from app.db.transaction import transaction
from app.services.coordination import notifications as notifications_service

router = APIRouter(prefix="/api/v1", tags=["notifications"])


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await notifications_service.list_notifications(session, user)


@router.post("/notifications/{notification_id}/read", response_model=NotificationOutput)
async def mark_notification_read(
    notification_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    async with transaction(session):
        return await notifications_service.mark_read(session, user, notification_id)
