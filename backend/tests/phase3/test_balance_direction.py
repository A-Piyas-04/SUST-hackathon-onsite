"""Regression tests for physical-cash/provider-e-money transaction direction."""

from decimal import Decimal

from app.contracts.v1.enums import ProviderCode, ScenarioCode, TransactionType
from app.services.synthetic.generator import (
    _apply_transaction_effect,
    generate_dataset,
)


def test_cash_out_decreases_cash_and_increases_provider_e_money():
    cash_after, provider_after = _apply_transaction_effect(
        cash_balance=Decimal("10000.00"),
        provider_balance=Decimal("5000.00"),
        transaction_type=TransactionType.CASH_OUT,
        amount=Decimal("1000.00"),
    )

    assert cash_after == Decimal("9000.00")
    assert provider_after == Decimal("6000.00")


def test_cash_in_increases_cash_and_decreases_provider_e_money():
    cash_after, provider_after = _apply_transaction_effect(
        cash_balance=Decimal("10000.00"),
        provider_balance=Decimal("5000.00"),
        transaction_type=TransactionType.CASH_IN,
        amount=Decimal("1000.00"),
    )

    assert cash_after == Decimal("11000.00")
    assert provider_after == Decimal("4000.00")


def test_scenario_a_cash_out_pressure_depletes_shared_cash():
    result = generate_dataset(
        scenario_code=ScenarioCode.SCENARIO_A,
        seed=2001,
        config={
            "target_provider": "bkash",
            "transaction_count": 12,
            "initial_cash": "85000.00",
            "initial_bkash": "42000.00",
        },
    )

    cash_snapshots = [
        event
        for batch in result.batches
        for event in batch.events
        if event.event_type.value == "cash_balance"
    ]
    bkash_snapshots = [
        event
        for batch in result.batches
        for event in batch.events
        if event.event_type.value == "provider_balance"
        and event.provider_code == ProviderCode.BKASH
    ]

    opening_cash = Decimal(cash_snapshots[0].payload["balance"])
    closing_cash = Decimal(cash_snapshots[-1].payload["balance"])
    opening_bkash = Decimal(bkash_snapshots[0].payload["balance"])
    closing_bkash = Decimal(bkash_snapshots[-1].payload["balance"])

    assert closing_cash < opening_cash
    assert closing_bkash > opening_bkash


def test_scenario_c_keeps_a_recent_trusted_provider_balance_before_the_conflict():
    result = generate_dataset(
        scenario_code=ScenarioCode.SCENARIO_C,
        seed=2003,
        config={"cluster_provider": "bkash", "cluster_count": 6},
    )

    bkash_snapshots = [
        event
        for batch in result.batches
        for event in batch.events
        if event.event_type.value == "provider_balance"
        and event.provider_code == ProviderCode.BKASH
    ]

    opening = Decimal(bkash_snapshots[0].payload["balance"])
    transaction_snapshots = [event for event in bkash_snapshots if "-TXN-" in event.source_event_ref]
    assert transaction_snapshots
    assert Decimal(transaction_snapshots[-1].payload["balance"]) > opening
