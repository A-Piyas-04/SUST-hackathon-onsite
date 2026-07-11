from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories import reference as reference_repo
from app.member1.schemas.reference import AreaOut, OutletOut, ProviderOut


async def list_providers(session: AsyncSession) -> list[ProviderOut]:
    rows = await reference_repo.list_providers(session)
    return [ProviderOut(**row) for row in rows]


async def list_areas(session: AsyncSession) -> list[AreaOut]:
    rows = await reference_repo.list_areas(session)
    return [AreaOut(**row) for row in rows]


async def list_outlets(session: AsyncSession, *, area_id: UUID | None = None) -> list[OutletOut]:
    rows = await reference_repo.list_outlets(session, area_id=area_id)
    return [OutletOut(**row) for row in rows]


async def get_outlet(session: AsyncSession, outlet_id: UUID) -> OutletOut | None:
    row = await reference_repo.get_outlet(session, outlet_id)
    return OutletOut(**row) if row else None
