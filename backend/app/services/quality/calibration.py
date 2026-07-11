"""Learned confidence calibration for the Quality engine (Feature 1).

Offline-trained logistic regression replaces the fixed penalty formula once
enough labeled examples exist. Inference uses persisted coefficients only —
no training happens at runtime.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Literal

from app.contracts.v1.enums import FeedHealthStatus
from app.services.analytics import config as cfg

logger = logging.getLogger(__name__)

CalibrationMode = Literal["fixed_formula", "learned"]

FEATURE_NAMES: tuple[str, ...] = (
    "status_fresh",
    "status_stale",
    "status_conflicting",
    "status_missing",
    "sample_count",
    "rejection_rate",
    "age_minutes",
)

_model_cache: ConfidenceCalibrationModel | None = None
_model_loaded: bool = False


def rejection_rate(*, sample_count: int, rejected_event_count: int) -> float:
    """Share of ingestion events rejected in the assessment window."""
    total = sample_count + rejected_event_count
    if rejected_event_count <= 0 or total <= 0:
        return 0.0
    return rejected_event_count / total


def build_feature_vector(
    *,
    status: FeedHealthStatus,
    sample_count: int,
    rejected_event_count: int,
    age_minutes: float | None,
) -> list[float]:
    """Build the ordered feature vector for calibration (option B)."""
    status_values = {
        FeedHealthStatus.FRESH: (1.0, 0.0, 0.0, 0.0),
        FeedHealthStatus.STALE: (0.0, 1.0, 0.0, 0.0),
        FeedHealthStatus.CONFLICTING: (0.0, 0.0, 1.0, 0.0),
        FeedHealthStatus.MISSING: (0.0, 0.0, 0.0, 1.0),
    }
    fresh, stale, conflicting, missing = status_values[status]
    return [
        fresh,
        stale,
        conflicting,
        missing,
        float(sample_count),
        rejection_rate(sample_count=sample_count, rejected_event_count=rejected_event_count),
        float(age_minutes or 0.0),
    ]


def sigmoid(logit: float) -> float:
    if logit >= 0:
        exp_neg = math.exp(-logit)
        return 1.0 / (1.0 + exp_neg)
    exp_pos = math.exp(logit)
    return exp_pos / (1.0 + exp_pos)


@dataclass(frozen=True)
class ConfidenceCalibrationModel:
    """Persisted logistic regression parameters for confidence calibration."""

    coefficients: tuple[float, ...]
    intercept: float
    feature_names: tuple[str, ...]
    trained_at: str
    n_human_examples: int
    n_synthetic_examples: int
    sklearn_version: str

    @property
    def n_labeled_examples(self) -> int:
        return self.n_human_examples + self.n_synthetic_examples

    @classmethod
    def try_load(cls, path: Path | None = None) -> ConfidenceCalibrationModel | None:
        artifact_path = path or cfg.CONFIDENCE_CALIBRATION_ARTIFACT_PATH
        if not artifact_path.is_file():
            return None
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            model = cls(
                coefficients=tuple(float(v) for v in payload["coefficients"]),
                intercept=float(payload["intercept"]),
                feature_names=tuple(payload["feature_names"]),
                trained_at=str(payload["trained_at"]),
                n_human_examples=int(payload["n_human_examples"]),
                n_synthetic_examples=int(payload["n_synthetic_examples"]),
                sklearn_version=str(payload.get("sklearn_version", "unknown")),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            logger.warning("confidence_calibration_artifact_invalid path=%s", artifact_path)
            return None
        if len(model.coefficients) != len(model.feature_names):
            logger.warning("confidence_calibration_artifact_mismatch path=%s", artifact_path)
            return None
        return model

    def save(self, path: Path | None = None) -> Path:
        artifact_path = path or cfg.CONFIDENCE_CALIBRATION_ARTIFACT_PATH
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "coefficients": list(self.coefficients),
            "intercept": self.intercept,
            "feature_names": list(self.feature_names),
            "trained_at": self.trained_at,
            "n_human_examples": self.n_human_examples,
            "n_synthetic_examples": self.n_synthetic_examples,
            "sklearn_version": self.sklearn_version,
            "min_labeled_examples": cfg.CALIBRATION_MIN_LABELED_EXAMPLES,
        }
        artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return artifact_path

    def logit(self, features: list[float]) -> float:
        if len(features) != len(self.coefficients):
            raise ValueError("feature vector length does not match coefficients")
        return self.intercept + sum(c * x for c, x in zip(self.coefficients, features, strict=True))

    def contributions(self, features: list[float]) -> dict[str, float]:
        contribs = {
            name: coef * value
            for name, coef, value in zip(self.feature_names, self.coefficients, features, strict=True)
        }
        contribs["intercept"] = self.intercept
        return contribs

    def predict_modifier(
        self, features: list[float]
    ) -> tuple[Decimal, dict[str, float], float]:
        """Return quantized modifier, per-feature contributions, and raw logit."""
        logit = self.logit(features)
        probability = sigmoid(logit)
        modifier = cfg.quantize_score(probability)
        return modifier, self.contributions(features), logit


def resolve_calibration_mode(model: ConfidenceCalibrationModel | None) -> CalibrationMode:
    if model is None or model.n_labeled_examples < cfg.CALIBRATION_MIN_LABELED_EXAMPLES:
        return "fixed_formula"
    return "learned"


def get_calibration_model(*, force_reload: bool = False) -> ConfidenceCalibrationModel | None:
    """Load the persisted calibration model once per process."""
    global _model_cache, _model_loaded
    if force_reload:
        _model_loaded = False
        _model_cache = None
    if not _model_loaded:
        _model_cache = ConfidenceCalibrationModel.try_load()
        _model_loaded = True
    return _model_cache


def reset_calibration_cache() -> None:
    """Clear the in-process model cache (for tests)."""
    global _model_cache, _model_loaded
    _model_cache = None
    _model_loaded = False


def log_calibration_mode(mode: CalibrationMode, *, n_labeled: int) -> None:
    logger.info(
        "confidence_calibration_mode=%s n_labeled=%s threshold=%s",
        mode,
        n_labeled,
        cfg.CALIBRATION_MIN_LABELED_EXAMPLES,
    )


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
