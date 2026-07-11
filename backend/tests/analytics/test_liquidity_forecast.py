from datetime import timedelta

from backend.analytics.liquidity_forecast import (
    RESERVE_TYPE_PROVIDER_E_MONEY,
    RESERVE_TYPE_SHARED_CASH,
    compute_liquidity_projection,
)


def _window(base_time, hours=2):
    return base_time, base_time + timedelta(hours=hours)


def test_zero_burn_no_shortage_projected(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    transactions = [
        txn_factory(
            provider_code="bkash",
            transaction_type="cash_out",
            amount=500.0,
            occurred_at=window_start + timedelta(minutes=10),
        ),
        txn_factory(
            provider_code="bkash",
            transaction_type="cash_in",
            amount=500.0,
            occurred_at=window_start + timedelta(minutes=90),
        ),
    ]

    envelope = compute_liquidity_projection(
        transactions,
        fresh_quality(),
        reserve_type=RESERVE_TYPE_PROVIDER_E_MONEY,
        outlet_id="outlet-1",
        provider_code="bkash",
        current_balance=0.0,  # also proves no divide-by-zero when balance is 0
        as_of_at=window_end,
        window_start=window_start,
        window_end=window_end,
    )

    assert envelope.engine_specific["burn_rate_per_hour"] == 0.0
    assert envelope.engine_specific["projected_shortage_at"] is None
    assert envelope.engine_specific["lower_bound_at"] is None
    assert envelope.engine_specific["upper_bound_at"] is None


def test_negative_burn_rate_replenishing(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    transactions = [
        txn_factory(
            provider_code="bkash",
            transaction_type="cash_in",
            amount=500.0,
            occurred_at=window_start + timedelta(minutes=15 * i),
        )
        for i in range(5)
    ]

    envelope = compute_liquidity_projection(
        transactions,
        fresh_quality(),
        reserve_type=RESERVE_TYPE_PROVIDER_E_MONEY,
        outlet_id="outlet-1",
        provider_code="bkash",
        current_balance=5000.0,
        as_of_at=window_end,
        window_start=window_start,
        window_end=window_end,
    )

    assert envelope.engine_specific["burn_rate_per_hour"] <= 0
    assert envelope.engine_specific["projected_shortage_at"] is None
    assert envelope.engine_specific["lower_bound_at"] is None
    assert envelope.engine_specific["upper_bound_at"] is None
    assert envelope.engine_specific["is_actionable"] is True


def test_replenishment_resets_trend(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    steady_outflow = [
        txn_factory(
            provider_code="bkash",
            transaction_type="cash_out",
            amount=500.0,
            occurred_at=window_start + timedelta(minutes=20 * i),
        )
        for i in range(6)
    ]

    def run(transactions):
        return compute_liquidity_projection(
            transactions,
            fresh_quality(),
            reserve_type=RESERVE_TYPE_PROVIDER_E_MONEY,
            outlet_id="outlet-1",
            provider_code="bkash",
            current_balance=3000.0,
            as_of_at=window_end,
            window_start=window_start,
            window_end=window_end,
        )

    before = run(steady_outflow)
    assert before.engine_specific["burn_rate_per_hour"] > 0
    assert before.engine_specific["projected_shortage_at"] is not None

    replenished = steady_outflow + [
        txn_factory(
            provider_code="bkash",
            transaction_type="cash_in",
            amount=5000.0,
            occurred_at=window_end - timedelta(minutes=5),
        )
    ]
    after = run(replenished)

    assert after.engine_specific["burn_rate_per_hour"] < before.engine_specific["burn_rate_per_hour"]
    assert after.engine_specific["burn_rate_per_hour"] <= 0
    assert after.engine_specific["projected_shortage_at"] is None


def test_minimum_samples_forces_low_confidence(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    transactions = [
        txn_factory(
            provider_code="bkash",
            transaction_type="cash_out",
            amount=500.0,
            occurred_at=window_start + timedelta(minutes=10),
        )
    ]

    envelope = compute_liquidity_projection(
        transactions,
        fresh_quality(),
        reserve_type=RESERVE_TYPE_PROVIDER_E_MONEY,
        outlet_id="outlet-1",
        provider_code="bkash",
        current_balance=1000.0,
        as_of_at=window_end,
        window_start=window_start,
        window_end=window_end,
        min_sample_count=5,
    )

    assert envelope.engine_specific["is_actionable"] is False
    assert envelope.engine_specific["non_actionable_reason"] == "insufficient_samples"
    assert envelope.engine_specific["projected_shortage_at"] is None
    assert envelope.engine_specific["sample_count"] == 1
    assert envelope.confidence < 0.75
    assert envelope.confidence_level != "high"


def test_happy_path_provider_projection(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    transactions = [
        txn_factory(
            provider_code="bkash",
            transaction_type="cash_out",
            amount=500.0,
            occurred_at=window_start + timedelta(minutes=10 * i),
        )
        for i in range(12)
    ]

    envelope = compute_liquidity_projection(
        transactions,
        fresh_quality(),
        reserve_type=RESERVE_TYPE_PROVIDER_E_MONEY,
        outlet_id="outlet-1",
        provider_code="bkash",
        current_balance=9000.0,
        as_of_at=window_end,
        window_start=window_start,
        window_end=window_end,
        min_sample_count=5,
    )

    assert envelope.engine_specific["is_actionable"] is True
    assert envelope.engine_specific["projected_shortage_at"] is not None
    assert envelope.engine_specific["projected_shortage_at"] > window_end
    assert envelope.confidence_level == "high"


def test_shared_cash_reserve_type_no_provider_columns(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    transactions = [
        txn_factory(
            provider_code="bkash",
            transaction_type="cash_out",
            amount=500.0,
            occurred_at=window_start + timedelta(minutes=10),
        ),
        txn_factory(
            provider_code="nagad",
            transaction_type="cash_out",
            amount=300.0,
            occurred_at=window_start + timedelta(minutes=20),
        ),
    ]

    envelope = compute_liquidity_projection(
        transactions,
        fresh_quality(provider_code=None),
        reserve_type=RESERVE_TYPE_SHARED_CASH,
        outlet_id="outlet-1",
        provider_code=None,
        current_balance=5000.0,
        as_of_at=window_end,
        window_start=window_start,
        window_end=window_end,
    )

    assert envelope.engine_specific["reserve_type"] == RESERVE_TYPE_SHARED_CASH
    assert envelope.engine_specific["provider_code"] is None
    # Shared cash aggregates across providers -- both transactions counted.
    assert envelope.engine_specific["sample_count"] == 2


def test_degraded_quality_widens_bounds_and_lowers_confidence(
    base_time, fresh_quality, degraded_quality, txn_factory
):
    window_start, window_end = _window(base_time)
    amounts = [400.0, 700.0, 500.0, 500.0, 600.0, 500.0]
    transactions = [
        txn_factory(
            provider_code="bkash",
            transaction_type="cash_out",
            amount=amount,
            occurred_at=window_start + timedelta(minutes=20 * i + 5),
        )
        for i, amount in enumerate(amounts)
    ]

    def run(quality):
        return compute_liquidity_projection(
            transactions,
            quality,
            reserve_type=RESERVE_TYPE_PROVIDER_E_MONEY,
            outlet_id="outlet-1",
            provider_code="bkash",
            current_balance=5000.0,
            as_of_at=window_end,
            window_start=window_start,
            window_end=window_end,
            min_sample_count=5,
        )

    fresh_envelope = run(fresh_quality())
    degraded_envelope = run(degraded_quality())

    assert degraded_envelope.confidence < fresh_envelope.confidence

    fresh_width = (
        fresh_envelope.engine_specific["upper_bound_at"] - fresh_envelope.engine_specific["lower_bound_at"]
    )
    degraded_width = (
        degraded_envelope.engine_specific["upper_bound_at"]
        - degraded_envelope.engine_specific["lower_bound_at"]
    )
    assert degraded_width > fresh_width
