"""Ledger read repositories."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import ProviderCode, ReserveType, TransactionStatus, TransactionType
from app.contracts.v1.ledger import (
    AreaRef,
    BalanceHistoryItem,
    BalanceHistoryResponse,
    OutletDetailResponse,
    OutletListItem,
    ProviderRef,
    TransactionListResponse,
    TransactionResponse,
)
from app.contracts.v1.responses import (
    DashboardResponse,
    FeedHealthSummary,
    OutletSummary,
    ProjectionSummary,
    ProviderDashboardItem,
    ProviderSummary,
    SharedCashDashboard,
)
from app.core.errors import AppError
from app.services.constants import INTERIM_PROJECTION, PROVIDER_IDS


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _interim_projection() -> ProjectionSummary:
    return ProjectionSummary(
        shortage_at=None,
        confidence_score=Decimal("0"),
        confidence_level="unavailable",
    )


async def get_dashboard(session: AsyncSession, outlet_id: UUID) -> DashboardResponse:
    result = await session.execute(
        text("SELECT * FROM v_outlet_dashboard WHERE outlet_id = :outlet_id"),
        {"outlet_id": outlet_id},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError("not_found", f"Outlet {outlet_id} not found.", status_code=404)

    area = await session.execute(
        text("SELECT area_id, code, name FROM areas WHERE area_id = :id"),
        {"id": row["area_id"]},
    )
    area_row = area.mappings().one()

    shared_raw = row["shared_cash"] or {}
    shared_cash = SharedCashDashboard(
        balance=_to_decimal(shared_raw.get("balance")),
        currency=str(shared_raw.get("currency") or "BDT"),
        observed_at=shared_raw.get("observed_at") or datetime.now(timezone.utc),
        projection=_projection_from_json(shared_raw.get("projection")) or _interim_projection(),
    )

    providers: list[ProviderDashboardItem] = []
    for p in row["providers"] or []:
        prov_obj = p.get("provider") or {}
        feed = p.get("feed_health") or {"status": "fresh", "confidence_modifier": 1.0}
        providers.append(
            ProviderDashboardItem(
                provider=ProviderSummary(
                    code=ProviderCode(prov_obj.get("code", "bkash")),
                    display_name=prov_obj.get("display_name", ""),
                ),
                balance=_to_decimal(p.get("balance")),
                observed_at=p.get("observed_at") or datetime.now(timezone.utc),
                feed_health=FeedHealthSummary(
                    status=str(feed.get("status", "fresh")),
                    confidence_modifier=float(feed.get("confidence_modifier", 1.0)),
                ),
                projection=_projection_from_json(p.get("projection")) or _interim_projection(),
            )
        )

    return DashboardResponse(
        outlet=OutletSummary(
            outlet_id=outlet_id,
            synthetic_code=row["synthetic_code"],
            area=area_row["name"],
        ),
        shared_cash=shared_cash,
        providers=providers,
        alerts=row["alerts"] or [],
        generated_at=row["generated_at"],
    )


def _projection_from_json(data: Any) -> ProjectionSummary | None:
    if not data or not isinstance(data, dict):
        return None
    shortage = data.get("shortage_at")
    score = data.get("confidence_score")
    if score is None:
        return None
    return ProjectionSummary(
        shortage_at=shortage,
        confidence_score=Decimal(str(score)),
        confidence_level=str(data.get("confidence_level", "unavailable")),
    )


async def list_transactions(
    session: AsyncSession,
    outlet_id: UUID,
    *,
    provider_code: ProviderCode | None = None,
    limit: int = 100,
) -> TransactionListResponse:
    query = """
        SELECT t.*, p.code AS provider_code
        FROM transactions t
        JOIN providers p ON p.provider_id = t.provider_id
        WHERE t.outlet_id = :outlet_id
    """
    params: dict[str, Any] = {"outlet_id": outlet_id, "limit": limit}
    if provider_code:
        query += " AND p.code = :provider_code"
        params["provider_code"] = provider_code.value
    query += " ORDER BY t.occurred_at DESC LIMIT :limit"

    result = await session.execute(text(query), params)
    txns = [
        TransactionResponse(
            transaction_id=r["transaction_id"],
            synthetic_transaction_ref=r["synthetic_transaction_ref"],
            synthetic_party_ref=r["synthetic_party_ref"],
            provider=ProviderCode(r["provider_code"]),
            transaction_type=TransactionType(r["transaction_type"]),
            status=TransactionStatus(r["status"]),
            amount=r["amount"],
            currency_code=r["currency_code"],
            occurred_at=r["occurred_at"],
            received_at=r["received_at"],
        )
        for r in result.mappings().all()
    ]
    return TransactionListResponse(outlet_id=outlet_id, transactions=txns, total=len(txns))


async def balance_history(
    session: AsyncSession,
    outlet_id: UUID,
    reserve_type: ReserveType,
    *,
    provider_code: ProviderCode | None = None,
    limit: int = 100,
) -> BalanceHistoryResponse:
    items: list[BalanceHistoryItem] = []

    if reserve_type == ReserveType.SHARED_CASH:
        result = await session.execute(
            text(
                """
                SELECT cash_balance_snapshot_id AS snapshot_id, outlet_id, balance,
                       currency_code, observed_at, received_at, source_kind
                FROM cash_balance_snapshots
                WHERE outlet_id = :outlet_id
                ORDER BY observed_at DESC, received_at DESC
                LIMIT :limit
                """
            ),
            {"outlet_id": outlet_id, "limit": limit},
        )
        for r in result.mappings().all():
            items.append(
                BalanceHistoryItem(
                    snapshot_id=r["snapshot_id"],
                    reserve_type=ReserveType.SHARED_CASH,
                    outlet_id=r["outlet_id"],
                    balance=r["balance"],
                    currency_code=r["currency_code"],
                    observed_at=r["observed_at"],
                    received_at=r["received_at"],
                    source_kind=r["source_kind"],
                )
            )
    else:
        if provider_code is None:
            raise AppError(
                "validation_error",
                "provider_code is required when reserve_type is provider_e_money.",
                status_code=422,
            )
        result = await session.execute(
            text(
                """
                SELECT pbs.provider_balance_snapshot_id AS snapshot_id, pbs.outlet_id,
                       pbs.balance, pbs.currency_code, pbs.observed_at, pbs.received_at,
                       pbs.source_kind, p.code AS provider_code
                FROM provider_balance_snapshots pbs
                JOIN providers p ON p.provider_id = pbs.provider_id
                WHERE pbs.outlet_id = :outlet_id AND p.code = :provider_code
                ORDER BY pbs.observed_at DESC, pbs.received_at DESC
                LIMIT :limit
                """
            ),
            {"outlet_id": outlet_id, "provider_code": provider_code.value, "limit": limit},
        )
        rows = result.mappings().all()
        # Detect conflicts: same observed_at, different balance
        conflict_times: set[datetime] = set()
        by_time: dict[datetime, set[str]] = {}
        for r in rows:
            by_time.setdefault(r["observed_at"], set()).add(str(r["balance"]))
        for t, balances in by_time.items():
            if len(balances) > 1:
                conflict_times.add(t)

        for r in rows:
            items.append(
                BalanceHistoryItem(
                    snapshot_id=r["snapshot_id"],
                    reserve_type=ReserveType.PROVIDER_E_MONEY,
                    outlet_id=r["outlet_id"],
                    provider=ProviderCode(r["provider_code"]),
                    balance=r["balance"],
                    currency_code=r["currency_code"],
                    observed_at=r["observed_at"],
                    received_at=r["received_at"],
                    source_kind=r["source_kind"],
                    is_conflicted=r["observed_at"] in conflict_times,
                )
            )

    return BalanceHistoryResponse(
        outlet_id=outlet_id,
        reserve_type=reserve_type,
        provider=provider_code,
        items=items,
    )


async def list_providers(session: AsyncSession) -> list[ProviderRef]:
    result = await session.execute(
        text("SELECT provider_id, code, display_name FROM providers ORDER BY code")
    )
    return [
        ProviderRef(
            provider_id=r["provider_id"],
            code=ProviderCode(r["code"]),
            display_name=r["display_name"],
        )
        for r in result.mappings().all()
    ]


async def list_areas(session: AsyncSession) -> list[AreaRef]:
    result = await session.execute(
        text("SELECT area_id, code, name FROM areas ORDER BY level, code")
    )
    return [AreaRef(area_id=r["area_id"], code=r["code"], name=r["name"]) for r in result.mappings().all()]


async def list_outlets(session: AsyncSession) -> list[OutletListItem]:
    result = await session.execute(
        text(
            """
            SELECT o.outlet_id, o.synthetic_code, o.display_name, a.name AS area_name
            FROM outlets o JOIN areas a ON a.area_id = o.area_id
            ORDER BY o.synthetic_code
            """
        )
    )
    return [
        OutletListItem(
            outlet_id=r["outlet_id"],
            synthetic_code=r["synthetic_code"],
            display_name=r["display_name"],
            area_name=r["area_name"],
        )
        for r in result.mappings().all()
    ]


async def get_outlet_detail(session: AsyncSession, outlet_id: UUID) -> OutletDetailResponse:
    result = await session.execute(
        text(
            """
            SELECT o.outlet_id, o.synthetic_code, o.display_name,
                   a.area_id, a.code AS area_code, a.name AS area_name
            FROM outlets o JOIN areas a ON a.area_id = o.area_id
            WHERE o.outlet_id = :outlet_id
            """
        ),
        {"outlet_id": outlet_id},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError("not_found", f"Outlet {outlet_id} not found.", status_code=404)

    prov_result = await session.execute(
        text(
            """
            SELECT p.provider_id, p.code, p.display_name
            FROM outlet_provider_accounts opa
            JOIN providers p ON p.provider_id = opa.provider_id
            WHERE opa.outlet_id = :outlet_id AND opa.is_active
            ORDER BY p.code
            """
        ),
        {"outlet_id": outlet_id},
    )
    providers = [
        ProviderRef(
            provider_id=r["provider_id"],
            code=ProviderCode(r["code"]),
            display_name=r["display_name"],
        )
        for r in prov_result.mappings().all()
    ]
    return OutletDetailResponse(
        outlet_id=row["outlet_id"],
        synthetic_code=row["synthetic_code"],
        display_name=row["display_name"],
        area=AreaRef(area_id=row["area_id"], code=row["area_code"], name=row["area_name"]),
        providers=providers,
    )
