"""Alert route scaffolds (schema.md 16.5).

Owner: Member 2. Read endpoints + idempotent case-open. Runtime is Phase 2/3;
handlers return an honest 501. Note: there is deliberately NO alert-mutation
endpoint — published analytical content is immutable.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.coordination.shared.http import not_implemented

alerts_router = APIRouter(prefix="/api/v1/alerts", tags=["coordination:alerts"])


@alerts_router.get("")
async def list_alerts(request: Request):
    return not_implemented("Alert list", request)


@alerts_router.get("/{alert_id}")
async def get_alert(request: Request, alert_id: str):
    return not_implemented("Alert detail", request)


@alerts_router.get("/{alert_id}/explanations")
async def get_alert_explanations(request: Request, alert_id: str):
    return not_implemented("Alert explanations", request)


@alerts_router.post("/{alert_id}/cases")
async def open_case_for_alert(request: Request, alert_id: str):
    # Requires Idempotency-Key (enforced in Phase 3 via shared.idempotency).
    return not_implemented("Open case for alert", request)
