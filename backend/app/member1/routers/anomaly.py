"""Anomaly analytics reads + internal trigger (schema.md Section 16.4)."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.member1.adapters.alert_candidate import build_alert_candidate_from_anomaly
from app.member1.adapters.result_envelope import AnomalyResultEnvelope, validate_result_envelope
from app.member1.routers.liquidity import LiquidityRunAcceptedResponse
from app.member1.schemas.anomaly import AnomalyFlagDetailOut, AnomalyFlagOut
from app.member1.services import anomaly_service
from app.shared.deps import get_current_user_stub

router = APIRouter(prefix="/api/v1", tags=["anomaly"])


@router.get("/outlets/{outlet_id}/anomaly-flags", response_model=list[AnomalyFlagOut])
async def list_anomaly_flags(
    outlet_id: UUID,
    provider_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[AnomalyFlagOut]:
    return await anomaly_service.list_anomaly_flags(session, outlet_id, provider_id=provider_id, limit=limit)


@router.get("/anomaly-flags/{flag_id}", response_model=AnomalyFlagDetailOut)
async def get_anomaly_flag(
    flag_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> AnomalyFlagDetailOut:
    flag = await anomaly_service.get_anomaly_flag_detail(session, flag_id)
    if flag is None:
        raise HTTPException(status_code=404, detail={"code": "anomaly_flag_not_found", "message": "Anomaly flag not found"})
    return flag


@router.post("/internal/analytics/anomalies/run", response_model=LiquidityRunAcceptedResponse, status_code=202)
async def trigger_anomaly_run(
    envelope_payload: dict[str, Any],
    _user=Depends(get_current_user_stub),
) -> LiquidityRunAcceptedResponse:
    """Service-only trigger (schema.md 16.4). See liquidity.py's
    trigger_liquidity_run docstring for the same TODO(owner=Member3) note —
    identical seam, different engine."""
    try:
        envelope = validate_result_envelope({**envelope_payload, "engine": "anomaly"})
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_result_envelope", "message": str(exc)}) from exc

    if not isinstance(envelope, AnomalyResultEnvelope):
        raise HTTPException(status_code=422, detail={"code": "invalid_result_envelope", "message": "Expected an anomaly envelope"})

    candidate = build_alert_candidate_from_anomaly(envelope, anomaly_flag_id=uuid4())

    return LiquidityRunAcceptedResponse(
        accepted=True,
        envelope=envelope.model_dump(mode="json"),
        derived_alert_candidate=candidate.model_dump(mode="json"),
    )
