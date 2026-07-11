"""Unit tests for the Liquidity Forecasting Engine (pure)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.contracts.v1.enums import ConfidenceLevel, ReserveType
from app.services.liquidity.engine import (
    BalancePoint,
    LiquidityReserveInput,
    forecast_reserve,
)

_START = datetime(2026, 7, 11, 6, 0, tzinfo=timezone.utc)


def _pt(minute: int, balance: str) -> BalancePoint:
    return BalancePoint(observed_at=_START + timedelta(minutes=minute), balance=Decimal(balance))


def _input(observations, *, modifier="1.0", status="fresh", reserve=ReserveType.PROVIDER_E_MONEY):
    return LiquidityReserveInput(
        reserve_type=reserve,
        observations=observations,
        as_of=observations[-1].observed_at if observations else _START,
        quality_modifier=Decimal(modifier),
        quality_status=status,
        provider_code="bkash" if reserve is ReserveType.PROVIDER_E_MONEY else None,
    )


def test_declining_balance_projects_shortage():
    result = forecast_reserve(_input([_pt(0, "10000.00"), _pt(60, "8000.00")]))
    assert result.is_actionable
    assert result.burn_rate_per_hour == Decimal("2000.0000")
    assert result.projected_shortage_at is not None
    # 8000 remaining at 2000/hr => ~4 hours after as_of.
    expected = _START + timedelta(minutes=60) + timedelta(hours=4)
    assert abs((result.projected_shortage_at - expected).total_seconds()) < 1
    assert result.lower_bound_at <= result.projected_shortage_at <= result.upper_bound_at


def test_zero_depletion_no_shortage():
    result = forecast_reserve(_input([_pt(0, "5000.00"), _pt(60, "5000.00")]))
    assert result.is_actionable
    assert result.burn_rate_per_hour == Decimal("0")
    assert result.projected_shortage_at is None


def test_negative_depletion_no_shortage():
    result = forecast_reserve(_input([_pt(0, "5000.00"), _pt(60, "7000.00")]))
    assert result.is_actionable
    assert result.projected_shortage_at is None
    assert result.burn_rate_per_hour == Decimal("0")


def test_insufficient_samples_non_actionable():
    result = forecast_reserve(_input([_pt(0, "5000.00")]))
    assert not result.is_actionable
    assert result.non_actionable_reason == "insufficient_samples"
    assert result.confidence_level is ConfidenceLevel.UNAVAILABLE
    assert result.projected_shortage_at is None


def test_degraded_quality_non_actionable():
    result = forecast_reserve(
        _input([_pt(0, "10000.00"), _pt(60, "8000.00")], modifier="0.1", status="conflicting")
    )
    assert not result.is_actionable
    assert result.non_actionable_reason == "degraded_data_quality"
    assert result.confidence_level is ConfidenceLevel.UNAVAILABLE


def test_lower_quality_widens_uncertainty_band():
    high = forecast_reserve(_input([_pt(0, "10000.00"), _pt(60, "8000.00")], modifier="1.0"))
    low = forecast_reserve(_input([_pt(0, "10000.00"), _pt(60, "8000.00")], modifier="0.5"))
    high_band = (high.upper_bound_at - high.lower_bound_at).total_seconds()
    low_band = (low.upper_bound_at - low.lower_bound_at).total_seconds()
    assert low_band > high_band
    assert low.confidence_score < high.confidence_score


def test_contributing_signals_present():
    result = forecast_reserve(_input([_pt(0, "10000.00"), _pt(60, "8000.00")]))
    codes = {s.signal_code for s in result.signals}
    assert "burn_rate_per_hour" in codes
    assert "current_balance" in codes
    assert "time_to_shortage_hours" in codes


def test_shared_cash_forecast_is_independent():
    result = forecast_reserve(
        _input([_pt(0, "20000.00"), _pt(60, "17000.00")], reserve=ReserveType.SHARED_CASH)
    )
    assert result.reserve_type is ReserveType.SHARED_CASH
    assert result.provider_code is None
    assert result.burn_rate_per_hour == Decimal("3000.0000")
