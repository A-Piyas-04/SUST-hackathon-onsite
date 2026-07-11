"""Health, metrics, validation (schema.md Section 16.6)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import check_db_connection, get_session
from app.member1.schemas.ops import HealthResponse, MetricsResponse, ValidationResultsResponse
from app.member1.services import validation_service

router = APIRouter(tags=["ops"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness + database readiness only; no confidential details
    (schema.md 16.6)."""
    db_ok = await check_db_connection()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database="ok" if db_ok else "unreachable",
        env=settings.ENV,
        checked_at=datetime.now(timezone.utc),
    )


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(session: AsyncSession = Depends(get_session)) -> MetricsResponse:
    """Protected JSON summary for the demo (schema.md 16.6). Real auth
    protection is Member 2's TODO; unauthenticated in Phase 1."""
    results = await validation_service.get_validation_metrics(session)
    return MetricsResponse(metrics=results, generated_at=datetime.now(timezone.utc))


@router.get("/api/v1/validation/results", response_model=ValidationResultsResponse)
async def validation_results(session: AsyncSession = Depends(get_session)) -> ValidationResultsResponse:
    results = await validation_service.get_validation_metrics(session)
    return ValidationResultsResponse(results=results, generated_at=datetime.now(timezone.utc))
