from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories.db import fetch_all, fetch_one


async def list_providers(session: AsyncSession) -> list[dict]:
    return await fetch_all(session, "SELECT provider_id, code, display_name, display_color, is_active FROM providers ORDER BY code")


async def list_areas(session: AsyncSession) -> list[dict]:
    return await fetch_all(session, "SELECT area_id, parent_area_id, code, name, level, is_active FROM areas ORDER BY name")


async def list_outlets(session: AsyncSession, *, area_id: UUID | None = None, limit: int = 50) -> list[dict]:
    rows = await fetch_all(
        session,
        """
        SELECT o.outlet_id, o.synthetic_code, o.display_name, o.area_id, o.currency_code, o.is_active,
               COALESCE(array_agg(p.code ORDER BY p.code) FILTER (WHERE p.code IS NOT NULL), ARRAY[]::text[]) AS active_provider_codes
        FROM outlets o
        LEFT JOIN outlet_provider_accounts opa ON opa.outlet_id = o.outlet_id AND opa.is_active
        LEFT JOIN providers p ON p.provider_id = opa.provider_id
        WHERE (:area_id IS NULL OR o.area_id = :area_id)
        GROUP BY o.outlet_id
        ORDER BY o.synthetic_code
        LIMIT :limit
        """,
        {"area_id": str(area_id) if area_id else None, "limit": limit},
    )
    return rows


async def get_outlet(session: AsyncSession, outlet_id: UUID) -> dict | None:
    return await fetch_one(
        session,
        """
        SELECT o.outlet_id, o.synthetic_code, o.display_name, o.area_id, o.currency_code, o.is_active,
               COALESCE(array_agg(p.code ORDER BY p.code) FILTER (WHERE p.code IS NOT NULL), ARRAY[]::text[]) AS active_provider_codes
        FROM outlets o
        LEFT JOIN outlet_provider_accounts opa ON opa.outlet_id = o.outlet_id AND opa.is_active
        LEFT JOIN providers p ON p.provider_id = opa.provider_id
        WHERE o.outlet_id = :outlet_id
        GROUP BY o.outlet_id
        """,
        {"outlet_id": str(outlet_id)},
    )
