from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories import dashboard as dashboard_repo
from app.member1.schemas.common import decimal_to_str, money_to_str
from app.member1.schemas.dashboard import (
    BalanceHistoryEntryOut,
    DashboardResponse,
    FeedHealthOut,
    OutletRefOut,
    ProjectionOut,
    ProviderBalanceEntryOut,
    ProviderRefOut,
    SharedCashOut,
    TransactionOut,
)


async def get_dashboard(session: AsyncSession, outlet_id: UUID) -> DashboardResponse | None:
    row = await dashboard_repo.get_outlet_dashboard_row(session, outlet_id)
    if row is None:
        return None

    providers_out = [
        ProviderBalanceEntryOut(
            provider=ProviderRefOut(code=p["provider_code"], display_name=p["provider_display_name"]),
            balance=money_to_str(p.get("balance")),
            observed_at=p.get("observed_at"),
            is_conflicted=bool(p.get("is_conflicted") or False),
            feed_health=FeedHealthOut(
                status=p.get("feed_status") or "missing",
                confidence_modifier=float(p["confidence_modifier"]) if p.get("confidence_modifier") is not None else None,
            ),
            projection=ProjectionOut(
                shortage_at=p.get("projected_shortage_at"),
                confidence_score=float(p["confidence_score"]) if p.get("confidence_score") is not None else None,
                confidence_level=p.get("confidence_level"),
            ),
        )
        for p in (row.get("providers") or [])
    ]

    return DashboardResponse(
        outlet=OutletRefOut(outlet_id=row["outlet_id"], synthetic_code=row["synthetic_code"], area=row.get("area_name")),
        shared_cash=SharedCashOut(
            balance=money_to_str(row.get("shared_cash_balance")),
            currency=row.get("shared_cash_currency_code") or "BDT",
            observed_at=row.get("shared_cash_observed_at"),
            projection=ProjectionOut(
                shortage_at=row.get("shared_cash_projected_shortage_at"),
                confidence_score=float(row["shared_cash_confidence_score"]) if row.get("shared_cash_confidence_score") is not None else None,
                confidence_level=row.get("shared_cash_confidence_level"),
            ),
        ),
        providers=providers_out,
        # TODO(owner=Member2): join real active alerts once the alerts table
        # exists (migration 004). Empty array is schema-valid for Phase 1.
        alerts=[],
        generated_at=row.get("generated_at") or datetime.now(timezone.utc),
    )


async def list_transactions(session: AsyncSession, outlet_id: UUID, **filters) -> list[TransactionOut]:
    rows = await dashboard_repo.list_transactions(session, outlet_id, **filters)
    return [
        TransactionOut(
            transaction_id=r["transaction_id"],
            outlet_id=r["outlet_id"],
            provider_id=r["provider_id"],
            synthetic_transaction_ref=r["synthetic_transaction_ref"],
            synthetic_party_ref=r["synthetic_party_ref"],
            transaction_type=r["transaction_type"],
            status=r["status"],
            amount=decimal_to_str(r["amount"]),
            currency_code=r["currency_code"],
            occurred_at=r["occurred_at"],
            received_at=r["received_at"],
        )
        for r in rows
    ]


async def list_cash_balance_history(session: AsyncSession, outlet_id: UUID, **filters) -> list[BalanceHistoryEntryOut]:
    rows = await dashboard_repo.list_cash_balance_history(session, outlet_id, **filters)
    return [
        BalanceHistoryEntryOut(
            balance=decimal_to_str(r["balance"]),
            currency_code=r["currency_code"],
            observed_at=r["observed_at"],
            received_at=r["received_at"],
            source_kind=r["source_kind"],
        )
        for r in rows
    ]


async def list_provider_balance_history(
    session: AsyncSession, outlet_id: UUID, provider_id: UUID, **filters
) -> list[BalanceHistoryEntryOut]:
    rows = await dashboard_repo.list_provider_balance_history(session, outlet_id, provider_id, **filters)
    return [
        BalanceHistoryEntryOut(
            balance=decimal_to_str(r["balance"]),
            currency_code=r["currency_code"],
            observed_at=r["observed_at"],
            received_at=r["received_at"],
            source_kind=r["source_kind"],
        )
        for r in rows
    ]
