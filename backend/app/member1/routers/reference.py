"""Reference and outlet reads (schema.md Section 16.2)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.member1.schemas.reference import AreaOut, OutletOut, ProviderOut
from app.member1.services import reference_service
from app.shared.deps import get_current_user_stub

router = APIRouter(prefix="/api/v1", tags=["reference"])


@router.get("/providers", response_model=list[ProviderOut])
async def list_providers(
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[ProviderOut]:
    return await reference_service.list_providers(session)


@router.get("/areas", response_model=list[AreaOut])
async def list_areas(
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[AreaOut]:
    return await reference_service.list_areas(session)


@router.get("/outlets", response_model=list[OutletOut])
async def list_outlets(
    area_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> list[OutletOut]:
    return await reference_service.list_outlets(session, area_id=area_id)


@router.get("/outlets/{outlet_id}", response_model=OutletOut)
async def get_outlet(
    outlet_id: UUID,
    session: AsyncSession = Depends(get_session),
    _user=Depends(get_current_user_stub),
) -> OutletOut:
    outlet = await reference_service.get_outlet(session, outlet_id)
    if outlet is None:
        # Same 404 shape for "does not exist" and "not authorized" (schema.md 16).
        raise HTTPException(status_code=404, detail={"code": "outlet_not_found", "message": "Outlet not found"})
    return outlet
