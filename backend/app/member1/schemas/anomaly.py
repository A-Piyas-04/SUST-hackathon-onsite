from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.member1.schemas.common import ApiModel


class AnomalyFlagOut(ApiModel):
    anomaly_flag_id: UUID
    analytics_run_id: UUID
    anomaly_rule_id: UUID
    outlet_id: UUID
    provider_id: UUID
    outlet_provider_account_id: UUID
    window_start: datetime
    window_end: datetime
    confidence_score: float
    confidence_level: str
    disposition: str
    reason_code: str | None = None
    evidence_summary: str
    plausible_benign_explanation: str | None = None
    suppression_reason: str | None = None


class AnomalyEvidenceItemOut(ApiModel):
    evidence_type: str
    label: str
    value: dict[str, Any]
    display_order: int


class AnomalyFlagDetailOut(AnomalyFlagOut):
    evidence_items: list[AnomalyEvidenceItemOut] = Field(default_factory=list)
    transaction_ids: list[UUID] = Field(default_factory=list)
