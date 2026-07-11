"""STUB / PLACEHOLDER -- test-only fixture builders, not a scenario generator.

These are small deterministic factory helpers used by tests/analytics to
build Transaction / QualityAssessment objects without repeating boilerplate.
This is NOT the real deterministic synthetic transaction generator (a
separate, not-yet-built deliverable) -- it exists only to make the
Liquidity and Anomaly engines independently testable.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from backend.analytics.fixtures.stub_types import (
    TRANSACTION_STATUS_COMPLETED,
    TRANSACTION_TYPE_CASH_OUT,
    QualityAssessment,
    Transaction,
)

_counter = {"n": 0}


def _next_id(prefix: str) -> str:
    _counter["n"] += 1
    return f"{prefix}-{_counter['n']}"


def make_transaction(
    *,
    outlet_id: str = "outlet-1",
    provider_code: str | None = "bkash",
    synthetic_party_ref: str = "syn-party-1",
    transaction_type: str = TRANSACTION_TYPE_CASH_OUT,
    status: str = TRANSACTION_STATUS_COMPLETED,
    amount: float = 1000.0,
    occurred_at: datetime,
    transaction_id: str | None = None,
) -> Transaction:
    return Transaction(
        transaction_id=transaction_id or _next_id("txn"),
        outlet_id=outlet_id,
        provider_code=provider_code,
        outlet_provider_account_id=f"opa-{provider_code}" if provider_code else None,
        synthetic_party_ref=synthetic_party_ref,
        transaction_type=transaction_type,
        status=status,
        amount=amount,
        occurred_at=occurred_at,
        received_at=occurred_at,
    )


def make_burst(
    *,
    count: int,
    amount: float,
    start: datetime,
    spacing: timedelta,
    outlet_id: str = "outlet-1",
    provider_code: str | None = "bkash",
    transaction_type: str = TRANSACTION_TYPE_CASH_OUT,
    status: str = TRANSACTION_STATUS_COMPLETED,
    distinct_accounts: int | None = None,
    amount_jitter_pct: float = 0.0,
) -> list[Transaction]:
    """Build `count` transactions spaced `spacing` apart starting at `start`.

    If `distinct_accounts` is given, party refs cycle through that many
    distinct synthetic accounts. `amount_jitter_pct` alternates the amount
    by +/- that fraction so callers can build near-identical (not exactly
    identical) amount clusters.
    """
    txns = []
    for i in range(count):
        if distinct_accounts:
            party_ref = f"syn-party-{i % distinct_accounts}"
        else:
            party_ref = "syn-party-0"
        jitter = 1.0
        if amount_jitter_pct:
            jitter = 1.0 + (amount_jitter_pct if i % 2 == 0 else -amount_jitter_pct)
        txns.append(
            make_transaction(
                outlet_id=outlet_id,
                provider_code=provider_code,
                synthetic_party_ref=party_ref,
                transaction_type=transaction_type,
                status=status,
                amount=amount * jitter,
                occurred_at=start + spacing * i,
            )
        )
    return txns


def make_quality_assessment(
    *,
    outlet_id: str = "outlet-1",
    provider_code: str | None = "bkash",
    status: str = "fresh",
    confidence_modifier: float = 1.0,
    sample_count: int = 10,
    assessed_at: datetime,
    data_quality_assessment_id: str | None = None,
) -> QualityAssessment:
    return QualityAssessment(
        data_quality_assessment_id=data_quality_assessment_id or _next_id("qa"),
        outlet_id=outlet_id,
        provider_code=provider_code,
        status=status,
        confidence_modifier=confidence_modifier,
        sample_count=sample_count,
        assessed_at=assessed_at,
    )
