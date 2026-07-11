from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories import liquidity as liquidity_repo
from app.member1.schemas.common import decimal_to_str
from app.member1.schemas.liquidity import LiquidityProjectionOut


def _to_out(row: dict) -> LiquidityProjectionOut:
    return LiquidityProjectionOut(
        liquidity_projection_id=row["liquidity_projection_id"],
        analytics_run_id=row["analytics_run_id"],
        outlet_id=row["outlet_id"],
        reserve_type=row["reserve_type"],
        outlet_provider_account_id=row.get("outlet_provider_account_id"),
        provider_id=row.get("provider_id"),
        as_of_at=row["as_of_at"],
        current_balance=decimal_to_str(row["current_balance"]),
        burn_rate_per_hour=decimal_to_str(row["burn_rate_per_hour"]),
        projected_shortage_at=row.get("projected_shortage_at"),
        lower_bound_at=row.get("lower_bound_at"),
        upper_bound_at=row.get("upper_bound_at"),
        confidence_score=float(row["confidence_score"]),
        confidence_level=row["confidence_level"],
        sample_count=row["sample_count"],
        is_actionable=row["is_actionable"],
        non_actionable_reason=row.get("non_actionable_reason"),
    )


async def list_latest_projections(
    session: AsyncSession, outlet_id: UUID, *, reserve_type: str, provider_id: UUID | None = None
) -> list[LiquidityProjectionOut]:
    rows = await liquidity_repo.list_latest_projections(session, outlet_id, reserve_type=reserve_type, provider_id=provider_id)
    return [_to_out(r) for r in rows]


async def list_projection_history(
    session: AsyncSession, outlet_id: UUID, *, reserve_type: str, provider_id: UUID | None = None, limit: int = 50
) -> list[LiquidityProjectionOut]:
    rows = await liquidity_repo.list_projection_history(session, outlet_id, reserve_type=reserve_type, provider_id=provider_id, limit=limit)
    return [_to_out(r) for r in rows]
