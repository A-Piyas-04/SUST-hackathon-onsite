"""Health and readiness endpoints."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.request_context import get_request_id
from app.db.health import check_database_ready
from app.db.session import get_db_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    db_health = await check_database_ready(session)
    status = "ok" if db_health.ready else "degraded"
    return {
        "status": status,
        "app": settings.app_name,
        "environment": settings.app_env,
        "contract_version": settings.contract_version,
        "request_id": get_request_id(),
        "database": {
            "connected": db_health.connected,
            "schema_ok": db_health.schema_ok,
            "ready": db_health.ready,
            "migration_count": db_health.migration_count,
            "error": db_health.error,
        },
    }
