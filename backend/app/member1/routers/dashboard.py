"""Dashboard/ledger reads (schema.md Section 16.2)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.member1.schemas.dashboard import BalanceHistoryEntryOut, DashboardResponse, TransactionOut
from app.member1.services import dashboard_service
from app.shared.deps import get_current_user_stub

router = APIRouter(prefix="/api/v1/outlets", tags=["dashboard"])


@router.get("/{outlet_id}/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    outlet_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> DashboardResponse:
    dashboard = await dashboard_service.get_dashboard(session, outlet_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail={"code": "outlet_not_found", "message": "Outlet not found"})
    return dashboard


@router.get("/{outlet_id}/transactions", response_model=list[TransactionOut])
async def list_transactions(
    outlet_id: UUID,
    provider_id: UUID | None = Query(default=None),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[TransactionOut]:
    return await dashboard_service.list_transactions(session, outlet_id, provider_id=provider_id, from_=from_, to=to, limit=limit)


@router.get("/{outlet_id}/balances/history", response_model=list[BalanceHistoryEntryOut])
async def get_balance_history(
    outlet_id: UUID,
    reserve_type: str = Query(..., description="Required to prevent blended queries: 'shared_cash' or 'provider_e_money'."),
    provider_id: UUID | None = Query(default=None, description="Required when reserve_type=provider_e_money."),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[BalanceHistoryEntryOut]:
    if reserve_type not in ("shared_cash", "provider_e_money"):
        raise HTTPException(status_code=400, detail={"code": "invalid_reserve_type", "message": "reserve_type must be 'shared_cash' or 'provider_e_money'"})
    if reserve_type == "shared_cash":
        return await dashboard_service.list_cash_balance_history(session, outlet_id, from_=from_, to=to, limit=limit)

    if provider_id is None:
        raise HTTPException(status_code=400, detail={"code": "provider_id_required", "message": "provider_id is required when reserve_type=provider_e_money"})
    return await dashboard_service.list_provider_balance_history(session, outlet_id, provider_id, from_=from_, to=to, limit=limit)
