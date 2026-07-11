"""ResultEnvelope -> AlertCandidate seam and guardrail unit tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.contracts.v1.enums import AnalyticsEngine, ConfidenceLevel, ReserveType
from app.contracts.v1.envelope import (
    AnomalyEngineSpecific,
    LiquidityEngineSpecific,
    ResultEnvelope,
)
from app.services.alert_candidate_adapter import envelope_to_alert_candidate

_NOW = datetime(2026, 7, 11, 8, 0, tzinfo=timezone.utc)
_OUTLET = uuid4()


def _liquidity_envelope(*, is_actionable: bool, shortage: bool) -> ResultEnvelope:
    specific = LiquidityEngineSpecific(
        reserve_type=ReserveType.PROVIDER_E_MONEY,
        provider_code="bkash",
        current_balance="8000.00",
        burn_rate_per_hour="2000.0000",
        projected_shortage_at=_NOW if shortage else None,
        lower_bound_at=_NOW if shortage else None,
        upper_bound_at=_NOW if shortage else None,
        sample_count=2,
        is_actionable=is_actionable,
        non_actionable_reason=None if is_actionable else "degraded_data_quality",
    )
    return ResultEnvelope(
        engine=AnalyticsEngine.LIQUIDITY,
        engine_version="liquidity-v1",
        input_window_start=_NOW,
        input_window_end=_NOW,
        quality_assessment_ids=(uuid4(),),
        confidence=0.7,
        confidence_level=ConfidenceLevel.MEDIUM,
        evidence=(),
        generated_at=_NOW,
        engine_specific=specific.model_dump(),
    )


def _anomaly_envelope(disposition: str) -> ResultEnvelope:
    specific = AnomalyEngineSpecific(
        pattern="near_identical_amounts",
        provider_code="bkash",
        window_start=_NOW,
        window_end=_NOW,
        disposition=disposition,
        reason_code="near_identical_amount_cluster",
        evidence_summary="6 transactions of about 1000.00 BDT.",
        plausible_benign_explanation="May reflect normal festival demand.",
        suppression_disposition="none",
    )
    return ResultEnvelope(
        engine=AnalyticsEngine.ANOMALY,
        engine_version="anomaly-v1",
        input_window_start=_NOW,
        input_window_end=_NOW,
        quality_assessment_ids=(uuid4(),),
        confidence=0.9,
        confidence_level=ConfidenceLevel.HIGH,
        evidence=(),
        generated_at=_NOW,
        engine_specific=specific.model_dump(),
    )


def test_actionable_liquidity_shortage_produces_candidate():
    candidate = envelope_to_alert_candidate(
        _liquidity_envelope(is_actionable=True, shortage=True), outlet_id=_OUTLET, provider_id=uuid4()
    )
    assert candidate is not None
    assert candidate.is_alertable
    assert candidate.source_links.quality_assessment_ids


def test_non_actionable_liquidity_produces_no_candidate():
    candidate = envelope_to_alert_candidate(
        _liquidity_envelope(is_actionable=False, shortage=False), outlet_id=_OUTLET, provider_id=uuid4()
    )
    assert candidate is None


def test_liquidity_without_shortage_produces_no_candidate():
    candidate = envelope_to_alert_candidate(
        _liquidity_envelope(is_actionable=True, shortage=False), outlet_id=_OUTLET, provider_id=uuid4()
    )
    assert candidate is None


def test_requires_review_anomaly_produces_candidate():
    candidate = envelope_to_alert_candidate(
        _anomaly_envelope("requires_review"), outlet_id=_OUTLET
    )
    assert candidate is not None
    assert candidate.is_alertable
    assert candidate.plausible_benign_explanation


def test_suppressed_anomaly_produces_no_candidate():
    candidate = envelope_to_alert_candidate(
        _anomaly_envelope("suppressed_data_quality"), outlet_id=_OUTLET
    )
    assert candidate is None


def test_inconclusive_anomaly_produces_no_candidate():
    candidate = envelope_to_alert_candidate(
        _anomaly_envelope("inconclusive"), outlet_id=_OUTLET
    )
    assert candidate is None
