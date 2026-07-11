"""Phase 3 reference, dashboard, and ledger read routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
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
from app.core.authz import (
    ForbiddenError,
    authorized_outlet_ids,
    authorized_provider_ids,
    provider_can_read_transactions,
    require_outlet_access,
    require_provider_access,
)
from app.core.errors import AppError
from app.db.session import get_db_session
from app.services.constants import PROVIDER_IDS
from app.services.ledger import reader as ledger_reader
from app.services.quality import foundation as quality_foundation

router = APIRouter(prefix="/api/v1", tags=["reference-ledger"])


async def _filter_providers(
    session: AsyncSession, user: UserContext, providers: list[ProviderRef]
) -> list[ProviderRef]:
    allowed = await authorized_provider_ids(session, user)
    if allowed is None:
        return providers
    allowed_set = set(allowed)
    return [p for p in providers if p.provider_id in allowed_set]


async def _filter_outlets(
    session: AsyncSession, user: UserContext, outlets: list[OutletListItem]
) -> list[OutletListItem]:
    allowed = await authorized_outlet_ids(session, user)
    if allowed is None:
        return outlets
    allowed_set = set(allowed)
    return [o for o in outlets if o.outlet_id in allowed_set]


def _filter_dashboard_providers(
    dashboard: DashboardResponse, allowed: list[UUID] | None
) -> DashboardResponse:
    if allowed is None:
        return dashboard
    allowed_codes = {code.value for code, pid in PROVIDER_IDS.items() if pid in set(allowed)}
    filtered = [p for p in dashboard.providers if p.provider.code.value in allowed_codes]
    return dashboard.model_copy(update={"providers": filtered})


@router.get("/providers", response_model=list[ProviderRef])
async def list_providers(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    providers = await ledger_reader.list_providers(session)
    return await _filter_providers(session, user, providers)


@router.get("/areas")
async def list_areas(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    areas = await ledger_reader.list_areas(session)
    allowed_outlets = await authorized_outlet_ids(session, user)
    if allowed_outlets is None:
        return areas
    allowed_area_ids = {
        row[0]
        for row in (
            await session.execute(
                text("SELECT DISTINCT area_id FROM outlets WHERE outlet_id = ANY(:ids)"),
                {"ids": allowed_outlets},
            )
        ).all()
    }
    return [a for a in areas if a.area_id in allowed_area_ids]


@router.get("/outlets", response_model=list[OutletListItem])
async def list_outlets(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    outlets = await ledger_reader.list_outlets(session)
    return await _filter_outlets(session, user, outlets)


@router.get("/outlets/{outlet_id}", response_model=OutletDetailResponse)
async def get_outlet(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    await require_outlet_access(session, user, outlet_id=outlet_id)
    return await ledger_reader.get_outlet_detail(session, outlet_id)


@router.get("/outlets/{outlet_id}/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    await require_outlet_access(session, user, outlet_id=outlet_id)
    dashboard = await ledger_reader.get_dashboard(session, outlet_id)
    allowed = await authorized_provider_ids(session, user, outlet_id=outlet_id)
    return _filter_dashboard_providers(dashboard, allowed)


@router.get("/outlets/{outlet_id}/transactions", response_model=TransactionListResponse)
async def list_transactions(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
    provider_code: ProviderCode | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    await require_outlet_access(session, user, outlet_id=outlet_id)
    if not await provider_can_read_transactions(session, user, outlet_id=outlet_id):
        raise ForbiddenError("Your role cannot read raw provider transactions.")
    if provider_code is not None:
        provider_id = PROVIDER_IDS[provider_code]
        await require_provider_access(
            session, user, provider_id=provider_id, outlet_id=outlet_id
        )
    response = await ledger_reader.list_transactions(
        session, outlet_id, provider_code=provider_code, limit=limit
    )
    allowed = await authorized_provider_ids(session, user, outlet_id=outlet_id)
    if allowed is None:
        return response
    allowed_codes = {code.value for code, pid in PROVIDER_IDS.items() if pid in set(allowed)}
    filtered = [t for t in response.transactions if t.provider.value in allowed_codes]
    return response.model_copy(
        update={"transactions": filtered, "total": len(filtered)}
    )


@router.get("/outlets/{outlet_id}/balances/history", response_model=BalanceHistoryResponse)
async def balance_history(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
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
    await require_outlet_access(session, user, outlet_id=outlet_id)
    if reserve_type == ReserveType.PROVIDER_E_MONEY:
        if not await provider_can_read_transactions(session, user, outlet_id=outlet_id):
            raise ForbiddenError("Your role cannot read provider balance history.")
        if provider_code is not None:
            provider_id = PROVIDER_IDS[provider_code]
            await require_provider_access(
                session, user, provider_id=provider_id, outlet_id=outlet_id
            )
    response = await ledger_reader.balance_history(
        session, outlet_id, reserve_type, provider_code=provider_code, limit=limit
    )
    if reserve_type == ReserveType.SHARED_CASH or provider_code is not None:
        return response
    allowed = await authorized_provider_ids(session, user, outlet_id=outlet_id)
    if allowed is None:
        return response
    allowed_codes = {code.value for code, pid in PROVIDER_IDS.items() if pid in set(allowed)}
    filtered = [
        item
        for item in response.items
        if item.provider is None or item.provider.value in allowed_codes
    ]
    return response.model_copy(update={"items": filtered})


@router.get("/outlets/{outlet_id}/data-quality", response_model=DataQualityResponse)
async def current_data_quality(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    await require_outlet_access(session, user, outlet_id=outlet_id)
    response = await quality_foundation.get_current_data_quality(session, outlet_id)
    allowed = await authorized_provider_ids(session, user, outlet_id=outlet_id)
    if allowed is None:
        return response
    allowed_codes = {code.value for code, pid in PROVIDER_IDS.items() if pid in set(allowed)}
    filtered = [item for item in response.providers if item.provider.value in allowed_codes]
    return response.model_copy(update={"providers": filtered})


@router.get("/outlets/{outlet_id}/data-quality/history", response_model=DataQualityHistoryResponse)
async def data_quality_history(
    outlet_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    await require_outlet_access(session, user, outlet_id=outlet_id)
    response = await quality_foundation.get_data_quality_history(session, outlet_id)
    allowed = await authorized_provider_ids(session, user, outlet_id=outlet_id)
    if allowed is None:
        return response
    allowed_codes = {code.value for code, pid in PROVIDER_IDS.items() if pid in set(allowed)}
    filtered = [item for item in response.assessments if item.provider.value in allowed_codes]
    return response.model_copy(update={"assessments": filtered})
