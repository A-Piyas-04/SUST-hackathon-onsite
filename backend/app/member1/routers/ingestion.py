"""Ingestion and data-quality reads (schema.md Section 16.3)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.member1.schemas.ingestion import CreateIngestionBatchRequest, FeedHealthOut, IngestionBatchOut
from app.member1.services import ingestion_service
from app.shared.deps import get_current_user_stub

router = APIRouter(prefix="/api/v1", tags=["ingestion"])


@router.post("/ingestion/batches", response_model=IngestionBatchOut, status_code=201)
async def create_ingestion_batch(
    payload: CreateIngestionBatchRequest,
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> IngestionBatchOut:
    """Admin/service only (schema.md 16.3) — RBAC enforcement is
    Member 2's TODO; this route is reachable via the stub dependency in
    Phase 1."""
    return await ingestion_service.create_ingestion_batch(session, payload)


@router.get("/outlets/{outlet_id}/data-quality", response_model=list[FeedHealthOut])
async def get_data_quality(
    outlet_id: UUID,
    provider_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[FeedHealthOut]:
    return await ingestion_service.get_current_feed_health(session, outlet_id, provider_id=provider_id)


@router.get("/outlets/{outlet_id}/data-quality/history", response_model=list[FeedHealthOut])
async def get_data_quality_history(
    outlet_id: UUID,
    provider_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[FeedHealthOut]:
    return await ingestion_service.get_feed_health_history(session, outlet_id, provider_id=provider_id, limit=limit)
