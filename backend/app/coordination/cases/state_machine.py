"""Pure case-transition state machine (member-2 plan Section 7.2; schema.md 10.6).

Owner: Member 2. Pure-stdlib, no persistence — this primitive is reused by the
case service in Phase 4 and is fully unit-tested now.

Legal transitions (and ONLY these):

    none          -> open           (creation; alert + routing + owner + next step)
    open          -> acknowledged   (authorized actor, expected version)
    open          -> escalated      (target role/user, reason, expected version)
    acknowledged  -> escalated      (target role/user, reason, expected version)
    acknowledged  -> resolved       (resolution summary, expected version)
    escalated     -> resolved       (resolution summary, expected version)

Everything else is rejected — including `open -> resolved`, any `resolved -> *`
(no reopening), and self-transitions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.coordination.shared.enums import CaseStatus

# Sentinel for "no case yet" (the source state of creation).
NONE_STATE = "none"


class TransitionAction(StrEnum):
    """The action verbs that drive transitions. `open` is creation."""

    OPEN = "open"
    ACKNOWLEDGE = "acknowledge"
    ESCALATE = "escalate"
    RESOLVE = "resolve"


@dataclass(frozen=True)
class TransitionSpec:
    from_status: str
    action: TransitionAction
    to_status: CaseStatus
    #: Field names that MUST be present in the transition payload.
    required_data: tuple[str, ...] = field(default_factory=tuple)


# The frozen transition table. Creation requires the routing/owner data; every
# post-creation transition requires the expected version; escalation needs a
# target + reason; resolution needs a summary.
_TRANSITIONS: tuple[TransitionSpec, ...] = (
    TransitionSpec(
        NONE_STATE,
        TransitionAction.OPEN,
        CaseStatus.OPEN,
        required_data=("alert_id", "recipient_role", "current_owner_role", "recommended_next_step"),
    ),
    TransitionSpec(
        CaseStatus.OPEN,
        TransitionAction.ACKNOWLEDGE,
        CaseStatus.ACKNOWLEDGED,
        required_data=("expected_version",),
    ),
    TransitionSpec(
        CaseStatus.OPEN,
        TransitionAction.ESCALATE,
        CaseStatus.ESCALATED,
        required_data=("target_role", "reason", "expected_version"),
    ),
    TransitionSpec(
        CaseStatus.ACKNOWLEDGED,
        TransitionAction.ESCALATE,
        CaseStatus.ESCALATED,
        required_data=("target_role", "reason", "expected_version"),
    ),
    TransitionSpec(
        CaseStatus.ACKNOWLEDGED,
        TransitionAction.RESOLVE,
        CaseStatus.RESOLVED,
        required_data=("resolution_summary", "expected_version"),
    ),
    TransitionSpec(
        CaseStatus.ESCALATED,
        TransitionAction.RESOLVE,
        CaseStatus.RESOLVED,
        required_data=("resolution_summary", "expected_version"),
    ),
)

_BY_KEY: dict[tuple[str, str], TransitionSpec] = {
    (t.from_status, str(t.action)): t for t in _TRANSITIONS
}


@dataclass(frozen=True)
class TransitionResult:
    ok: bool
    to_status: CaseStatus | None = None
    missing_data: tuple[str, ...] = field(default_factory=tuple)
    error_code: str | None = None  # "ILLEGAL_TRANSITION" | "MISSING_TRANSITION_DATA"


def is_legal(from_status: str, action: TransitionAction | str) -> bool:
    return (from_status, str(action)) in _BY_KEY


def spec_for(from_status: str, action: TransitionAction | str) -> TransitionSpec | None:
    return _BY_KEY.get((from_status, str(action)))


def legal_actions(from_status: str) -> tuple[str, ...]:
    return tuple(
        str(t.action) for t in _TRANSITIONS if t.from_status == from_status
    )


def evaluate_transition(
    from_status: str,
    action: TransitionAction | str,
    payload: dict | None = None,
) -> TransitionResult:
    """Pure decision: is this transition legal, and is its required data present?

    Does NOT check authorization/version-staleness/scope — those are separate
    concerns handled by the scope policy and concurrency policy. This answers
    only "is this a legal state change with the mandatory fields supplied".
    """
    payload = payload or {}
    spec = _BY_KEY.get((from_status, str(action)))
    if spec is None:
        return TransitionResult(ok=False, error_code="ILLEGAL_TRANSITION")
    missing = tuple(
        key
        for key in spec.required_data
        if payload.get(key) in (None, "", [])
    )
    if missing:
        return TransitionResult(
            ok=False,
            to_status=spec.to_status,
            missing_data=missing,
            error_code="MISSING_TRANSITION_DATA",
        )
    return TransitionResult(ok=True, to_status=spec.to_status)


def all_transitions() -> tuple[TransitionSpec, ...]:
    """Expose the frozen table (e.g. for docs generation and exhaustive tests)."""
    return _TRANSITIONS
