"""Liquidity Forecasting Engine (Phase 3, Member 3).

Computes a rolling burn rate for a single reserve -- either one provider's
e-money account (bkash | nagad | rocket) or the shared physical-cash pool
-- from a window of recent transactions, and projects an estimated
shortage time with a confidence value.

Pure function, no HTTP/DB/UI code. Returns a ResultEnvelope (see
analytics/result_envelope.py) for Member 1 to persist and adapt.

Provider isolation note: unlike the Anomaly Detection Engine, this module
does NOT enforce single-provider input when reserve_type is "shared_cash"
-- the shared physical-cash pool is, by design (docs/schema.md §2.1),
fed by cash legs from every provider at an outlet, so aggregating across
providers is correct and expected for that one reserve type only. For
reserve_type "provider_e_money", the caller must pass a provider_code and
only that provider's transactions.
"""

from __future__ import annotations

import dataclasses
import statistics
from datetime import datetime, timedelta

from backend.analytics.confidence import clamp, combine_confidence
from backend.analytics.fixtures.stub_types import (
    TRANSACTION_STATUS_COMPLETED,
    TRANSACTION_TYPE_CASH_IN,
    TRANSACTION_TYPE_CASH_OUT,
    TRANSACTION_TYPE_PAYMENT,
    TRANSACTION_TYPE_REFUND,
    QualityAssessment,
    Transaction,
)
from backend.analytics.result_envelope import (
    LiquidityResult,
    ResultEnvelope,
    confidence_level_for,
)

LIQUIDITY_ENGINE_VERSION = "1.0.0"

RESERVE_TYPE_SHARED_CASH = "shared_cash"
RESERVE_TYPE_PROVIDER_E_MONEY = "provider_e_money"

# Below this magnitude (currency units/hour) the burn rate is treated as
# flat -- avoids a shortage projection built on noise, and guarantees the
# shortage-time division branch never runs near zero.
_ZERO_BURN_EPSILON = 0.01

# "Comfortable" sample count at which the sample-size confidence
# component saturates to 1.0; below min_sample_count the projection is
# also marked non-actionable regardless of the resulting confidence.
_SAMPLE_COMPONENT_RAMP_MULTIPLIER = 2

_BUCKET_COUNT = 6  # number of sub-windows used to estimate rate stability

_OUTFLOW_TYPES = {TRANSACTION_TYPE_CASH_OUT, TRANSACTION_TYPE_PAYMENT}
_INFLOW_TYPES = {TRANSACTION_TYPE_CASH_IN, TRANSACTION_TYPE_REFUND}


def _signed_amount(txn: Transaction) -> float:
    """Positive for outflow, negative for inflow, 0 for a no-op type.

    `adjustment` transactions are treated as a no-op for burn-rate
    purposes this phase: schema.md keeps `amount > 0` always, so there is
    no stored sign convention to read direction from, and guessing one
    would be worse than a documented simplification.
    """
    if txn.transaction_type in _OUTFLOW_TYPES:
        return txn.amount
    if txn.transaction_type in _INFLOW_TYPES:
        return -txn.amount
    return 0.0


def _filter_window(
    transactions: list[Transaction],
    *,
    reserve_type: str,
    provider_code: str | None,
    window_start: datetime,
    window_end: datetime,
) -> list[Transaction]:
    result = []
    for txn in transactions:
        if txn.status != TRANSACTION_STATUS_COMPLETED:
            continue
        if not (window_start <= txn.occurred_at <= window_end):
            continue
        if reserve_type == RESERVE_TYPE_PROVIDER_E_MONEY and txn.provider_code != provider_code:
            continue
        result.append(txn)
    return result


def _burn_rate_per_hour(transactions: list[Transaction], window_hours: float) -> float:
    if window_hours <= 0:
        return 0.0
    net_outflow = sum(_signed_amount(t) for t in transactions)
    return net_outflow / window_hours


def _rate_stability_component(
    transactions: list[Transaction],
    *,
    window_start: datetime,
    window_end: datetime,
) -> float:
    """1 - coefficient_of_variation across fixed sub-buckets, clamped to [0, 1].

    Low variance in the per-bucket rate -> high stability (near 1).
    Wildly varying rate -> low stability (near 0).
    """
    total_seconds = (window_end - window_start).total_seconds()
    if total_seconds <= 0:
        return 0.0
    bucket_seconds = total_seconds / _BUCKET_COUNT
    if bucket_seconds <= 0:
        return 0.0

    bucket_rates = []
    for i in range(_BUCKET_COUNT):
        bucket_start = window_start + timedelta(seconds=bucket_seconds * i)
        bucket_end = window_start + timedelta(seconds=bucket_seconds * (i + 1))
        bucket_txns = [t for t in transactions if bucket_start <= t.occurred_at < bucket_end]
        bucket_hours = bucket_seconds / 3600.0
        bucket_rates.append(_burn_rate_per_hour(bucket_txns, bucket_hours))

    if len(bucket_rates) < 2:
        return 0.0
    mean_rate = statistics.mean(bucket_rates)
    if abs(mean_rate) < 1e-9:
        # No meaningful average rate to compare deviation against.
        return 0.0
    stddev_rate = statistics.pstdev(bucket_rates)
    coefficient_of_variation = abs(stddev_rate / mean_rate)
    return clamp(1.0 - coefficient_of_variation)


