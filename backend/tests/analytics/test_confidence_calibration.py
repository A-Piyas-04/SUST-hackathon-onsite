"""Tests for learned confidence calibration (Feature 1)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from app.contracts.v1.enums import FeedHealthStatus
from app.services.analytics import config as cfg
from app.services.quality.calibration import (
    ConfidenceCalibrationModel,
    build_feature_vector,
    reset_calibration_cache,
    sigmoid,
)
from app.services.quality.engine import (
    BalanceObservation,
    ProviderQualityInput,
    assess_provider_quality,
    compute_fixed_confidence_modifier,
)

_AS_OF = datetime(2026, 7, 11, 8, 0, tzinfo=timezone.utc)


def _obs(minute: int, balance: str) -> BalanceObservation:
    ts = _AS_OF - timedelta(minutes=minute)
    return BalanceObservation(observed_at=ts, balance=Decimal(balance), received_at=ts)


@pytest.fixture(autouse=True)
def _reset_cache():
    reset_calibration_cache()
    yield
    reset_calibration_cache()


@pytest.fixture
def artifact_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "confidence_calibration.json"
    model = ConfidenceCalibrationModel(
        coefficients=(0.5, -0.3, -0.6, -1.2, 0.04, -0.8, -0.002),
        intercept=-0.1,
        feature_names=(
            "status_fresh",
            "status_stale",
            "status_conflicting",
            "status_missing",
            "sample_count",
            "rejection_rate",
            "age_minutes",
        ),
        trained_at="2026-07-11T00:00:00Z",
        n_human_examples=12,
        n_synthetic_examples=8,
        sklearn_version="1.5.0",
    )
    model.save(path)
    monkeypatch.setattr(cfg, "CONFIDENCE_CALIBRATION_ARTIFACT_PATH", path)
    return path


def _stale_input(*, rejected: int = 1) -> ProviderQualityInput:
    return ProviderQualityInput(
        provider_code="bkash",
        observations=[_obs(300, "500.00")],
        transaction_count=0,
        rejected_event_count=rejected,
        as_of=_AS_OF,
        stale_after_minutes=30,
        min_samples=2,
    )


def test_cold_start_matches_fixed_formula(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    missing_artifact = tmp_path / "missing.json"
    monkeypatch.setattr(cfg, "CONFIDENCE_CALIBRATION_ARTIFACT_PATH", missing_artifact)

    cases: list[tuple[ProviderQualityInput, FeedHealthStatus, int]] = [
        (
            ProviderQualityInput(
                provider_code="bkash",
                observations=[],
                transaction_count=0,
                rejected_event_count=0,
                as_of=_AS_OF,
            ),
            FeedHealthStatus.MISSING,
            0,
        ),
        (
            ProviderQualityInput(
                provider_code="bkash",
                observations=[_obs(10, "500.00"), _obs(5, "480.00")],
                transaction_count=4,
                rejected_event_count=0,
                as_of=_AS_OF,
            ),
            FeedHealthStatus.FRESH,
            6,
        ),
        (
            _stale_input(rejected=0),
            FeedHealthStatus.STALE,
            1,
        ),
        (
            ProviderQualityInput(
                provider_code="bkash",
                observations=[_obs(10, "500.00"), _obs(5, "480.00")],
                transaction_count=4,
                rejected_event_count=3,
                as_of=_AS_OF,
            ),
            FeedHealthStatus.FRESH,
            6,
        ),
    ]
    ts = _AS_OF - timedelta(minutes=5)
    cases.append(
        (
            ProviderQualityInput(
                provider_code="bkash",
                observations=[
                    BalanceObservation(observed_at=ts, balance=Decimal("500.00"), received_at=ts),
                    BalanceObservation(observed_at=ts, balance=Decimal("900.00"), received_at=ts),
                ],
                transaction_count=2,
                rejected_event_count=0,
                as_of=_AS_OF,
            ),
            FeedHealthStatus.CONFLICTING,
            4,
        )
    )

    for data, status, sample_count in cases:
        expected = compute_fixed_confidence_modifier(
            status=status,
            sample_count=sample_count,
            min_samples=data.min_samples,
            rejected_event_count=data.rejected_event_count,
        )
        result = assess_provider_quality(data)
        assert result.calibration_mode == "fixed_formula"
        assert result.confidence_modifier == expected
        assert result.feature_contributions == {}


def test_cold_start_with_insufficient_artifact_examples(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    path = tmp_path / "small.json"
    model = ConfidenceCalibrationModel(
        coefficients=(0.1,) * 7,
        intercept=0.0,
        feature_names=(
            "status_fresh",
            "status_stale",
            "status_conflicting",
            "status_missing",
            "sample_count",
            "rejection_rate",
            "age_minutes",
        ),
        trained_at="2026-07-11T00:00:00Z",
        n_human_examples=5,
        n_synthetic_examples=4,
        sklearn_version="1.5.0",
    )
    model.save(path)
    monkeypatch.setattr(cfg, "CONFIDENCE_CALIBRATION_ARTIFACT_PATH", path)

    result = assess_provider_quality(_stale_input())
    expected = compute_fixed_confidence_modifier(
        status=FeedHealthStatus.STALE,
        sample_count=1,
        min_samples=2,
        rejected_event_count=1,
    )
    assert result.calibration_mode == "fixed_formula"
    assert result.confidence_modifier == expected


def test_learned_path_used_when_trained(artifact_path: Path):
    result = assess_provider_quality(_stale_input())
    assert result.calibration_mode == "learned"
    assert result.feature_contributions
    assert "intercept" in result.feature_contributions


def test_contributions_relate_to_modifier():
    features = build_feature_vector(
        status=FeedHealthStatus.STALE,
        sample_count=1,
        rejected_event_count=1,
        age_minutes=300.0,
    )
    model = ConfidenceCalibrationModel(
        coefficients=(0.5, -0.3, -0.6, -1.2, 0.04, -0.8, -0.002),
        intercept=-0.1,
        feature_names=(
            "status_fresh",
            "status_stale",
            "status_conflicting",
            "status_missing",
            "sample_count",
            "rejection_rate",
            "age_minutes",
        ),
        trained_at="2026-07-11T00:00:00Z",
        n_human_examples=12,
        n_synthetic_examples=8,
        sklearn_version="1.5.0",
    )
    modifier, contributions, logit = model.predict_modifier(features)
    assert logit == pytest.approx(sum(contributions.values()))
    assert float(modifier) == pytest.approx(sigmoid(logit), abs=1e-4)


def test_end_to_end_fixed_vs_learned_side_by_side(artifact_path: Path):
    data = _stale_input(rejected=1)
    fixed = compute_fixed_confidence_modifier(
        status=FeedHealthStatus.STALE,
        sample_count=1,
        min_samples=2,
        rejected_event_count=1,
    )
    learned = assess_provider_quality(data)
    features = build_feature_vector(
        status=FeedHealthStatus.STALE,
        sample_count=1,
        rejected_event_count=1,
        age_minutes=300.0,
    )
    model = ConfidenceCalibrationModel.try_load(artifact_path)
    assert model is not None
    learned_modifier, contributions, logit = model.predict_modifier(features)

    print(
        json.dumps(
            {
                "inputs": {
                    "status": "stale",
                    "sample_count": 1,
                    "rejected_event_count": 1,
                    "age_minutes": 300.0,
                },
                "fixed_formula": {"modifier": str(fixed), "mode": "fixed_formula"},
                "learned_model": {
                    "modifier": str(learned.confidence_modifier),
                    "mode": learned.calibration_mode,
                    "contributions": contributions,
                    "logit": logit,
                },
            },
            indent=2,
        )
    )

    assert learned.calibration_mode == "learned"
    assert learned.confidence_modifier == learned_modifier
    assert fixed != learned.confidence_modifier or contributions
