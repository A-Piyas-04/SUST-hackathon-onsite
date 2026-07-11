"""Unit tests for the Data Quality & Confidence Engine (pure)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.contracts.v1.enums import FeedHealthStatus, QualityIssueType
from app.services.quality.engine import (
    BalanceObservation,
    ProviderQualityInput,
    assess_provider_quality,
)

_AS_OF = datetime(2026, 7, 11, 8, 0, tzinfo=timezone.utc)


def _obs(minute: int, balance: str) -> BalanceObservation:
    ts = _AS_OF - timedelta(minutes=minute)
    return BalanceObservation(observed_at=ts, balance=Decimal(balance), received_at=ts)


def test_missing_when_no_samples():
    result = assess_provider_quality(
        ProviderQualityInput(
            provider_code="bkash",
            observations=[],
            transaction_count=0,
            rejected_event_count=0,
            as_of=_AS_OF,
        )
    )
    assert result.status is FeedHealthStatus.MISSING
    assert result.confidence_modifier == Decimal("0.0000")
    assert any(i.issue_type is QualityIssueType.MISSING_FEED for i in result.issues)


def test_conflicting_takes_precedence_over_stale():
    # Two different balances at the same (old) observed time => conflicting, and
    # the observation is also old enough to be stale. Conflicting must win.
    ts = _AS_OF - timedelta(minutes=90)
    observations = [
        BalanceObservation(observed_at=ts, balance=Decimal("100.00"), received_at=ts),
        BalanceObservation(observed_at=ts, balance=Decimal("200.00"), received_at=ts),
    ]
    result = assess_provider_quality(
        ProviderQualityInput(
            provider_code="bkash",
            observations=observations,
            transaction_count=0,
            rejected_event_count=0,
            as_of=_AS_OF,
            stale_after_minutes=30,
        )
    )
    assert result.status is FeedHealthStatus.CONFLICTING
    types = {i.issue_type for i in result.issues}
    assert QualityIssueType.CONFLICTING_SNAPSHOT in types
    assert QualityIssueType.LATE_ARRIVAL in types  # stale still recorded as evidence


def test_stale_when_latest_beyond_window():
    result = assess_provider_quality(
        ProviderQualityInput(
            provider_code="nagad",
            observations=[_obs(120, "500.00"), _obs(100, "400.00")],
            transaction_count=0,
            rejected_event_count=0,
            as_of=_AS_OF,
            stale_after_minutes=30,
        )
    )
    assert result.status is FeedHealthStatus.STALE


def test_fresh_high_modifier():
    result = assess_provider_quality(
        ProviderQualityInput(
            provider_code="rocket",
            observations=[_obs(10, "500.00"), _obs(5, "480.00")],
            transaction_count=4,
            rejected_event_count=0,
            as_of=_AS_OF,
        )
    )
    assert result.status is FeedHealthStatus.FRESH
    assert result.confidence_modifier == Decimal("1.0000")


def test_conflicting_reduces_confidence_below_fresh():
    fresh = assess_provider_quality(
        ProviderQualityInput(
            provider_code="bkash",
            observations=[_obs(10, "500.00"), _obs(5, "480.00")],
            transaction_count=4,
            rejected_event_count=0,
            as_of=_AS_OF,
        )
    )
    ts = _AS_OF - timedelta(minutes=5)
    conflicting = assess_provider_quality(
        ProviderQualityInput(
            provider_code="bkash",
            observations=[
                BalanceObservation(observed_at=ts, balance=Decimal("500.00"), received_at=ts),
                BalanceObservation(observed_at=ts, balance=Decimal("999.00"), received_at=ts),
            ],
            transaction_count=4,
            rejected_event_count=0,
            as_of=_AS_OF,
        )
    )
    assert conflicting.confidence_modifier < fresh.confidence_modifier


def test_malformed_payload_records_issue_and_penalizes():
    result = assess_provider_quality(
        ProviderQualityInput(
            provider_code="bkash",
            observations=[_obs(10, "500.00"), _obs(5, "480.00")],
            transaction_count=4,
            rejected_event_count=3,
            as_of=_AS_OF,
        )
    )
    assert any(i.issue_type is QualityIssueType.MALFORMED_PAYLOAD for i in result.issues)
    assert result.confidence_modifier < Decimal("1.0000")


def test_insufficient_samples_flagged_safely():
    result = assess_provider_quality(
        ProviderQualityInput(
            provider_code="bkash",
            observations=[_obs(5, "500.00")],
            transaction_count=0,
            rejected_event_count=0,
            as_of=_AS_OF,
            min_samples=3,
        )
    )
    assert any(i.issue_type is QualityIssueType.INSUFFICIENT_SAMPLES for i in result.issues)
    assert Decimal("0") <= result.confidence_modifier <= Decimal("1")


def test_last_trusted_value_preserved_under_conflict():
    trusted_ts = _AS_OF - timedelta(minutes=20)
    conflict_ts = _AS_OF - timedelta(minutes=5)
    observations = [
        BalanceObservation(observed_at=trusted_ts, balance=Decimal("700.00"), received_at=trusted_ts),
        BalanceObservation(observed_at=conflict_ts, balance=Decimal("500.00"), received_at=conflict_ts),
        BalanceObservation(observed_at=conflict_ts, balance=Decimal("900.00"), received_at=conflict_ts),
    ]
    result = assess_provider_quality(
        ProviderQualityInput(
            provider_code="bkash",
            observations=observations,
            transaction_count=0,
            rejected_event_count=0,
            as_of=_AS_OF,
        )
    )
    assert result.status is FeedHealthStatus.CONFLICTING
    assert result.trusted_balance == Decimal("700.00")
    assert result.trusted_observed_at == trusted_ts
