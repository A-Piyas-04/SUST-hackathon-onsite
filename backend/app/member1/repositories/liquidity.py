from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories.db import fetch_all


async def list_latest_projections(
    session: AsyncSession, outlet_id: UUID, *, reserve_type: str, provider_id: UUID | None = None
) -> list[dict]:
    return await fetch_all(
        session,
        """
        SELECT liquidity_projection_id, analytics_run_id, outlet_id, reserve_type, outlet_provider_account_id,
               provider_id, as_of_at, current_balance, burn_rate_per_hour, projected_shortage_at,
               lower_bound_at, upper_bound_at, confidence_score, confidence_level, sample_count,
               is_actionable, non_actionable_reason
        FROM v_latest_liquidity_projections
        WHERE outlet_id = :outlet_id AND reserve_type = :reserve_type
          AND (CAST(:provider_id AS uuid) IS NULL OR provider_id = CAST(:provider_id AS uuid))
        ORDER BY as_of_at DESC
        """,
        {"outlet_id": str(outlet_id), "reserve_type": reserve_type, "provider_id": str(provider_id) if provider_id else None},
    )


async def list_projection_history(
    session: AsyncSession, outlet_id: UUID, *, reserve_type: str, provider_id: UUID | None = None, limit: int = 50
) -> list[dict]:
    return await fetch_all(
        session,
        """
        SELECT liquidity_projection_id, analytics_run_id, outlet_id, reserve_type, outlet_provider_account_id,
               provider_id, as_of_at, current_balance, burn_rate_per_hour, projected_shortage_at,
               lower_bound_at, upper_bound_at, confidence_score, confidence_level, sample_count,
               is_actionable, non_actionable_reason
        FROM liquidity_projections
        WHERE outlet_id = :outlet_id AND reserve_type = :reserve_type
          AND (CAST(:provider_id AS uuid) IS NULL OR provider_id = CAST(:provider_id AS uuid))
        ORDER BY as_of_at DESC
        LIMIT :limit
        """,
        {
            "outlet_id": str(outlet_id),
            "reserve_type": reserve_type,
            "provider_id": str(provider_id) if provider_id else None,
            "limit": limit,
        },
    )
