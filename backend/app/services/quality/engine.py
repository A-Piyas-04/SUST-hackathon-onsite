"""Data Quality & Confidence Engine (pure, deterministic).

Classifies a provider feed as ``fresh``/``stale``/``missing``/``conflicting``
with an explicit precedence, emits machine-readable issue evidence, and derives a
confidence modifier. The engine is a pure function of its structured inputs so it
is fully unit-testable and reproducible; the runner supplies ledger-derived
inputs and persists the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from app.contracts.v1.enums import FeedHealthStatus, QualityIssueType, Severity
from app.services.analytics import config as cfg
from app.services.quality.calibration import (
    build_feature_vector,
    get_calibration_model,
    log_calibration_mode,
    resolve_calibration_mode,
)

CalibrationMode = Literal["fixed_formula", "learned"]

# Precedence when multiple issues coexist: the highest-precedence classification
# wins the top-level status while all detected issues remain recorded as evidence.
# missing (cannot assess) > conflicting (integrity failure) > stale (age) > fresh.
_STATUS_PRECEDENCE = [
    FeedHealthStatus.MISSING,
    FeedHealthStatus.CONFLICTING,
    FeedHealthStatus.STALE,
    FeedHealthStatus.FRESH,
]


@dataclass(frozen=True)
class BalanceObservation:
    observed_at: datetime
    balance: Decimal
    received_at: datetime | None = None


@dataclass(frozen=True)
class ProviderQualityInput:
    provider_code: str
    observations: list[BalanceObservation]
    transaction_count: int
    rejected_event_count: int
    as_of: datetime
    min_samples: int = cfg.QUALITY_MIN_SAMPLES
    stale_after_minutes: int = cfg.QUALITY_STALE_AFTER_MINUTES


@dataclass(frozen=True)
class QualityIssue:
    issue_type: QualityIssueType
    severity: Severity
    field_name: str | None
    evidence: dict[str, Any]


@dataclass(frozen=True)
class QualityAssessmentResult:
    status: FeedHealthStatus
    confidence_modifier: Decimal
    sample_count: int
    latest_source_at: datetime | None
    trusted_balance: Decimal | None
    trusted_observed_at: datetime | None
    summary: str
    issues: list[QualityIssue] = field(default_factory=list)
    calibration_mode: CalibrationMode = "fixed_formula"
    feature_contributions: dict[str, float] = field(default_factory=dict)


def compute_fixed_confidence_modifier(
    *,
    status: FeedHealthStatus,
    sample_count: int,
    min_samples: int,
    rejected_event_count: int,
) -> Decimal:
    """Fixed penalty formula (Step 3 of the quality pipeline)."""
    modifier = Decimal(str(cfg.QUALITY_STATUS_MODIFIER[status.value]))
    if status != FeedHealthStatus.MISSING and min_samples > 0:
        adequacy = min(1.0, sample_count / min_samples)
        modifier = modifier * Decimal(str(adequacy))
    total_events = sample_count + rejected_event_count
    if rejected_event_count > 0 and total_events > 0:
        rejection_ratio = rejected_event_count / total_events
        penalty = max(cfg.QUALITY_REJECTION_FLOOR, 1.0 - rejection_ratio)
        modifier = modifier * Decimal(str(penalty))
    return cfg.quantize_score(modifier)


def _resolve_confidence_modifier(
    *,
    status: FeedHealthStatus,
    sample_count: int,
    min_samples: int,
    rejected_event_count: int,
    age_minutes: float | None,
) -> tuple[Decimal, CalibrationMode, dict[str, float]]:
    model = get_calibration_model()
    mode = resolve_calibration_mode(model)
    n_labeled = model.n_labeled_examples if model is not None else 0
    log_calibration_mode(mode, n_labeled=n_labeled)

    if mode == "learned" and model is not None:
        features = build_feature_vector(
            status=status,
            sample_count=sample_count,
            rejected_event_count=rejected_event_count,
            age_minutes=age_minutes,
        )
        modifier, contributions, _logit = model.predict_modifier(features)
        return modifier, mode, contributions

    modifier = compute_fixed_confidence_modifier(
        status=status,
        sample_count=sample_count,
        min_samples=min_samples,
        rejected_event_count=rejected_event_count,
    )
    return modifier, "fixed_formula", {}


def _detect_conflict(observations: list[BalanceObservation]) -> tuple[bool, list[dict[str, Any]]]:
    by_time: dict[datetime, set[str]] = {}
    for obs in observations:
        by_time.setdefault(obs.observed_at, set()).add(format(obs.balance, "f"))
    conflicts = [
        {"observed_at": ts.isoformat(), "distinct_balances": sorted(vals)}
        for ts, vals in by_time.items()
        if len(vals) > 1
    ]
    return bool(conflicts), conflicts


def _last_trusted(
    observations: list[BalanceObservation],
) -> tuple[Decimal | None, datetime | None]:
    """Latest observation at a timestamp with no conflicting candidate."""
    by_time: dict[datetime, set[str]] = {}
    for obs in observations:
        by_time.setdefault(obs.observed_at, set()).add(format(obs.balance, "f"))
    trusted = [o for o in observations if len(by_time[o.observed_at]) == 1]
    if not trusted:
        return None, None
    latest = max(trusted, key=lambda o: o.observed_at)
    return latest.balance, latest.observed_at


def assess_provider_quality(data: ProviderQualityInput) -> QualityAssessmentResult:
    """Classify feed health and derive a confidence modifier with evidence."""
    issues: list[QualityIssue] = []
    observations = data.observations
    sample_count = len(observations) + data.transaction_count
    latest_source_at = max((o.observed_at for o in observations), default=None)

    has_conflict, conflict_evidence = _detect_conflict(observations)
    is_missing = sample_count == 0
    age_minutes: float | None = None
    is_stale = False
    if latest_source_at is not None:
        age_minutes = (data.as_of - latest_source_at).total_seconds() / 60.0
        is_stale = age_minutes > data.stale_after_minutes

    # --- Record every detected issue (evidence is preserved regardless of the
    # winning top-level status). ------------------------------------------------
    if is_missing:
        issues.append(
            QualityIssue(
                QualityIssueType.MISSING_FEED,
                Severity.HIGH,
                None,
                {"reason": "no_samples_in_window"},
            )
        )
    if has_conflict:
        issues.append(
            QualityIssue(
                QualityIssueType.CONFLICTING_SNAPSHOT,
                Severity.HIGH,
                "balance",
                {"conflicts": conflict_evidence},
            )
        )
    if is_stale and age_minutes is not None:
        issues.append(
            QualityIssue(
                QualityIssueType.LATE_ARRIVAL,
                Severity.MEDIUM,
                None,
                {
                    "age_minutes": round(age_minutes, 2),
                    "stale_after_minutes": data.stale_after_minutes,
                    "latest_source_at": latest_source_at.isoformat()
                    if latest_source_at
                    else None,
                },
            )
        )
    if not is_missing and sample_count < data.min_samples:
        issues.append(
            QualityIssue(
                QualityIssueType.INSUFFICIENT_SAMPLES,
                Severity.MEDIUM,
                None,
                {"sample_count": sample_count, "min_samples": data.min_samples},
            )
        )
    if data.rejected_event_count > 0:
        issues.append(
            QualityIssue(
                QualityIssueType.MALFORMED_PAYLOAD,
                Severity.MEDIUM,
                None,
                {"rejected_event_count": data.rejected_event_count},
            )
        )

    # --- Resolve top-level status by precedence. -------------------------------
    detected = set()
    if is_missing:
        detected.add(FeedHealthStatus.MISSING)
    if has_conflict:
        detected.add(FeedHealthStatus.CONFLICTING)
    if is_stale:
        detected.add(FeedHealthStatus.STALE)
    status = next((s for s in _STATUS_PRECEDENCE if s in detected), FeedHealthStatus.FRESH)

    # --- Confidence modifier: fixed formula or learned calibration. ------------
    modifier, calibration_mode, feature_contributions = _resolve_confidence_modifier(
        status=status,
        sample_count=sample_count,
        min_samples=data.min_samples,
        rejected_event_count=data.rejected_event_count,
        age_minutes=age_minutes,
    )

    trusted_balance, trusted_observed_at = _last_trusted(observations)

    summary = _build_summary(status, sample_count, len(issues))

    return QualityAssessmentResult(
        status=status,
        confidence_modifier=modifier,
        sample_count=sample_count,
        latest_source_at=latest_source_at,
        trusted_balance=trusted_balance,
        trusted_observed_at=trusted_observed_at,
        summary=summary,
        issues=issues,
        calibration_mode=calibration_mode,
        feature_contributions=feature_contributions,
    )


def _build_summary(status: FeedHealthStatus, sample_count: int, issue_count: int) -> str:
    descriptions = {
        FeedHealthStatus.FRESH: "Feed is current with sufficient recent samples.",
        FeedHealthStatus.STALE: "Latest feed data is older than the freshness window.",
        FeedHealthStatus.MISSING: "No feed samples were available in the analysis window.",
        FeedHealthStatus.CONFLICTING: "Conflicting balance snapshots were observed for the same time.",
    }
    base = descriptions[status]
    return f"{base} Samples={sample_count}, issues={issue_count}."
