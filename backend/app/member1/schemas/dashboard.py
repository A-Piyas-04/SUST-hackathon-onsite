"""Response schemas for dashboard/ledger reads (schema.md Section 17
"Outlet dashboard response" canonical shape). Money fields are decimal
strings, never floats (schema.md Section 16)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.member1.schemas.common import ApiModel


class ProjectionOut(ApiModel):
    shortage_at: datetime | None = None
    confidence_score: str | None = None
    confidence_level: str | None = None


class FeedHealthOut(ApiModel):
    status: str
    confidence_modifier: str | None = None


class SharedCashOut(ApiModel):
    balance: str | None = None
    currency: str = "BDT"
    observed_at: datetime | None = None
    projection: ProjectionOut


class ProviderRefOut(ApiModel):
    code: str
    display_name: str


class ProviderBalanceEntryOut(ApiModel):
    provider: ProviderRefOut
    balance: str | None = None
    observed_at: datetime | None = None
    is_conflicted: bool = False
    feed_health: FeedHealthOut
    projection: ProjectionOut


class OutletRefOut(ApiModel):
    outlet_id: UUID
    synthetic_code: str
    area: str | None = None


class DashboardResponse(ApiModel):
    """Never includes a combined/total balance field — schema.md Section 17."""

    outlet: OutletRefOut
    shared_cash: SharedCashOut
    providers: list[ProviderBalanceEntryOut]
    alerts: list[dict] = []
    generated_at: datetime


class TransactionOut(ApiModel):
    transaction_id: UUID
    outlet_id: UUID
    provider_id: UUID
    synthetic_transaction_ref: str
    synthetic_party_ref: str
    transaction_type: str
    status: str
    amount: str
    currency_code: str
    occurred_at: datetime
    received_at: datetime


class BalanceHistoryEntryOut(ApiModel):
    balance: str
    currency_code: str
    observed_at: datetime
    received_at: datetime
    source_kind: str
