"""Case-transition state-machine tests: every legal transition, every illegal
transition, required data, and version/If-Match concurrency policy."""
from __future__ import annotations

import pytest

from app.coordination.cases.state_machine import (
    NONE_STATE,
    TransitionAction,
    all_transitions,
    evaluate_transition,
    is_legal,
    legal_actions,
)
from app.coordination.shared.enums import CaseStatus

LEGAL = [
    (NONE_STATE, TransitionAction.OPEN, CaseStatus.OPEN),
    (CaseStatus.OPEN, TransitionAction.ACKNOWLEDGE, CaseStatus.ACKNOWLEDGED),
    (CaseStatus.OPEN, TransitionAction.ESCALATE, CaseStatus.ESCALATED),
    (CaseStatus.ACKNOWLEDGED, TransitionAction.ESCALATE, CaseStatus.ESCALATED),
    (CaseStatus.ACKNOWLEDGED, TransitionAction.RESOLVE, CaseStatus.RESOLVED),
    (CaseStatus.ESCALATED, TransitionAction.RESOLVE, CaseStatus.RESOLVED),
]

# Complete payloads so legality (not missing-data) is what is under test.
_FULL_PAYLOAD = {
    "alert_id": "alert_001", "recipient_role": "provider_ops", "current_owner_role": "provider_ops",
    "recommended_next_step": "Review.", "expected_version": 1, "target_role": "risk_analyst",
    "reason": "needs review", "resolution_summary": "done",
}


@pytest.mark.parametrize("frm,action,to", LEGAL)
def test_legal_transitions(frm, action, to):
    result = evaluate_transition(str(frm), action, _FULL_PAYLOAD)
    assert result.ok
    assert result.to_status == to


ILLEGAL = [
    (CaseStatus.OPEN, TransitionAction.RESOLVE),           # open -> resolved is INVALID in MVP
    (CaseStatus.RESOLVED, TransitionAction.ACKNOWLEDGE),   # no reopening
    (CaseStatus.RESOLVED, TransitionAction.ESCALATE),      # no reopening
    (CaseStatus.RESOLVED, TransitionAction.RESOLVE),       # self / reopen
    (CaseStatus.ESCALATED, TransitionAction.ACKNOWLEDGE),  # backwards
    (CaseStatus.ACKNOWLEDGED, TransitionAction.ACKNOWLEDGE),  # self
]


@pytest.mark.parametrize("frm,action", ILLEGAL)
def test_illegal_transitions_rejected(frm, action):
    result = evaluate_transition(str(frm), action, _FULL_PAYLOAD)
    assert not result.ok
    assert result.error_code == "ILLEGAL_TRANSITION"
    assert not is_legal(str(frm), action)


def test_open_to_resolved_is_invalid_per_frozen_matrix():
    assert not is_legal(str(CaseStatus.OPEN), TransitionAction.RESOLVE)


def test_escalate_requires_reason_and_target():
    result = evaluate_transition(str(CaseStatus.OPEN), TransitionAction.ESCALATE, {"expected_version": 1})
    assert not result.ok
    assert result.error_code == "MISSING_TRANSITION_DATA"
    assert "target_role" in result.missing_data and "reason" in result.missing_data


def test_resolve_requires_summary():
    result = evaluate_transition(str(CaseStatus.ACKNOWLEDGED), TransitionAction.RESOLVE, {"expected_version": 1})
    assert not result.ok
    assert "resolution_summary" in result.missing_data


def test_transition_requires_expected_version():
    result = evaluate_transition(str(CaseStatus.OPEN), TransitionAction.ACKNOWLEDGE, {})
    assert not result.ok
    assert "expected_version" in result.missing_data


def test_creation_requires_alert_owner_and_next_step():
    result = evaluate_transition(NONE_STATE, TransitionAction.OPEN, {})
    assert not result.ok
    for key in ("alert_id", "recipient_role", "current_owner_role", "recommended_next_step"):
        assert key in result.missing_data


def test_legal_actions_listing():
    assert set(legal_actions(str(CaseStatus.OPEN))) == {"acknowledge", "escalate"}
    assert legal_actions(str(CaseStatus.RESOLVED)) == ()


def test_transition_table_frozen_size():
    assert len(all_transitions()) == 6


# --- concurrency / version policy -----------------------------------------

def test_version_conflict_rejects_stale_write():
    from app.coordination.shared.concurrency import check_version
    from app.coordination.shared.errors import ApiError, ErrorCode

    with pytest.raises(ApiError) as exc:
        check_version(current_version=5, expected_version=4)
    assert exc.value.code == ErrorCode.VERSION_CONFLICT
    assert exc.value.http_status == 409


def test_version_match_passes():
    from app.coordination.shared.concurrency import check_version

    check_version(current_version=5, expected_version=5)  # no raise


def test_if_match_and_body_must_agree():
    from app.coordination.shared.concurrency import resolve_expected_version
    from app.coordination.shared.errors import ApiError

    assert resolve_expected_version(body_version=3, if_match='"3"').expected_version == 3
    with pytest.raises(ApiError):
        resolve_expected_version(body_version=3, if_match='"4"')


def test_version_required_when_absent():
    from app.coordination.shared.concurrency import resolve_expected_version
    from app.coordination.shared.errors import ApiError, ErrorCode

    with pytest.raises(ApiError) as exc:
        resolve_expected_version(body_version=None, if_match=None)
    assert exc.value.code == ErrorCode.VERSION_REQUIRED
