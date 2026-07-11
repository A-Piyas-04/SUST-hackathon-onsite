"""Phase 7 observability endpoint: GET /metrics (admin/management only).

Combines the signed-off release-candidate identifier, live in-process counters,
and the latest completed validation metrics. Never exposes confidential
provider/outlet data — only aggregate, release-tagged evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.validation import MetricsSummaryResponse, ProcessCounters
from app.core import observability
from app.core.auth import UserContext, require_authenticated
from app.core.authz import require_admin_or_management
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.services.validation import config as vcfg
from app.services.validation import reader as validation_reader

router = APIRouter(tags=["observability"])


@router.get("/metrics", response_model=MetricsSummaryResponse)
async def metrics(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    require_admin_or_management(user)
    counters = observability.snapshot()
    validation_metrics = await validation_reader.latest_summary_metrics(session)
    return MetricsSummaryResponse(
        contract_version=settings.contract_version,
        release_candidate=vcfg.release_candidate(),
        process=ProcessCounters(
            request_count=counters.request_count,
            error_count=counters.error_count,
        ),
        validation_metrics=validation_metrics,
        generated_at=datetime.now(timezone.utc),
    )
