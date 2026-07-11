"""Configurable, documented analytics constants and shared confidence helpers.

All engine formulas are intentionally transparent and inspectable. Thresholds
live here (and, for the anomaly rule, in ``anomaly_rules.configuration``) so the
behavior is reproducible and auditable rather than hidden in scattered literals.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.contracts.v1.enums import ConfidenceLevel

# --- Engine versions (traceable in persisted outputs) ------------------------
QUALITY_ENGINE_VERSION = "quality-v1"
LIQUIDITY_ENGINE_VERSION = "liquidity-v1"
ANOMALY_ENGINE_VERSION = "anomaly-v1"

# --- Data-quality engine defaults --------------------------------------------
# Minimum combined samples (balance observations + transactions) below which a
# feed is treated as having insufficient evidence for a confident assessment.
QUALITY_MIN_SAMPLES = 2
# A feed whose most recent source observation is older than this (relative to the
# analysis "as of" time = newest observation for the outlet) is classified as
# stale. Set beyond a single simulated session so ordinary sequential feeds are
# not falsely flagged; a genuinely lagging feed still trips the threshold.
QUALITY_STALE_AFTER_MINUTES = 240
# Base confidence modifier per feed-health classification.
QUALITY_STATUS_MODIFIER = {
    "fresh": 1.0,
    "stale": 0.6,
    "conflicting": 0.4,
    "missing": 0.0,
}
# Floor applied when rejections are present but not total.
QUALITY_REJECTION_FLOOR = 0.3

# --- Liquidity engine defaults -----------------------------------------------
# Minimum balance observations required to forecast a burn rate.
LIQUIDITY_MIN_SAMPLES = 2
# Recent window used for the burn-rate (depletion) estimate.
LIQUIDITY_BURN_WINDOW_MINUTES = 180
# Sample count at which sample-adequacy confidence saturates. Complete opening +
# closing coverage (2 points) yields solid-but-not-maximal confidence.
LIQUIDITY_TARGET_SAMPLES = 3
# Half-width of the uncertainty band as a fraction of time-to-shortage at zero
# confidence. The band narrows linearly as confidence rises.
LIQUIDITY_BOUND_FACTOR = 0.6
# Quality modifier at/below which a projection becomes non-actionable.
LIQUIDITY_NONACTIONABLE_MODIFIER = 0.2

# --- Anomaly engine defaults (rule config overrides these when present) -------
ANOMALY_DEFAULT_CONFIG = {
    "window_minutes": 15,
    "amount_tolerance_pct": 2.0,
    "minimum_count": 5,
    "minimum_distinct_parties": 1,
}
VELOCITY_SPIKE_DEFAULT_CONFIG = {
    "window_minutes": 10,
    "std_dev_threshold": 2.0,
    "minimum_baseline_windows": 3,
    "minimum_spike_count": 8,
}
BALANCE_INCONSISTENCY_DEFAULT_CONFIG = {
    "min_discrepancy_amount": 100.0,
    "min_discrepancy_pct": 0.5,
    "staleness_soft_minutes": 120,
}
# Quality modifier at/below which an otherwise-detected pattern is suppressed.
ANOMALY_SUPPRESSION_MODIFIER = 0.5

# --- Confidence level thresholds ---------------------------------------------
CONFIDENCE_HIGH = Decimal("0.75")
CONFIDENCE_MEDIUM = Decimal("0.50")
CONFIDENCE_LOW = Decimal("0.25")

_SCORE_QUANT = Decimal("0.0001")


def quantize_score(value: float | Decimal) -> Decimal:
    """Clamp to [0, 1] and quantize to the ``score_unit`` numeric(5,4) domain."""
    score = value if isinstance(value, Decimal) else Decimal(str(value))
    if score < 0:
        score = Decimal("0")
    elif score > 1:
        score = Decimal("1")
    return score.quantize(_SCORE_QUANT, rounding=ROUND_HALF_UP)


def confidence_level_for(score: Decimal, *, actionable: bool = True) -> ConfidenceLevel:
    """Map a numeric confidence score to a categorical level.

    Non-actionable outcomes always report ``unavailable`` so degraded or
    unsupported results never present as confident.
    """
    if not actionable:
        return ConfidenceLevel.UNAVAILABLE
    if score >= CONFIDENCE_HIGH:
        return ConfidenceLevel.HIGH
    if score >= CONFIDENCE_MEDIUM:
        return ConfidenceLevel.MEDIUM
    if score >= CONFIDENCE_LOW:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.UNAVAILABLE
