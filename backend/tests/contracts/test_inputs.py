import pytest
from pydantic import ValidationError

from app.contracts.v1.inputs import (
    NormalizedCashBalanceInput,
    NormalizedProviderBalanceInput,
    NormalizedTransactionInput,
)
from tests.contracts.conftest import load_fixture


def test_normalized_transaction_positive():
    NormalizedTransactionInput.model_validate(load_fixture("normalized_transaction.json"))


def test_normalized_cash_balance_positive():
    NormalizedCashBalanceInput.model_validate(load_fixture("normalized_cash_balance.json"))


def test_normalized_provider_balance_positive():
    NormalizedProviderBalanceInput.model_validate(
        load_fixture("normalized_provider_balance.json")
    )


def test_normalized_transaction_missing_required_field():
    with pytest.raises(ValidationError):
        NormalizedTransactionInput.model_validate(
            load_fixture("normalized_transaction_missing_ref.json", positive=False)
        )


def test_normalized_transaction_bad_decimal():
    with pytest.raises(ValidationError):
        NormalizedTransactionInput.model_validate(
            load_fixture("normalized_transaction_bad_decimal.json", positive=False)
        )


def test_normalized_cash_balance_rejects_naive_timestamp():
    with pytest.raises(ValidationError):
        NormalizedCashBalanceInput.model_validate(
            load_fixture("normalized_cash_balance_naive_ts.json", positive=False)
        )
