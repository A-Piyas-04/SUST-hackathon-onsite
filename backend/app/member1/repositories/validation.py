from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories.db import fetch_all


async def list_validation_summary(session: AsyncSession, *, limit: int = 50) -> list[dict]:
    return await fetch_all(
        session,
        """
        SELECT metric_code, category, value, unit, sample_size, method, limitations, computed_at
        FROM v_validation_summary
        LIMIT :limit
        """,
        {"limit": limit},
    )
