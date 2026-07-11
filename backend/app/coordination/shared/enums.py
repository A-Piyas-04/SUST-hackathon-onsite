"""Coordination-only enumerations owned by Member 2.

Owner: Member 2. These mirror docs/schema.md Section 4 for the coordination /
security surface and back both the Python contracts and the future database
`text + CHECK (... IN (...))` columns in Member 2's migration files.

Shared analytical enums (`AlertType`, `Severity`, `ConfidenceLevel`,
`ReserveType`, `AnomalyDisposition`) are Member 1-owned and re-used from
`app.shared.enums` rather than duplicated here — see the re-exports at the
bottom of this module.

`fraud`, `fraudster`, `blocked`, `frozen`, `confirmed_fraud`, and every other
definitive-verdict or financial-action value is intentionally absent from every
enum below. Member 2 records advisory workflow state only.
"""
from __future__ import annotations

from enum import StrEnum

# Re-use, do not duplicate, the analytical enums Member 1 already froze.
from app.shared.enums import (  # noqa: F401  (re-exported on purpose)
    AlertType,
    AnomalyDisposition,
    ConfidenceLevel,
    ReserveType,
    Severity,
)


class AppRole(StrEnum):
    """schema.md Section 4 `app_role`. No role is a cross-provider wildcard."""

    AGENT = "agent"
    FIELD_OFFICER = "field_officer"
    AREA_MANAGER = "area_manager"
    PROVIDER_OPS = "provider_ops"
    RISK_ANALYST = "risk_analyst"
    MANAGEMENT = "management"
    ADMIN = "admin"


class AlertState(StrEnum):
    """schema.md Section 4 `alert_state`. Only lifecycle metadata is mutable."""

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CLOSED = "closed"


class CaseStatus(StrEnum):
    """schema.md Section 4 `case_status`. Reopening is out of MVP scope."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class AssignmentReason(StrEnum):
    """schema.md Section 4 `assignment_reason`."""

    INITIAL_ROUTE = "initial_route"
    MANUAL_ASSIGN = "manual_assign"
    REASSIGN = "reassign"
    ESCALATION = "escalation"


class NotificationChannel(StrEnum):
    """schema.md Section 4 `notification_channel`. MVP uses `in_app` only."""

    IN_APP = "in_app"
    WEBHOOK = "webhook"
    EMAIL_STUB = "email_stub"


class NotificationStatus(StrEnum):
    """schema.md Section 4 `notification_status`."""

    QUEUED = "queued"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class LocaleCode(StrEnum):
    """schema.md Section 4 `locale_code`. `en` is the required fallback."""

    EN = "en"
    BN = "bn"
    BN_LATN = "bn_latn"


class ReviewOutcome(StrEnum):
    """schema.md Section 4 `review_outcome`. Never a fraud verdict.

    Note: schema.md uses `benign_operational` / `requires_follow_up`; the
    problem statement phrases these as benign / operational-follow-up. Values
    below follow schema.md verbatim so the DB CHECK constraint matches.
    """

    BENIGN_OPERATIONAL = "benign_operational"
    REQUIRES_FOLLOW_UP = "requires_follow_up"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    CONFIRMED_UNUSUAL = "confirmed_unusual"
    INCONCLUSIVE = "inconclusive"


class NoteType(StrEnum):
    """schema.md Section 10.9 `case_notes.note_type` (constrained text)."""

    GENERAL = "general"
    CONTACT_ATTEMPT = "contact_attempt"
    EVIDENCE = "evidence"
    RESOLUTION = "resolution"


class ActorType(StrEnum):
    """schema.md Section 10.12 `audit_events.actor_type`."""

    USER = "user"
    ROUTING_ENGINE = "routing_engine"
    ANALYTICS_ENGINE = "analytics_engine"
    SYSTEM = "system"


# --- Candidate-consumer support -------------------------------------------

#: The only AlertCandidate contract version Member 2 accepts in Phase 1.
SUPPORTED_CANDIDATE_VERSIONS: frozenset[str] = frozenset({"1", "v1", "1.0"})

#: Canonical severities that count as "high-impact" and therefore require the
#: full explanation coverage set (EN situation/evidence/uncertainty/next-step).
HIGH_IMPACT_SEVERITIES: frozenset[str] = frozenset(
    {Severity.HIGH.value, Severity.CRITICAL.value}
)
