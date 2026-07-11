from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories.db import fetch_all, fetch_one


async def get_outlet_dashboard_row(session: AsyncSession, outlet_id: UUID) -> dict | None:
    return await fetch_one(
        session,
        """
        SELECT d.*, a.name AS area_name
        FROM v_outlet_dashboard d
        LEFT JOIN areas a ON a.area_id = d.area_id
        WHERE d.outlet_id = :outlet_id
        """,
        {"outlet_id": str(outlet_id)},
    )


async def list_transactions(
    session: AsyncSession,
    outlet_id: UUID,
    *,
    provider_id: UUID | None = None,
    from_: datetime | None = None,
    to: datetime | None = None,
    limit: int = 50,
) -> list[dict]:
    return await fetch_all(
        session,
        """
        SELECT transaction_id, outlet_id, provider_id, synthetic_transaction_ref, synthetic_party_ref,
               transaction_type, status, amount, currency_code, occurred_at, received_at
        FROM transactions
        WHERE outlet_id = :outlet_id
          AND (CAST(:provider_id AS uuid) IS NULL OR provider_id = CAST(:provider_id AS uuid))
          AND (CAST(:from_ts AS timestamptz) IS NULL OR occurred_at >= CAST(:from_ts AS timestamptz))
          AND (CAST(:to_ts AS timestamptz) IS NULL OR occurred_at <= CAST(:to_ts AS timestamptz))
        ORDER BY occurred_at DESC
        LIMIT :limit
        """,
        {
            "outlet_id": str(outlet_id),
            "provider_id": str(provider_id) if provider_id else None,
            "from_ts": from_,
            "to_ts": to,
            "limit": limit,
        },
    )


async def list_cash_balance_history(
    session: AsyncSession, outlet_id: UUID, *, from_: datetime | None = None, to: datetime | None = None, limit: int = 50
) -> list[dict]:
    return await fetch_all(
        session,
        """
        SELECT balance, currency_code, observed_at, received_at, source_kind
        FROM cash_balance_snapshots
        WHERE outlet_id = :outlet_id
          AND (CAST(:from_ts AS timestamptz) IS NULL OR observed_at >= CAST(:from_ts AS timestamptz))
          AND (CAST(:to_ts AS timestamptz) IS NULL OR observed_at <= CAST(:to_ts AS timestamptz))
        ORDER BY observed_at DESC
        LIMIT :limit
        """,
        {"outlet_id": str(outlet_id), "from_ts": from_, "to_ts": to, "limit": limit},
    )


async def list_provider_balance_history(
    session: AsyncSession,
    outlet_id: UUID,
    provider_id: UUID,
    *,
    from_: datetime | None = None,
    to: datetime | None = None,
    limit: int = 50,
) -> list[dict]:
    return await fetch_all(
        session,
        """
        SELECT balance, currency_code, observed_at, received_at, source_kind
        FROM provider_balance_snapshots
        WHERE outlet_id = :outlet_id AND provider_id = :provider_id
          AND (CAST(:from_ts AS timestamptz) IS NULL OR observed_at >= CAST(:from_ts AS timestamptz))
          AND (CAST(:to_ts AS timestamptz) IS NULL OR observed_at <= CAST(:to_ts AS timestamptz))
        ORDER BY observed_at DESC, received_at DESC
        LIMIT :limit
        """,
        {"outlet_id": str(outlet_id), "provider_id": str(provider_id), "from_ts": from_, "to_ts": to, "limit": limit},
    )
