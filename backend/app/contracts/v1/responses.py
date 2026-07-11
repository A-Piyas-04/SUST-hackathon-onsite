"""API response contracts — docs/schema.md §17 and §10.6."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import Confidence, ContractModel, MoneyDecimal, ensure_utc, validate_safe_language
from app.contracts.v1.enums import AlertState, AlertType, AppRole, CaseStatus, LocaleCode, ProviderCode, Severity


class ProviderSummary(ContractModel):
    code: ProviderCode
    display_name: str


class OutletSummary(ContractModel):
    outlet_id: UUID
    synthetic_code: str
    area: str


class ProjectionSummary(ContractModel):
    shortage_at: datetime | None = None
    confidence_score: Annotated[Decimal, Field(ge=0, le=1, decimal_places=4, max_digits=6)]
    confidence_level: str

    @field_validator("shortage_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)


class FeedHealthSummary(ContractModel):
    status: str
    confidence_modifier: Annotated[float, Field(ge=0, le=1)]


class SharedCashDashboard(ContractModel):
    balance: MoneyDecimal
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "BDT"
    observed_at: datetime
    projection: ProjectionSummary

    @field_validator("observed_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class ProviderDashboardItem(ContractModel):
    provider: ProviderSummary
    balance: MoneyDecimal
    observed_at: datetime
    feed_health: FeedHealthSummary
    projection: ProjectionSummary

    @field_validator("observed_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class DashboardResponse(ContractModel):
    outlet: OutletSummary
    shared_cash: SharedCashDashboard
    providers: list[ProviderDashboardItem]
    alerts: list[Any] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class AlertExplanation(ContractModel):
    locale: LocaleCode
    situation: str
    evidence: str
    uncertainty: str
    next_step: str


class AlertEvidenceRefs(ContractModel):
    liquidity_projection_ids: list[UUID] = Field(default_factory=list)
    anomaly_flag_ids: list[UUID] = Field(default_factory=list)
    summary: str


class AlertResponse(ContractModel):
    alert_id: UUID
    type: AlertType
    severity: Severity
    provider: ProviderCode | None = None
    outlet_id: UUID
    detected_at: datetime
    confidence: Confidence
    evidence: AlertEvidenceRefs
    plausible_benign_explanation: str | None = None
    recommended_next_step: str
    explanation: AlertExplanation
    case_id: UUID | None = None
    state: AlertState = AlertState.ACTIVE

    @field_validator("detected_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)

    @field_validator("plausible_benign_explanation", "recommended_next_step")
    @classmethod
    def _safe_alert_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_safe_language(value, "alert text")


class CaseResponse(ContractModel):
    case_id: UUID
    case_number: str
    alert_id: UUID
    outlet_id: UUID
    provider_id: UUID | None = None
    status: CaseStatus
    current_owner_user_id: UUID | None = None
    current_owner_role: AppRole
    recommended_next_step: str
    opened_at: datetime
    acknowledged_at: datetime | None = None
    escalated_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_summary: str | None = None
    version: Annotated[int, Field(ge=1)] = 1

    @field_validator("opened_at", "acknowledged_at", "escalated_at", "resolved_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value)

    @field_validator("recommended_next_step", "resolution_summary")
    @classmethod
    def _safe_language(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_safe_language(value, "case text")
