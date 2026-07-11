"""Phase 7 validation results endpoint (admin/management read grant only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.validation import ValidationResultsResponse
from app.core.auth import UserContext, require_authenticated
from app.core.authz import require_admin_or_management
from app.db.session import get_db_session
from app.services.validation import reader as validation_reader

router = APIRouter(prefix="/api/v1", tags=["validation"])


@router.get("/validation/results", response_model=ValidationResultsResponse)
async def validation_results(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
    validation_run_id: UUID | None = None,
    dataset_split: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    """Persisted held-out validation runs with nested metric results.

    Reads from ``validation_runs`` + ``metric_results`` (never hard-coded JSON).
    Agent/ops/provider/risk roles receive 403.
    """
    require_admin_or_management(user)
    runs = await validation_reader.list_validation_runs(
        session,
        validation_run_id=validation_run_id,
        dataset_split=dataset_split,
        status=status,
    )
    return ValidationResultsResponse(
        runs=runs, generated_at=datetime.now(timezone.utc)
    )
