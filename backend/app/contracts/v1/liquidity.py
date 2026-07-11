"""Liquidity projection contracts — docs/schema.md §9.4, §9.6."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, MoneyDecimal, ensure_utc
from app.contracts.v1.enums import ConfidenceLevel, ReserveType


class LiquiditySignal(ContractModel):
    signal_code: str
    label: str
    numeric_value: Decimal | float | None = None
    unit: str | None = None
    direction: str | None = None
    details: dict[str, Any] | None = None
    display_order: Annotated[int, Field(ge=0)] = 0


class LiquidityProjectionOutput(ContractModel):
    liquidity_projection_id: UUID | None = None
    analytics_run_id: UUID | None = None
    outlet_id: UUID
    reserve_type: ReserveType
    outlet_provider_account_id: UUID | None = None
    provider_id: UUID | None = None
    as_of_at: datetime
    current_balance: MoneyDecimal
    burn_rate_per_hour: Decimal
    projected_shortage_at: datetime | None = None
    lower_bound_at: datetime | None = None
    upper_bound_at: datetime | None = None
    confidence_score: Annotated[Decimal, Field(ge=0, le=1, decimal_places=4, max_digits=6)]
    confidence_level: ConfidenceLevel
    sample_count: Annotated[int, Field(ge=0)]
    is_actionable: bool
    non_actionable_reason: str | None = None
    signals: list[LiquiditySignal] = Field(default_factory=list)

    @field_validator("as_of_at", "projected_shortage_at", "lower_bound_at", "upper_bound_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)
