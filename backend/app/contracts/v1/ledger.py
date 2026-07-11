"""Ledger read API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, MoneyDecimal, ensure_utc
from app.contracts.v1.enums import ProviderCode, ReserveType, TransactionStatus, TransactionType
from app.contracts.v1.quality import QualityAssessmentInput


class ProviderRef(ContractModel):
    provider_id: UUID
    code: ProviderCode
    display_name: str


class AreaRef(ContractModel):
    area_id: UUID
    code: str
    name: str


class OutletDetailResponse(ContractModel):
    outlet_id: UUID
    synthetic_code: str
    display_name: str
    area: AreaRef
    providers: list[ProviderRef]


class OutletListItem(ContractModel):
    outlet_id: UUID
    synthetic_code: str
    display_name: str
    area_name: str


class TransactionResponse(ContractModel):
    transaction_id: UUID
    synthetic_transaction_ref: str
    synthetic_party_ref: str
    provider: ProviderCode
    transaction_type: TransactionType
    status: TransactionStatus
    amount: MoneyDecimal
    currency_code: str
    occurred_at: datetime
    received_at: datetime

    @field_validator("occurred_at", "received_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class TransactionListResponse(ContractModel):
    outlet_id: UUID
    transactions: list[TransactionResponse]
    total: int


class BalanceHistoryItem(ContractModel):
    snapshot_id: UUID
    reserve_type: ReserveType
    outlet_id: UUID
    provider: ProviderCode | None = None
    balance: MoneyDecimal
    currency_code: str
    observed_at: datetime
    received_at: datetime
    source_kind: str
    is_conflicted: bool = False

    @field_validator("observed_at", "received_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class BalanceHistoryResponse(ContractModel):
    outlet_id: UUID
    reserve_type: ReserveType
    provider: ProviderCode | None = None
    items: list[BalanceHistoryItem]


class DataQualityItem(ContractModel):
    provider: ProviderCode
    assessment: QualityAssessmentInput
    phase: Annotated[str, Field(pattern=r"^foundation$")] = "foundation"


class DataQualityResponse(ContractModel):
    outlet_id: UUID
    phase: Annotated[str, Field(pattern=r"^foundation$")] = "foundation"
    note: str = "Pre-Phase-4 interim estimates derived from ingestion metadata."
    providers: list[DataQualityItem]


class DataQualityHistoryResponse(ContractModel):
    outlet_id: UUID
    phase: Annotated[str, Field(pattern=r"^foundation$")] = "foundation"
    assessments: list[DataQualityItem]
