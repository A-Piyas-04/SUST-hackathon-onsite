"""Phase 3 reference, dashboard, and ledger read routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import ProviderCode, ReserveType
from app.contracts.v1.ledger import (
    BalanceHistoryResponse,
    DataQualityHistoryResponse,
    DataQualityResponse,
    OutletDetailResponse,
    OutletListItem,
    ProviderRef,
    TransactionListResponse,
)
from app.contracts.v1.responses import DashboardResponse
from app.core.auth import UserContext, require_authenticated
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services.ledger import reader as ledger_reader
from app.services.quality import foundation as quality_foundation

router = APIRouter(prefix="/api/v1", tags=["reference-ledger"])


@router.get("/providers", response_model=list[ProviderRef])
async def list_providers(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await ledger_reader.list_providers(session)


@router.get("/areas")
async def list_areas(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await ledger_reader.list_areas(session)


@router.get("/outlets", response_model=list[OutletListItem])
async def list_outlets(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await ledger_reader.list_outlets(session)


@router.get("/outlets/{outlet_id}", response_model=OutletDetailResponse)
async def get_outlet(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await ledger_reader.get_outlet_detail(session, outlet_id)


@router.get("/outlets/{outlet_id}/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await ledger_reader.get_dashboard(session, outlet_id)


@router.get("/outlets/{outlet_id}/transactions", response_model=TransactionListResponse)
async def list_transactions(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
    provider_code: ProviderCode | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    return await ledger_reader.list_transactions(
        session, outlet_id, provider_code=provider_code, limit=limit
    )


@router.get("/outlets/{outlet_id}/balances/history", response_model=BalanceHistoryResponse)
async def balance_history(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
    reserve_type: ReserveType | None = None,
    provider_code: ProviderCode | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    if reserve_type is None:
        raise AppError(
            "validation_error",
            "reserve_type query parameter is required.",
            status_code=422,
            details={"field": "reserve_type"},
        )
    return await ledger_reader.balance_history(
        session, outlet_id, reserve_type, provider_code=provider_code, limit=limit
    )


@router.get("/outlets/{outlet_id}/data-quality", response_model=DataQualityResponse)
async def current_data_quality(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await quality_foundation.get_current_data_quality(session, outlet_id)


@router.get("/outlets/{outlet_id}/data-quality/history", response_model=DataQualityHistoryResponse)
async def data_quality_history(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await quality_foundation.get_data_quality_history(session, outlet_id)
