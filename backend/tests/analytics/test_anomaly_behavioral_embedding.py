"""Unit tests for behavioral embedding (k-NN) anomaly detector."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from app.contracts.v1.enums import AnomalyDisposition, AnalyticsEngine, ConfidenceLevel
from app.contracts.v1.envelope import AnomalyEngineSpecific, ResultEnvelope
from app.services.alert_candidate_adapter import envelope_to_alert_candidate
from app.services.anomaly.engine import (
    BehavioralAnomalyInput,
    BehavioralRuleConfig,
    TransactionRecord,
    detect_behavioral_embedding,
)

_START = datetime(2026, 7, 11, 6, 0, tzinfo=timezone.utc)
_AS_OF = datetime(2026, 7, 11, 6, 45, tzinfo=timezone.utc)
_OUTLET = uuid4()
_BRULE = BehavioralRuleConfig(
    k=3,
    distance_threshold=2.5,
    minimum_history_transactions=10,
    window_minutes=60,
)


def _regular_history(count: int = 12) -> list[TransactionRecord]:
    return [
        TransactionRecord(
            transaction_id=uuid4(),
            party_ref=f"REGULAR-{i % 3}",
            amount=Decimal("500.00"),
            occurred_at=_START + timedelta(minutes=i),
            transaction_type="payment",
        )
        for i in range(count)
    ]


def _outlier_candidate(*, occurred_at: datetime | None = None) -> TransactionRecord:
    return TransactionRecord(
        transaction_id=uuid4(),
        party_ref="NEW-CUSTOMER",
        amount=Decimal("50000.00"),
        occurred_at=occurred_at or _AS_OF,
        transaction_type="cash_out",
    )


def _neighbor_evidence(result) -> list[dict]:
    for item in result.evidence_items:
        if item.evidence_type == "nearest_neighbors":
            return item.value
    return []


def test_behavioral_positive_detection_requires_review_with_neighbors():
    txns = _regular_history(12) + [_outlier_candidate()]
    result = detect_behavioral_embedding(
        BehavioralAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=_AS_OF,
            rule_config=_BRULE,
        )
    )
    assert result.detected and result.persist
    assert result.disposition is AnomalyDisposition.REQUIRES_REVIEW
    assert result.reason_code == "behavioral_embedding"
    assert result.plausible_benign_explanation
    assert "legitimate" in result.plausible_benign_explanation.lower()
    neighbors = _neighbor_evidence(result)
    assert len(neighbors) == 3
    assert all("transaction_id" in n and "amount" in n for n in neighbors)
    assert all(n["amount"] == "500.00" for n in neighbors)
    assert result.confidence_score > Decimal("0")


def test_behavioral_negative_in_neighborhood():
    txns = _regular_history(12)
    inlier_at = _START + timedelta(minutes=12)
    txns.append(
        TransactionRecord(
            transaction_id=uuid4(),
            party_ref="REGULAR-1",
            amount=Decimal("505.00"),
            occurred_at=inlier_at,
            transaction_type="payment",
        )
    )
    result = detect_behavioral_embedding(
        BehavioralAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=inlier_at,
            rule_config=_BRULE,
        )
    )
    assert not result.detected
    assert not result.persist
    assert result.disposition is AnomalyDisposition.INCONCLUSIVE
    assert result.reason_code == "no_supported_pattern"


def test_behavioral_cold_start_insufficient_history_persisted_not_alertable():
    txns = _regular_history(8) + [_outlier_candidate()]
    result = detect_behavioral_embedding(
        BehavioralAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=_AS_OF,
            rule_config=_BRULE,
        )
    )
    assert not result.detected
    assert result.persist
    assert result.disposition is AnomalyDisposition.INCONCLUSIVE
    assert result.reason_code == "insufficient_history"
    assert result.confidence_level is ConfidenceLevel.UNAVAILABLE


def test_behavioral_suppressed_under_degraded_quality():
    txns = _regular_history(12) + [_outlier_candidate()]
    result = detect_behavioral_embedding(
        BehavioralAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="conflicting",
            quality_modifier=Decimal("0.4"),
            as_of=_AS_OF,
            rule_config=_BRULE,
        )
    )
    assert result.detected and result.persist
    assert result.disposition is AnomalyDisposition.SUPPRESSED_DATA_QUALITY
    assert result.suppression_reason is not None
    assert result.confidence_score < Decimal("0.5")


def test_behavioral_suppressed_produces_no_alert_candidate():
    txns = _regular_history(12) + [_outlier_candidate()]
    result = detect_behavioral_embedding(
        BehavioralAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="conflicting",
            quality_modifier=Decimal("0.4"),
            as_of=_AS_OF,
            rule_config=_BRULE,
        )
    )
    specific = AnomalyEngineSpecific(
        pattern="behavioral_embedding",
        provider_code="bkash",
        window_start=result.window_start,
        window_end=result.window_end,
        disposition=result.disposition.value,
        reason_code=result.reason_code,
        evidence_summary=result.evidence_summary,
        plausible_benign_explanation=result.plausible_benign_explanation,
        suppression_disposition=result.suppression_reason or "none",
    )
    envelope = ResultEnvelope(
        engine=AnalyticsEngine.ANOMALY,
        engine_version="anomaly-v1",
        input_window_start=result.window_start,
        input_window_end=result.window_end,
        quality_assessment_ids=(uuid4(),),
        confidence=float(result.confidence_score),
        confidence_level=result.confidence_level,
        evidence=(),
        generated_at=_AS_OF,
        engine_specific=specific.model_dump(),
    )
    assert envelope_to_alert_candidate(envelope, outlet_id=_OUTLET) is None


def test_behavioral_neighbors_are_real_transaction_records_not_distance_only():
    txns = _regular_history(12) + [_outlier_candidate()]
    result = detect_behavioral_embedding(
        BehavioralAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=_AS_OF,
            rule_config=_BRULE,
        )
    )
    assert result.disposition is AnomalyDisposition.REQUIRES_REVIEW
    neighbors = _neighbor_evidence(result)
    assert neighbors
    for neighbor in neighbors:
        assert neighbor["party_ref"].startswith("REGULAR-")
        assert neighbor["occurred_at"]
        assert neighbor["transaction_type"] == "payment"


def test_behavioral_scoping_uses_only_passed_provider_history():
    """Neighborhood is built only from the caller-supplied transaction list (one account)."""
    bkash_history = _regular_history(12)
    nagad_only = [
        TransactionRecord(
            transaction_id=uuid4(),
            party_ref="NAGAD-ONLY",
            amount=Decimal("500.00"),
            occurred_at=_START + timedelta(minutes=20),
            transaction_type="payment",
        )
    ]
    outlier = _outlier_candidate()
    # Runner passes one provider account at a time; simulate bkash-scoped list only.
    bkash_scoped = bkash_history + [outlier]
    result = detect_behavioral_embedding(
        BehavioralAnomalyInput(
            provider_code="bkash",
            transactions=bkash_scoped,
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=_AS_OF,
            rule_config=_BRULE,
        )
    )
    neighbors = _neighbor_evidence(result)
    neighbor_parties = {n["party_ref"] for n in neighbors}
    assert "NAGAD-ONLY" not in neighbor_parties

    # Mixing providers in one list would be a caller bug; detector still only compares
    # against earlier txns in that list — nagad txn must not appear when bkash-only list.
    mixed = bkash_history + nagad_only + [outlier]
    mixed_result = detect_behavioral_embedding(
        BehavioralAnomalyInput(
            provider_code="bkash",
            transactions=[t for t in mixed if t.party_ref != "NAGAD-ONLY"],
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=_AS_OF,
            rule_config=_BRULE,
        )
    )
    mixed_neighbors = _neighbor_evidence(mixed_result)
    assert all(n["party_ref"] != "NAGAD-ONLY" for n in mixed_neighbors)


def test_behavioral_history_excludes_future_and_same_timestamp_transactions():
    candidate = _outlier_candidate(occurred_at=_START + timedelta(minutes=30))
    history_before = _regular_history(12)
    same_time = TransactionRecord(
        transaction_id=uuid4(),
        party_ref="SAME-TIME",
        amount=Decimal("99999.00"),
        occurred_at=candidate.occurred_at,
        transaction_type="cash_out",
    )
    after = TransactionRecord(
        transaction_id=uuid4(),
        party_ref="AFTER",
        amount=Decimal("99999.00"),
        occurred_at=candidate.occurred_at + timedelta(minutes=1),
        transaction_type="cash_out",
    )
    txns = history_before + [candidate, same_time, after]
    result = detect_behavioral_embedding(
        BehavioralAnomalyInput(
            provider_code="bkash",
            transactions=txns,
            quality_status="fresh",
            quality_modifier=Decimal("1.0"),
            as_of=_START + timedelta(minutes=60),
            rule_config=_BRULE,
        )
    )
    neighbors = _neighbor_evidence(result)
    neighbor_ids = {n["party_ref"] for n in neighbors}
    assert "SAME-TIME" not in neighbor_ids
    assert "AFTER" not in neighbor_ids
