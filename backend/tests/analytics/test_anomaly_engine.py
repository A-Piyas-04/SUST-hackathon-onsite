"""Unit tests for the Anomaly Detection Engine (pure)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.contracts.v1.enums import AnomalyDisposition
from app.services.anomaly.engine import (
    AnomalyInput,
    AnomalyRuleConfig,
    TransactionRecord,
    detect_near_identical_amounts,
)

_START = datetime(2026, 7, 11, 6, 0, tzinfo=timezone.utc)
_RULE = AnomalyRuleConfig(
    window_minutes=15, amount_tolerance_pct=2.0, minimum_count=5, minimum_distinct_parties=1
)


def _cluster_txns(count: int, amount: str, *, step_min: int = 2, parties: int = 2):
    return [
        TransactionRecord(
            transaction_id=uuid4(),
            party_ref=f"PARTY-{i % parties}",
            amount=Decimal(amount),
            occurred_at=_START + timedelta(minutes=i * step_min),
        )
        for i in range(count)
    ]


def _varied_txns(count: int):
    return [
        TransactionRecord(
            transaction_id=uuid4(),
            party_ref=f"PARTY-{i}",
            amount=Decimal(str(500 + i * 137)),
            occurred_at=_START + timedelta(minutes=i * 2),
        )
        for i in range(count)
    ]


def test_positive_detection_requires_review():
    result = detect_near_identical_amounts(
        AnomalyInput(
            provider_code="bkash",
            transactions=_cluster_txns(6, "1000.00"),
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            rule_config=_RULE,
        )
    )
    assert result.detected and result.persist
    assert result.disposition is AnomalyDisposition.REQUIRES_REVIEW
    assert result.confidence_score >= Decimal("0.75")
    assert len(result.transaction_ids) == 6
    assert result.distinct_party_count == 2
    assert result.plausible_benign_explanation
    assert result.suppression_reason is None


def test_negative_normal_spike_no_high_confidence_flag():
    result = detect_near_identical_amounts(
        AnomalyInput(
            provider_code="bkash",
            transactions=_varied_txns(8),
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            rule_config=_RULE,
        )
    )
    assert not result.detected
    assert not result.persist
    assert result.disposition is AnomalyDisposition.INCONCLUSIVE


def test_below_minimum_count_not_flagged():
    result = detect_near_identical_amounts(
        AnomalyInput(
            provider_code="bkash",
            transactions=_cluster_txns(4, "1000.00"),
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            rule_config=_RULE,
        )
    )
    assert not result.persist
    assert result.disposition is AnomalyDisposition.INCONCLUSIVE


def test_exactly_minimum_count_flagged():
    result = detect_near_identical_amounts(
        AnomalyInput(
            provider_code="bkash",
            transactions=_cluster_txns(5, "1000.00"),
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            rule_config=_RULE,
        )
    )
    assert result.disposition is AnomalyDisposition.REQUIRES_REVIEW


def test_cluster_spanning_beyond_window_not_flagged():
    # 6 identical amounts but spaced 5 minutes apart => 25-minute span > 15 window.
    txns = _cluster_txns(6, "1000.00", step_min=5)
    result = detect_near_identical_amounts(
        AnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            rule_config=_RULE,
        )
    )
    # At most 4 fit in any 15-min window => below minimum_count.
    assert result.disposition is AnomalyDisposition.INCONCLUSIVE


def test_suppressed_under_degraded_quality():
    result = detect_near_identical_amounts(
        AnomalyInput(
            provider_code="bkash",
            transactions=_cluster_txns(6, "1000.00"),
            quality_status="conflicting",
            quality_modifier=Decimal("0.4"),
            rule_config=_RULE,
        )
    )
    assert result.detected and result.persist
    assert result.disposition is AnomalyDisposition.SUPPRESSED_DATA_QUALITY
    assert result.suppression_reason is not None
    # Suppressed evaluations are never presented with high confidence.
    assert result.confidence_score < Decimal("0.5")
