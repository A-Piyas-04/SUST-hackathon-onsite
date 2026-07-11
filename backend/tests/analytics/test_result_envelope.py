import dataclasses

import pytest

from backend.analytics.result_envelope import (
    AnomalyResult,
    LiquidityResult,
    ResultEnvelope,
    confidence_level_for,
)


def _build_envelope(base_time):
    return ResultEnvelope(
        engine="liquidity",
        engine_version="1.0.0",
        input_window_start=base_time,
        input_window_end=base_time,
        quality_assessment_ids=("qa-1",),
        confidence=0.8,
        confidence_level="high",
        evidence=({"evidence_type": "count", "label": "x", "value": 1, "display_order": 0},),
        generated_at=base_time,
        engine_specific={"reserve_type": "shared_cash"},
    )


def test_envelope_has_required_fields(base_time):
    envelope = _build_envelope(base_time)
    assert envelope.engine == "liquidity"
    assert envelope.engine_version == "1.0.0"
    assert envelope.input_window_start == base_time
    assert envelope.input_window_end == base_time
    assert envelope.quality_assessment_ids == ("qa-1",)
    assert envelope.confidence == 0.8
    assert envelope.confidence_level == "high"
    assert isinstance(envelope.evidence, tuple)
    assert envelope.generated_at == base_time
    assert isinstance(envelope.engine_specific, dict)


def test_envelope_is_frozen(base_time):
    envelope = _build_envelope(base_time)
    with pytest.raises(dataclasses.FrozenInstanceError):
        envelope.confidence = 0.1  # type: ignore[misc]


def test_envelope_serializes_to_dict(base_time):
    envelope = _build_envelope(base_time)
    as_dict = dataclasses.asdict(envelope)
    assert as_dict["engine"] == "liquidity"
    assert as_dict["engine_specific"] == {"reserve_type": "shared_cash"}


def test_liquidity_result_and_anomaly_result_asdict_shapes(base_time):
    liquidity = LiquidityResult(
        reserve_type="shared_cash",
        provider_code=None,
        current_balance=1000.0,
        burn_rate_per_hour=0.0,
        projected_shortage_at=None,
        lower_bound_at=None,
        upper_bound_at=None,
        sample_count=0,
        is_actionable=False,
        non_actionable_reason="insufficient_samples",
    )
    anomaly = AnomalyResult(
        pattern="near_identical_amounts",
        provider_code="bkash",
        window_start=base_time,
        window_end=base_time,
        disposition="requires_review",
        reason_code="near_identical_amounts_cluster",
        evidence_summary="summary",
        plausible_benign_explanation="benign",
        suppression_disposition="NOT_SUPPRESSED",
        account_refs=("syn-1",),
    )
    assert dataclasses.asdict(liquidity)["reserve_type"] == "shared_cash"
    assert dataclasses.asdict(anomaly)["pattern"] == "near_identical_amounts"


@pytest.mark.parametrize(
    "score,sample_count,expected",
    [
        (0.9, 10, "high"),
        (0.5, 10, "medium"),
        (0.2, 10, "low"),
        (0.0, 10, "unavailable"),
        (0.9, 0, "unavailable"),
    ],
)
def test_confidence_level_for(score, sample_count, expected):
    assert confidence_level_for(score, sample_count=sample_count) == expected
