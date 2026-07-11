"""Phase 5 coordination contracts: auth, alerts, cases, notifications, audit.

Explicit enums, ISO timezone-aware timestamps, structured evidence/explanation
payloads, explicit actor/scope identity in audit events, and a concurrency
``version`` field on mutable case records (see docs/schema.md §10, §16).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from app.contracts.v1.common import ContractModel, ensure_utc, validate_safe_language
from app.contracts.v1.enums import (
    AlertState,
    AlertType,
    AppRole,
    AssignmentReason,
    CaseNoteType,
    CaseStatus,
    LocaleCode,
    NotificationChannel,
    NotificationStatus,
    ReviewOutcome,
    Severity,
)


# --------------------------------------------------------------------------- #
# Auth / principal
# --------------------------------------------------------------------------- #
class ScopeOut(ContractModel):
    role: AppRole
    provider_id: UUID | None = None
    area_id: UUID | None = None
    outlet_id: UUID | None = None


class PrincipalResponse(ContractModel):
    user_id: UUID
    display_name: str
    preferred_locale: LocaleCode
    roles: list[AppRole] = Field(default_factory=list)
    scopes: list[ScopeOut] = Field(default_factory=list)


class DemoLoginRequest(ContractModel):
    """Select a seeded demo identity by friendly key or by role.

    ``user_key`` (e.g. ``agent``, ``bkash_ops``, ``risk_analyst``) wins when set;
    otherwise ``role`` (+ optional ``provider`` to disambiguate provider ops).
    """

    user_key: str | None = None
    role: AppRole | None = None
    provider: str | None = None


class DemoLoginResponse(ContractModel):
    token: str
    token_type: str = "bearer"
    user: PrincipalResponse


class PreferencesUpdate(ContractModel):
    preferred_locale: LocaleCode


# --------------------------------------------------------------------------- #
# Alerts
# --------------------------------------------------------------------------- #
class AlertOutput(ContractModel):
    alert_id: UUID
    simulation_run_id: UUID
    outlet_id: UUID
    provider_id: UUID | None = None
    alert_type: AlertType
    severity: Severity
    state: AlertState
    deduplication_key: str
    title_key: str
    requires_case: bool
    detected_at: datetime
    created_at: datetime
    structured_payload: dict[str, Any] = Field(default_factory=dict)
    source_links: dict[str, Any] = Field(default_factory=dict)
    has_case: bool = False
    case_id: UUID | None = None

    @field_validator("detected_at", "created_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class AlertListResponse(ContractModel):
    alerts: list[AlertOutput] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class AlertExplanationOutput(ContractModel):
    alert_explanation_id: UUID
    alert_id: UUID
    locale: LocaleCode
    situation_text: str
    evidence_text: str
    uncertainty_text: str
    next_step_text: str
    benign_context_text: str | None = None
    rendered_at: datetime

    @field_validator("rendered_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class AlertExplanationsResponse(ContractModel):
    alert_id: UUID
    explanations: list[AlertExplanationOutput] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class PublishRequest(ContractModel):
    simulation_run_id: UUID
    outlet_id: UUID | None = None


class PublishResponse(ContractModel):
    published: list[AlertOutput] = Field(default_factory=list)
    deduplicated_alert_ids: list[UUID] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


# --------------------------------------------------------------------------- #
# Cases
# --------------------------------------------------------------------------- #
class CaseOutput(ContractModel):
    case_id: UUID
    case_number: str
    alert_id: UUID
    outlet_id: UUID
    provider_id: UUID | None = None
    routing_rule_id: UUID | None = None
    status: CaseStatus
    current_owner_user_id: UUID | None = None
    current_owner_role: AppRole
    recommended_next_step: str
    opened_at: datetime
    acknowledged_at: datetime | None = None
    escalated_at: datetime | None = None
    resolved_at: datetime | None = None
    resolution_summary: str | None = None
    version: int
    updated_at: datetime

    @field_validator("opened_at", "updated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class CaseListResponse(ContractModel):
    cases: list[CaseOutput] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


class OpenCaseRequest(ContractModel):
    idempotency_key: str | None = None


class _Mutation(ContractModel):
    """Common optimistic-concurrency + idempotency envelope for case mutations."""

    expected_version: int | None = None
    idempotency_key: str | None = None
    reason: str | None = None

    @field_validator("reason", mode="before")
    @classmethod
    def _safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_safe_language(value, "reason")


class AssignmentRequest(_Mutation):
    assigned_to_role: AppRole
    assigned_to_user_id: UUID | None = None
    assignment_reason: AssignmentReason = AssignmentReason.MANUAL_ASSIGN


class AcknowledgeRequest(_Mutation):
    pass


class EscalateRequest(_Mutation):
    target_role: AppRole | None = None


class ResolveRequest(_Mutation):
    resolution_summary: str

    @field_validator("resolution_summary", mode="before")
    @classmethod
    def _safe_summary(cls, value: str) -> str:
        return validate_safe_language(value, "resolution_summary")


class NoteRequest(ContractModel):
    note_text: str
    note_type: CaseNoteType = CaseNoteType.GENERAL
    idempotency_key: str | None = None

    @field_validator("note_text", mode="before")
    @classmethod
    def _safe_note(cls, value: str) -> str:
        return validate_safe_language(value, "note_text")


class ReviewRequest(ContractModel):
    disposition: ReviewOutcome
    review_summary: str
    was_false_positive: bool | None = None
    idempotency_key: str | None = None

    @field_validator("review_summary", mode="before")
    @classmethod
    def _safe_review(cls, value: str) -> str:
        return validate_safe_language(value, "review_summary")


class NoteOutput(ContractModel):
    case_note_id: UUID
    case_id: UUID
    author_user_id: UUID
    note_text: str
    note_type: CaseNoteType
    created_at: datetime


class ReviewOutput(ContractModel):
    case_review_id: UUID
    case_id: UUID
    reviewed_by_user_id: UUID
    disposition: ReviewOutcome
    was_false_positive: bool | None = None
    review_summary: str
    reviewed_at: datetime


# --------------------------------------------------------------------------- #
# Timeline
# --------------------------------------------------------------------------- #
class TimelineEvent(ContractModel):
    event_at: datetime
    event_type: str
    event_id: UUID
    actor_user_id: UUID | None = None
    detail: dict[str, Any] = Field(default_factory=dict)


class CaseTimelineResponse(ContractModel):
    case_id: UUID
    events: list[TimelineEvent] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


# --------------------------------------------------------------------------- #
# Notifications
# --------------------------------------------------------------------------- #
class NotificationOutput(ContractModel):
    notification_id: UUID
    case_id: UUID
    recipient_user_id: UUID | None = None
    recipient_role: AppRole
    channel: NotificationChannel
    status: NotificationStatus
    payload: dict[str, Any] = Field(default_factory=dict)
    queued_at: datetime
    delivered_at: datetime | None = None
    read_at: datetime | None = None


class NotificationListResponse(ContractModel):
    notifications: list[NotificationOutput] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)


# --------------------------------------------------------------------------- #
# Audit
# --------------------------------------------------------------------------- #
class AuditEventOutput(ContractModel):
    audit_event_id: UUID
    case_id: UUID | None = None
    alert_id: UUID | None = None
    provider_id: UUID | None = None
    outlet_id: UUID | None = None
    actor_user_id: UUID | None = None
    actor_type: str
    action: str
    entity_type: str | None = None
    entity_id: UUID | None = None
    previous_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    request_id: str | None = None
    occurred_at: datetime


class AuditEventsResponse(ContractModel):
    case_id: UUID
    events: list[AuditEventOutput] = Field(default_factory=list)
    generated_at: datetime

    @field_validator("generated_at")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        return ensure_utc(value)
