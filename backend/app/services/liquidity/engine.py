"""Liquidity Forecasting Engine (pure, deterministic, transparent).

Forecasts each reserve independently (shared physical cash and each provider
e-money reserve) using an inspectable recent-window depletion / burn-rate model.
There is never a blended reserve forecast. Outcomes:

- no shortage when depletion (burn rate) is zero or negative;
- non-actionable when there are too few samples or quality is degraded;
- otherwise a projected shortage time with a confidence band that widens as
  confidence falls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from app.contracts.v1.enums import ConfidenceLevel, ReserveType
from app.services.analytics import config as cfg


@dataclass(frozen=True)
class BalancePoint:
    observed_at: datetime
    balance: Decimal


@dataclass(frozen=True)
class LiquidityReserveInput:
    reserve_type: ReserveType
    observations: list[BalancePoint]
    as_of: datetime
    quality_modifier: Decimal
    quality_status: str
    provider_code: str | None = None
    min_samples: int = cfg.LIQUIDITY_MIN_SAMPLES
    burn_window_minutes: int = cfg.LIQUIDITY_BURN_WINDOW_MINUTES
    target_samples: int = cfg.LIQUIDITY_TARGET_SAMPLES


@dataclass(frozen=True)
class LiquiditySignalData:
    signal_code: str
    label: str
    numeric_value: Decimal | float | None
    unit: str | None
    direction: str
    display_order: int
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LiquidityForecast:
    reserve_type: ReserveType
    provider_code: str | None
    as_of_at: datetime
    current_balance: Decimal
    burn_rate_per_hour: Decimal
    projected_shortage_at: datetime | None
    lower_bound_at: datetime | None
    upper_bound_at: datetime | None
    confidence_score: Decimal
    confidence_level: ConfidenceLevel
    sample_count: int
    is_actionable: bool
    non_actionable_reason: str | None
    signals: list[LiquiditySignalData] = field(default_factory=list)


def _q2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _q4(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"))


def forecast_reserve(data: LiquidityReserveInput) -> LiquidityForecast:
    observations = sorted(data.observations, key=lambda o: o.observed_at)
    sample_count = len(observations)

    # --- Insufficient samples => non-actionable, no misleading confidence. -----
    if sample_count < data.min_samples:
        return _non_actionable(
            data,
            sample_count=sample_count,
            current_balance=observations[-1].balance if observations else Decimal("0"),
            as_of_at=observations[-1].observed_at if observations else data.as_of,
            reason="insufficient_samples",
        )

    current_balance = observations[-1].balance
    as_of_at = observations[-1].observed_at

    # --- Recent-window burn rate (explicit, inspectable). ----------------------
    window_start = as_of_at - timedelta(minutes=data.burn_window_minutes)
    window_obs = [o for o in observations if o.observed_at >= window_start]
    if len(window_obs) < 2:
        window_obs = observations
    first, last = window_obs[0], window_obs[-1]
    hours = (last.observed_at - first.observed_at).total_seconds() / 3600.0
    if hours <= 0:
        burn_rate = Decimal("0")
    else:
        depletion = first.balance - last.balance  # positive => balance falling
        burn_rate = _q4(depletion / Decimal(str(hours)))

    # --- Confidence: sample adequacy scaled by quality modifier. ---------------
    adequacy = min(1.0, sample_count / max(1, data.target_samples))
    confidence = cfg.quantize_score(Decimal(str(adequacy)) * data.quality_modifier)

    degraded = (
        data.quality_status == "missing"
        or data.quality_modifier <= Decimal(str(cfg.LIQUIDITY_NONACTIONABLE_MODIFIER))
    )
    if degraded:
        return _non_actionable(
            data,
            sample_count=sample_count,
            current_balance=_q2(current_balance),
            as_of_at=as_of_at,
            reason="degraded_data_quality",
            burn_rate=burn_rate if burn_rate > 0 else Decimal("0"),
            confidence=confidence,
        )

    signals = _base_signals(data, burn_rate, current_balance, sample_count)

    # --- No shortage when depletion is zero or negative. -----------------------
    if burn_rate <= 0:
        signals.append(
            LiquiditySignalData(
                signal_code="no_depletion",
                label="Reserve is stable or increasing",
                numeric_value=burn_rate,
                unit="BDT/hour",
                direction="reduces_pressure",
                display_order=len(signals),
                details={"interpretation": "no_shortage"},
            )
        )
        return LiquidityForecast(
            reserve_type=data.reserve_type,
            provider_code=data.provider_code,
            as_of_at=as_of_at,
            current_balance=_q2(current_balance),
            burn_rate_per_hour=Decimal("0"),
            projected_shortage_at=None,
            lower_bound_at=None,
            upper_bound_at=None,
            confidence_score=confidence,
            confidence_level=cfg.confidence_level_for(confidence),
            sample_count=sample_count,
            is_actionable=True,
            non_actionable_reason=None,
            signals=signals,
        )

    # --- Time to shortage + widening uncertainty band. -------------------------
    hours_to_shortage = float(current_balance / burn_rate)
    projected = as_of_at + timedelta(hours=hours_to_shortage)
    band = (1.0 - float(confidence)) * cfg.LIQUIDITY_BOUND_FACTOR
    lower = as_of_at + timedelta(hours=hours_to_shortage * max(0.0, 1.0 - band))
    upper = as_of_at + timedelta(hours=hours_to_shortage * (1.0 + band))

    signals.append(
        LiquiditySignalData(
            signal_code="time_to_shortage_hours",
            label="Estimated hours until shortage",
            numeric_value=_q2(Decimal(str(hours_to_shortage))),
            unit="hours",
            direction="increases_pressure",
            display_order=len(signals),
            details={"projected_shortage_at": projected.isoformat()},
        )
    )
    if data.quality_modifier < 1:
        signals.append(
            LiquiditySignalData(
                signal_code="quality_modifier",
                label="Data-quality confidence modifier",
                numeric_value=data.quality_modifier,
                unit="ratio",
                direction="reduces_confidence",
                display_order=len(signals),
                details={"quality_status": data.quality_status},
            )
        )

    return LiquidityForecast(
        reserve_type=data.reserve_type,
        provider_code=data.provider_code,
        as_of_at=as_of_at,
        current_balance=_q2(current_balance),
        burn_rate_per_hour=burn_rate,
        projected_shortage_at=projected,
        lower_bound_at=lower,
        upper_bound_at=upper,
        confidence_score=confidence,
        confidence_level=cfg.confidence_level_for(confidence),
        sample_count=sample_count,
        is_actionable=True,
        non_actionable_reason=None,
        signals=signals,
    )


def _base_signals(
    data: LiquidityReserveInput,
    burn_rate: Decimal,
    current_balance: Decimal,
    sample_count: int,
) -> list[LiquiditySignalData]:
    return [
        LiquiditySignalData(
            signal_code="burn_rate_per_hour",
            label="Recent outflow (burn) rate",
            numeric_value=burn_rate,
            unit="BDT/hour",
            direction="increases_pressure",
            display_order=0,
            details={"window_minutes": data.burn_window_minutes},
        ),
        LiquiditySignalData(
            signal_code="current_balance",
            label="Current reserve balance",
            numeric_value=_q2(current_balance),
            unit="BDT",
            direction="reduces_pressure",
            display_order=1,
            details={},
        ),
        LiquiditySignalData(
            signal_code="sample_count",
            label="Balance observations used",
            numeric_value=sample_count,
            unit="count",
            direction="reduces_confidence",
            display_order=2,
            details={},
        ),
    ]


def _non_actionable(
    data: LiquidityReserveInput,
    *,
    sample_count: int,
    current_balance: Decimal,
    as_of_at: datetime,
    reason: str,
    burn_rate: Decimal = Decimal("0"),
    confidence: Decimal = Decimal("0"),
) -> LiquidityForecast:
    signals = [
        LiquiditySignalData(
            signal_code="non_actionable",
            label="Forecast withheld",
            numeric_value=None,
            unit=None,
            direction="reduces_confidence",
            display_order=0,
            details={"reason": reason, "quality_status": data.quality_status},
        )
    ]
    return LiquidityForecast(
        reserve_type=data.reserve_type,
        provider_code=data.provider_code,
        as_of_at=as_of_at,
        current_balance=_q2(current_balance),
        burn_rate_per_hour=Decimal("0"),
        projected_shortage_at=None,
        lower_bound_at=None,
        upper_bound_at=None,
        confidence_score=cfg.quantize_score(confidence),
        confidence_level=ConfidenceLevel.UNAVAILABLE,
        sample_count=sample_count,
        is_actionable=False,
        non_actionable_reason=reason,
        signals=signals,
    )
