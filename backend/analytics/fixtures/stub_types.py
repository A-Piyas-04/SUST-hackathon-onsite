"""STUB / PLACEHOLDER -- Phase 3 scope only.

These dataclasses mirror the relevant subset of the `transactions` and
`data_quality_assessments` tables from docs/schema.md so the Liquidity
Forecasting Engine and Anomaly Detection Engine have a concrete,
testable input shape.

They are NOT the real synthetic transaction generator or the real Data
Quality & Confidence Engine -- those are separate deliverables that are
not yet present in this repository. Once they land, engine code in
analytics/liquidity_forecast.py and analytics/anomaly_rules.py should
keep working unchanged (it only relies on duck-typed attribute access
matching these field names); only this stub module and callers building
these objects directly should need to be retired.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# transaction_type (docs/schema.md §4)
TRANSACTION_TYPE_CASH_IN = "cash_in"
TRANSACTION_TYPE_CASH_OUT = "cash_out"
TRANSACTION_TYPE_PAYMENT = "payment"
TRANSACTION_TYPE_REFUND = "refund"
TRANSACTION_TYPE_ADJUSTMENT = "adjustment"

# transaction_status (docs/schema.md §4)
TRANSACTION_STATUS_PENDING = "pending"
TRANSACTION_STATUS_COMPLETED = "completed"
TRANSACTION_STATUS_FAILED = "failed"
TRANSACTION_STATUS_REVERSED = "reversed"

# feed_health_status (docs/schema.md §4)
FEED_HEALTH_FRESH = "fresh"
FEED_HEALTH_STALE = "stale"
FEED_HEALTH_MISSING = "missing"
FEED_HEALTH_CONFLICTING = "conflicting"


@dataclass(frozen=True)
class Transaction:
    """Mirrors the relevant subset of docs/schema.md §8.1 `transactions`."""

    transaction_id: str
    outlet_id: str
    provider_code: str | None  # "bkash" | "nagad" | "rocket"; None only for a shared-cash-scoped pseudo entry
    outlet_provider_account_id: str | None
    synthetic_party_ref: str  # opaque; never a phone number
    transaction_type: str
    status: str
    amount: float  # > 0
    occurred_at: datetime
    received_at: datetime


@dataclass(frozen=True)
class QualityAssessment:
    """Mirrors the relevant subset of docs/schema.md §9.1 `data_quality_assessments`."""

    data_quality_assessment_id: str
    outlet_id: str
    provider_code: str | None  # None permitted for a shared-cash-scoped assessment
    status: str  # fresh | stale | missing | conflicting
    confidence_modifier: float  # 0..1
    sample_count: int
    assessed_at: datetime
