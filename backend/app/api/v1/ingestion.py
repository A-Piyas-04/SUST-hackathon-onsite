"""Phase 3 ingestion routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.ingestion import IngestBatchRequest, IngestBatchResponse
from app.core.auth import UserContext, require_authenticated
from app.db.session import get_db_session
from app.db.transaction import transaction
from app.services.ingestion.pipeline import ingest_batch

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])


@router.post("/batches", response_model=IngestBatchResponse, status_code=201)
async def ingest_batch_route(
    request: IngestBatchRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    async with transaction(session):
        return await ingest_batch(session, request)
