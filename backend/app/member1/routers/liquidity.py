"""Liquidity analytics reads + internal trigger (schema.md Section 16.4)."""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.member1.adapters.alert_candidate import AlertCandidate, build_alert_candidate_from_liquidity
from app.member1.adapters.result_envelope import LiquidityResultEnvelope, validate_result_envelope
from app.member1.schemas.liquidity import LiquidityProjectionOut
from app.member1.services import liquidity_service
from app.shared.deps import get_current_user_stub

router = APIRouter(prefix="/api/v1", tags=["liquidity"])


@router.get("/outlets/{outlet_id}/liquidity-projections", response_model=list[LiquidityProjectionOut])
async def get_liquidity_projections(
    outlet_id: UUID,
    reserve_type: str = Query(..., description="'shared_cash' or 'provider_e_money'"),
    provider_id: UUID | None = Query(default=None, description="Required when reserve_type=provider_e_money."),
    history: bool = Query(default=False, description="False (default) returns only the latest projection per reserve."),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[LiquidityProjectionOut]:
    if reserve_type not in ("shared_cash", "provider_e_money"):
        raise HTTPException(status_code=400, detail={"code": "invalid_reserve_type", "message": "reserve_type must be 'shared_cash' or 'provider_e_money'"})
    if reserve_type == "provider_e_money" and provider_id is None:
        raise HTTPException(status_code=400, detail={"code": "provider_id_required", "message": "provider_id is required when reserve_type=provider_e_money"})

    if history:
        return await liquidity_service.list_projection_history(session, outlet_id, reserve_type=reserve_type, provider_id=provider_id, limit=limit)
    return await liquidity_service.list_latest_projections(session, outlet_id, reserve_type=reserve_type, provider_id=provider_id)


class LiquidityRunAcceptedResponse(BaseModel):
    accepted: bool
    envelope: dict[str, Any]
    derived_alert_candidate: dict[str, Any] | None = None


@router.post("/internal/analytics/liquidity/run", response_model=LiquidityRunAcceptedResponse, status_code=202)
async def trigger_liquidity_run(
    envelope_payload: dict[str, Any],
    _user=Depends(get_current_user_stub),
) -> LiquidityRunAcceptedResponse:
    """Service-only trigger (schema.md 16.4): calculates decision-support
    output only, never moves money or acts on an account.

    # TODO(owner=Member3): replace this stub — Member 3's engine should call
    # `validate_result_envelope` with its real computed output. This route
    # currently just proves the ResultEnvelope -> AlertCandidate seam works
    # end-to-end without persisting (persistence lands in Phase 2+).
    """
    try:
        envelope = validate_result_envelope({**envelope_payload, "engine": "liquidity"})
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_result_envelope", "message": str(exc)}) from exc

    if not isinstance(envelope, LiquidityResultEnvelope):
        raise HTTPException(status_code=422, detail={"code": "invalid_result_envelope", "message": "Expected a liquidity envelope"})

    candidate: AlertCandidate | None = None
    if envelope.is_actionable:
        candidate = build_alert_candidate_from_liquidity(envelope, liquidity_projection_id=uuid4())

    return LiquidityRunAcceptedResponse(
        accepted=True,
        envelope=envelope.model_dump(mode="json"),
        derived_alert_candidate=candidate.model_dump(mode="json") if candidate else None,
    )
