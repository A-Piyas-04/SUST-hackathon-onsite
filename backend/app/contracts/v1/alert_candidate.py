"""AlertCandidate seam contract — pre-alert, no case workflow fields."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, EvidenceItem, validate_safe_language
from app.contracts.v1.enums import AlertType, ConfidenceLevel, Severity


class AlertSourceLinks(ContractModel):
    analytics_run_id: UUID | None = None
    liquidity_projection_id: UUID | None = None
    anomaly_flag_id: UUID | None = None
    quality_assessment_ids: tuple[UUID, ...] = ()


class AlertCandidate(ContractModel):
    outlet_id: UUID
    provider_id: UUID | None = None
    alert_type: AlertType
    severity: Severity
    confidence: Annotated[Decimal, Field(ge=0, le=1, decimal_places=4, max_digits=6)]
    confidence_level: ConfidenceLevel
    detected_at: datetime
    deduplication_key: str
    requires_case: bool
    is_alertable: bool
    evidence_summary: str
    recommended_next_step: str
    plausible_benign_explanation: str | None = None
    source_links: AlertSourceLinks
    structured_evidence: tuple[EvidenceItem, ...] = ()
    title_key: str

    @field_validator(
        "evidence_summary",
        "recommended_next_step",
        "plausible_benign_explanation",
        mode="before",
    )
    @classmethod
    def _safe_language(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_safe_language(value, "alert candidate text")
