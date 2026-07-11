"""Shared ResultEnvelope contract for the Phase 3 analytics engines.

Both the Liquidity Forecasting Engine and the Anomaly Detection Engine
return a ResultEnvelope. It is the frozen hand-off contract to Member 1,
who persists it and adapts it into an AlertCandidate. Member 3 (this
package) never writes HTTP or database integration code.

Field names deliberately mirror docs/schema.md so Member 1's persistence
adapter can map this 1:1 onto `analytics_runs` / `liquidity_projections` /
`anomaly_flags` without semantic guesswork.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

CONFIDENCE_LEVEL_HIGH = "high"
CONFIDENCE_LEVEL_MEDIUM = "medium"
CONFIDENCE_LEVEL_LOW = "low"
CONFIDENCE_LEVEL_UNAVAILABLE = "unavailable"

# Named thresholds for bucketing a 0..1 confidence score into a confidence_level.
_HIGH_THRESHOLD = 0.75
_MEDIUM_THRESHOLD = 0.45


def confidence_level_for(score: float, *, sample_count: int) -> str:
    """Bucket a numeric confidence score into the confidence_level enum."""
    if sample_count <= 0 or score <= 0.0:
        return CONFIDENCE_LEVEL_UNAVAILABLE
    if score >= _HIGH_THRESHOLD:
        return CONFIDENCE_LEVEL_HIGH
    if score >= _MEDIUM_THRESHOLD:
        return CONFIDENCE_LEVEL_MEDIUM
    return CONFIDENCE_LEVEL_LOW


@dataclass(frozen=True)
class ResultEnvelope:
    """Versioned, immutable output contract shared by both engines.

    engine_specific carries the fields unique to each engine (see
    LiquidityResult / AnomalyResult below), stored as a plain dict via
    dataclasses.asdict() so the envelope itself stays engine-agnostic.
    """

    engine: str  # "liquidity" | "anomaly"
    engine_version: str
    input_window_start: datetime
    input_window_end: datetime
    quality_assessment_ids: tuple[str, ...]
    confidence: float
    confidence_level: str
    evidence: tuple[dict, ...]
    generated_at: datetime
    engine_specific: dict


@dataclass(frozen=True)
class LiquidityResult:
    """engine_specific payload for a "liquidity" ResultEnvelope."""

    reserve_type: str  # "shared_cash" | "provider_e_money"
    provider_code: str | None  # None for shared_cash
    current_balance: float
    burn_rate_per_hour: float  # signed; <= 0 means flat/replenishing
    projected_shortage_at: datetime | None
    lower_bound_at: datetime | None
    upper_bound_at: datetime | None
    sample_count: int
    is_actionable: bool
    non_actionable_reason: str | None


@dataclass(frozen=True)
class AnomalyResult:
    """engine_specific payload for an "anomaly" ResultEnvelope."""

    pattern: str  # always "near_identical_amounts" this phase
    provider_code: str
    window_start: datetime
    window_end: datetime
    disposition: str  # anomaly_disposition value
    reason_code: str
    evidence_summary: str
    plausible_benign_explanation: str
    suppression_disposition: str
    account_refs: tuple[str, ...]
