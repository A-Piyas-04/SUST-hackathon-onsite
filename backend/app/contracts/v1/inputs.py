"""Normalized ingestion input contracts — docs/schema.md §8."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, MoneyDecimal, ensure_utc
from app.contracts.v1.enums import ProviderCode, TransactionStatus, TransactionType


class NormalizedTransactionInput(ContractModel):
    synthetic_transaction_ref: str
    synthetic_party_ref: str
    outlet_id: UUID
    outlet_provider_account_id: UUID
    provider_code: ProviderCode
    transaction_type: TransactionType
    status: TransactionStatus
    amount: MoneyDecimal
    currency_code: Annotated[str, Field(min_length=3, max_length=3)] = "BDT"
    occurred_at: datetime
    received_at: datetime

    @field_validator("occurred_at", "received_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("currency_code")
    @classmethod
    def _bdt_only(cls, value: str) -> str:
        if value != "BDT":
            raise ValueError("MVP supports BDT only.")
        return value


class NormalizedCashBalanceInput(ContractModel):
    outlet_id: UUID
    balance: MoneyDecimal
    currency_code: Annotated[str, Field(min_length=3, max_length=3)] = "BDT"
    observed_at: datetime
    received_at: datetime
    source_kind: Annotated[str, Field(pattern=r"^(feed|derived|seed)$")] = "feed"

    @field_validator("observed_at", "received_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class NormalizedProviderBalanceInput(ContractModel):
    outlet_id: UUID
    outlet_provider_account_id: UUID
    provider_code: ProviderCode
    balance: MoneyDecimal
    currency_code: Annotated[str, Field(min_length=3, max_length=3)] = "BDT"
    observed_at: datetime
    received_at: datetime
    source_kind: Annotated[str, Field(pattern=r"^(feed|derived|seed)$")] = "feed"

    @field_validator("observed_at", "received_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)
