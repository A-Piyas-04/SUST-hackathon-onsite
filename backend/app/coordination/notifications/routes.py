"""Notification route scaffolds (schema.md 16.5). Owner: Member 2.

Runtime is Phase 4; handlers return an honest 501. Marking a notification read
is idempotent (Idempotency-Key enforced in Phase 4).
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.coordination.shared.http import not_implemented

notifications_router = APIRouter(prefix="/api/v1/notifications", tags=["coordination:notifications"])


@notifications_router.get("")
async def list_notifications(request: Request):
    return not_implemented("Notification list", request)


@notifications_router.post("/{notification_id}/read")
async def mark_notification_read(request: Request, notification_id: str):
    return not_implemented("Mark notification read", request)
