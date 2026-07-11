"""Audit contract + service interface (schema.md 10.12; member-2 plan 7.4).

Owner: Member 2. Pure-stdlib contract + Protocol.

Audit invariants frozen now, implemented in Phase 4:
  * Every workflow mutation writes exactly one audit event in the SAME database
    transaction as the mutation (atomic).
  * Audit rows are strictly append-only; application roles cannot update/delete
    them (enforced via grants/triggers in the security migration).
  * `previous_values`/`new_values` carry a minimal safe diff — never
    credentials, tokens, or another provider's confidential payload.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.coordination.shared.enums import ActorType
from app.coordination.shared.references import CallerScope
from app.coordination.shared.security import scan_structured_variables
from app.coordination.shared.service import NotImplementedServiceError

#: Stable audit action codes (extend as workflow grows).
AUDIT_ACTIONS: frozenset[str] = frozenset(
    {
        "alert.published",
        "alert.state_changed",
        "case.created",
        "case.routed",
        "case.assigned",
        "case.acknowledged",
        "case.escalated",
        "case.note_added",
        "case.reviewed",
        "case.resolved",
        "notification.queued",
        "notification.read",
        "authz.denied",
    }
)


@dataclass(frozen=True)
class AuditEvent:
    action: str
    actor_type: ActorType
    entity_type: str
    entity_id: str
    request_id: str
    occurred_at: str
    actor_user_id: str | None = None
    case_id: str | None = None
    alert_id: str | None = None
    provider_id: str | None = None
    outlet_id: str | None = None
    previous_values: dict[str, Any] = field(default_factory=dict)
    new_values: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Contract self-check reused by tests: known action, safe diffs."""
        if self.action not in AUDIT_ACTIONS:
            raise ValueError(f"unknown audit action: {self.action!r}")
        if scan_structured_variables(self.previous_values) or scan_structured_variables(self.new_values):
            raise ValueError("audit diff contains prohibited language")


class AuditReadService(Protocol):
    def list_case_audit_events(self, caller: CallerScope, case_id: str) -> list[dict[str, Any]]: ...


class ScaffoldAuditReadService:
    def list_case_audit_events(self, caller: CallerScope, case_id: str):
        raise NotImplementedServiceError("audit reads are implemented in Phase 4")
