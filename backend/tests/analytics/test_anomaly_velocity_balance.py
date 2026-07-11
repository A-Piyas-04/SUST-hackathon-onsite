"""Unit tests for velocity spike and balance inconsistency detectors."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from app.contracts.v1.enums import AnomalyDisposition
from app.services.anomaly.engine import (
    BalanceAnomalyInput,
    BalanceRuleConfig,
    BalanceSnapshotRecord,
    TransactionRecord,
    VelocityAnomalyInput,
    VelocityRuleConfig,
    detect_balance_inconsistency,
    detect_velocity_spike,
)

_START = datetime(2026, 7, 11, 6, 0, tzinfo=timezone.utc)
_AS_OF = datetime(2026, 7, 11, 6, 30, tzinfo=timezone.utc)
_VRULE = VelocityRuleConfig(
    window_minutes=10,
    std_dev_threshold=2.0,
    minimum_baseline_windows=3,
    minimum_spike_count=8,
)
_BRULE = BalanceRuleConfig(
    min_discrepancy_amount=100.0,
    min_discrepancy_pct=0.5,
    staleness_soft_minutes=120,
)


def _velocity_baseline_txns():
    txns = []
    for end_min in (5, 15, 20):
        for i in range(3):
            txns.append(
                TransactionRecord(
                    transaction_id=uuid4(),
                    party_ref=f"BASE-{end_min}-{i}",
                    amount=Decimal("500.00"),
                    occurred_at=_START + timedelta(minutes=end_min - i),
                )
            )
    return txns


def _velocity_spike_txns(count: int = 10):
    return [
        TransactionRecord(
            transaction_id=uuid4(),
            party_ref=f"SPIKE-{i}",
            amount=Decimal("800.00"),
            occurred_at=_AS_OF - timedelta(minutes=i),
        )
        for i in range(count)
    ]


def test_velocity_positive_detection_requires_review():
    txns = _velocity_baseline_txns() + _velocity_spike_txns(10)
    result = detect_velocity_spike(
        VelocityAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=_AS_OF,
            rule_config=_VRULE,
        )
    )
    assert result.detected and result.persist
    assert result.disposition is AnomalyDisposition.REQUIRES_REVIEW
    assert result.reason_code == "velocity_spike"
    assert len(result.transaction_ids) >= 8
    assert result.plausible_benign_explanation
    assert "salary" in result.plausible_benign_explanation.lower() or "festival" in result.plausible_benign_explanation.lower()


def test_velocity_negative_normal_volume():
    txns = _velocity_baseline_txns()
    result = detect_velocity_spike(
        VelocityAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=_AS_OF,
            rule_config=_VRULE,
        )
    )
    assert not result.detected
    assert not result.persist
    assert result.disposition is AnomalyDisposition.INCONCLUSIVE


def test_velocity_suppressed_under_degraded_quality():
    txns = _velocity_baseline_txns() + _velocity_spike_txns(10)
    result = detect_velocity_spike(
        VelocityAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="conflicting",
            quality_modifier=Decimal("0.4"),
            as_of=_AS_OF,
            rule_config=_VRULE,
        )
    )
    assert result.detected and result.persist
    assert result.disposition is AnomalyDisposition.SUPPRESSED_DATA_QUALITY
    assert result.suppression_reason is not None
    assert result.confidence_score < Decimal("0.5")


def _balance_reconciliation_txns():
    return [
        TransactionRecord(
            transaction_id=uuid4(),
            party_ref=f"PARTY-{i}",
            amount=Decimal("1000.00"),
            occurred_at=_START + timedelta(minutes=10 + i),
            transaction_type="cash_out",
            status="completed",
        )
        for i in range(5)
    ]


def test_balance_positive_reconciliation_mismatch():
    trusted_at = _START
    reported_at = _START + timedelta(minutes=30)
    result = detect_balance_inconsistency(
        BalanceAnomalyInput(
            provider_code="bkash",
            transactions=_balance_reconciliation_txns(),
            observations=[
                BalanceSnapshotRecord(
                    observed_at=trusted_at,
                    balance=Decimal("10000.00"),
                ),
                BalanceSnapshotRecord(
                    observed_at=reported_at,
                    balance=Decimal("14000.00"),
                ),
            ],
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=reported_at,
            rule_config=_BRULE,
        )
    )
    assert result.detected and result.persist
    assert result.disposition is AnomalyDisposition.REQUIRES_REVIEW
    assert result.reason_code == "balance_reconciliation_mismatch"
    assert result.plausible_benign_explanation
    assert "data-quality" in result.plausible_benign_explanation.lower()
    assert "wallet integrity" not in result.evidence_summary.lower()


def test_balance_negative_consistent_feed():
    trusted_at = _START
    reported_at = _START + timedelta(minutes=30)
    result = detect_balance_inconsistency(
        BalanceAnomalyInput(
            provider_code="bkash",
            transactions=_balance_reconciliation_txns(),
            observations=[
                BalanceSnapshotRecord(
                    observed_at=trusted_at,
                    balance=Decimal("10000.00"),
                ),
                BalanceSnapshotRecord(
                    observed_at=reported_at,
                    balance=Decimal("15000.00"),
                ),
            ],
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=reported_at,
            rule_config=_BRULE,
        )
    )
    assert not result.detected
    assert not result.persist
    assert result.disposition is AnomalyDisposition.INCONCLUSIVE


def test_balance_positive_conflicting_snapshots():
    conflict_at = _START + timedelta(minutes=30)
    result = detect_balance_inconsistency(
        BalanceAnomalyInput(
            provider_code="bkash",
            transactions=[],
            observations=[
                BalanceSnapshotRecord(
                    observed_at=_START,
                    balance=Decimal("10000.00"),
                ),
                BalanceSnapshotRecord(
                    observed_at=conflict_at,
                    balance=Decimal("12000.00"),
                ),
                BalanceSnapshotRecord(
                    observed_at=conflict_at,
                    balance=Decimal("18000.00"),
                ),
            ],
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=conflict_at,
            rule_config=_BRULE,
        )
    )
    assert result.detected and result.persist
    assert result.disposition is AnomalyDisposition.REQUIRES_REVIEW
    assert result.reason_code == "conflicting_balance_snapshots"


def test_balance_suppressed_under_degraded_quality():
    conflict_at = _START + timedelta(minutes=30)
    result = detect_balance_inconsistency(
        BalanceAnomalyInput(
            provider_code="bkash",
            transactions=_balance_reconciliation_txns(),
            observations=[
                BalanceSnapshotRecord(
                    observed_at=_START,
                    balance=Decimal("10000.00"),
                ),
                BalanceSnapshotRecord(
                    observed_at=conflict_at,
                    balance=Decimal("14000.00"),
                ),
            ],
            quality_status="conflicting",
            quality_modifier=Decimal("0.4"),
            as_of=conflict_at,
            rule_config=_BRULE,
        )
    )
    assert result.detected and result.persist
    assert result.disposition is AnomalyDisposition.SUPPRESSED_DATA_QUALITY
    assert result.suppression_reason is not None
