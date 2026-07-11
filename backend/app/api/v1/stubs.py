"""Versioned API stub routers — contract placeholders for later phases.

Phase 3 (reference/ledger), Phase 4 (analytics), and Phase 5 (auth/alerts/cases/
notifications/audit) are now implemented in their own routers. Only endpoints
scheduled for a later phase remain stubbed here.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import UserContext, require_authenticated
from app.core.errors import NotImplementedFeatureError

router = APIRouter(prefix="/api/v1", tags=["stubs-phase7+"])


def _raise(phase: str, feature: str) -> None:
    raise NotImplementedFeatureError(f"{feature} — implemented in Phase {phase}.")


# --- Validation (Phase 7) -----------------------------------------------------
@router.get("/validation/results")
async def validation_results(_user: Annotated[UserContext, Depends(require_authenticated)]):
    _raise("7", "Validation results")