def compute_liquidity_projection(
    transactions: list[Transaction],
    quality: QualityAssessment,
    *,
    reserve_type: str,
    outlet_id: str,
    provider_code: str | None,
    current_balance: float,
    as_of_at: datetime,
    window_start: datetime,
    window_end: datetime,
    engine_version: str = LIQUIDITY_ENGINE_VERSION,
    min_sample_count: int = 5,
) -> ResultEnvelope:
    """Compute a liquidity projection for one reserve over one window.

    reserve_type must be "shared_cash" (provider_code is ignored/None) or
    "provider_e_money" (provider_code required; transactions are scoped
    to that provider only).
    """
    if reserve_type == RESERVE_TYPE_PROVIDER_E_MONEY and not provider_code:
        raise ValueError("provider_code is required when reserve_type is 'provider_e_money'")

    windowed = _filter_window(
        transactions,
        reserve_type=reserve_type,
        provider_code=provider_code,
        window_start=window_start,
        window_end=window_end,
    )
    sample_count = len(windowed)
    window_hours = (window_end - window_start).total_seconds() / 3600.0

    burn_rate_per_hour = _burn_rate_per_hour(windowed, window_hours)
    if abs(burn_rate_per_hour) < _ZERO_BURN_EPSILON:
        burn_rate_per_hour = 0.0

    stability_component = _rate_stability_component(
        windowed, window_start=window_start, window_end=window_end
    )
    sample_component = clamp(
        sample_count / (min_sample_count * _SAMPLE_COMPONENT_RAMP_MULTIPLIER)
    )
    confidence = combine_confidence(
        sample_component, stability_component, quality.confidence_modifier
    )
    confidence_level = confidence_level_for(confidence, sample_count=sample_count)

    projected_shortage_at: datetime | None = None
    lower_bound_at: datetime | None = None
    upper_bound_at: datetime | None = None

    # Division only ever happens inside this branch -- burn_rate_per_hour
    # <= 0 (flat or replenishing) skips it entirely, so a divide-by-zero
    # is impossible by construction rather than guarded by a try/except.
    if burn_rate_per_hour > 0 and current_balance > 0:
        hours_to_shortage = current_balance / burn_rate_per_hour
        projected_shortage_at = as_of_at + timedelta(hours=hours_to_shortage)

        # Wider confidence band when the underlying feed is degraded --
        # separate from (multiplicative with) the confidence score itself.
        band_widen_multiplier = 1.0 / max(quality.confidence_modifier, 0.1)
        uncertainty_fraction = (1.0 - stability_component) * band_widen_multiplier
        band_half_width_hours = hours_to_shortage * clamp(uncertainty_fraction, 0.0, 5.0)
        lower_bound_at = as_of_at + timedelta(
            hours=max(0.0, hours_to_shortage - band_half_width_hours)
        )
        upper_bound_at = as_of_at + timedelta(
            hours=hours_to_shortage + band_half_width_hours
        )

    is_actionable = True
    non_actionable_reason: str | None = None
    if sample_count < min_sample_count:
        is_actionable = False
        non_actionable_reason = "insufficient_samples"
        projected_shortage_at = None
        lower_bound_at = None
        upper_bound_at = None

    evidence = (
        {
            "signal_code": "recent_cashout_velocity",
            "label": "Net outflow rate over window",
            "numeric_value": burn_rate_per_hour,
            "unit": "currency_per_hour",
            "direction": "increases_pressure" if burn_rate_per_hour > 0 else "reduces_pressure",
        },
        {
            "signal_code": "rate_stability",
            "label": "Burn-rate stability across window",
            "numeric_value": stability_component,
            "unit": "ratio",
            "direction": "reduces_confidence" if stability_component < 0.5 else "increases_pressure",
        },
        {
            "signal_code": "feed_freshness",
            "label": "Linked data-quality status",
            "numeric_value": quality.confidence_modifier,
            "unit": "ratio",
            "direction": "reduces_confidence" if quality.confidence_modifier < 1.0 else "increases_pressure",
        },
    )

    engine_specific = LiquidityResult(
        reserve_type=reserve_type,
        provider_code=provider_code if reserve_type == RESERVE_TYPE_PROVIDER_E_MONEY else None,
        current_balance=current_balance,
        burn_rate_per_hour=burn_rate_per_hour,
        projected_shortage_at=projected_shortage_at,
        lower_bound_at=lower_bound_at,
        upper_bound_at=upper_bound_at,
        sample_count=sample_count,
        is_actionable=is_actionable,
        non_actionable_reason=non_actionable_reason,
    )

    return ResultEnvelope(
        engine="liquidity",
        engine_version=engine_version,
        input_window_start=window_start,
        input_window_end=window_end,
        quality_assessment_ids=(quality.data_quality_assessment_id,),
        confidence=confidence,
        confidence_level=confidence_level,
        evidence=evidence,
        generated_at=as_of_at,
        engine_specific=dataclasses.asdict(engine_specific),
    )
