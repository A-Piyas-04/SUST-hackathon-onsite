"""Unit tests for the in-app notification queue (docs/schema.md §10.10).

The service touches the DB only through session.execute(), so stub sessions
exercise recipient/role visibility filtering and read-state transitions without
a database. Provider-boundary checks (can_access_scope) are monkeypatched.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.contracts.v1.enums import AppRole
from app.core.auth import AccessScope, UserContext
from app.core.authz import SafeNotFoundError
from app.services.coordination import notifications as notif_mod

CASE_ID = uuid4()
OUTLET_ID = uuid4()
PROVIDER_ID = uuid4()
NOW = datetime(2026, 7, 11, 10, 0, tzinfo=timezone.utc)

OPS_USER = UserContext(
    user_id=uuid4(),
    display_name="Ops",
    preferred_locale="en",
    scopes=(AccessScope(role=AppRole.PROVIDER_OPS, provider_id=PROVIDER_ID),),
)


def _row(**overrides):
    row = {
        "notification_id": uuid4(),
        "case_id": CASE_ID,
        "recipient_user_id": None,
        "recipient_role": "provider_ops",
        "channel": "in_app",
        "status": "queued",
        "payload": {"kind": "case_opened"},
        "queued_at": NOW,
        "delivered_at": None,
        "read_at": None,
        "case_outlet_id": OUTLET_ID,
        "case_provider_id": PROVIDER_ID,
    }
    row.update(overrides)
    return row


class _StubResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None

    def one(self):
        assert len(self._rows) == 1
        return self._rows[0]


class _StubSession:
    """Routes execute() by SQL shape; records INSERT/UPDATE params."""

    def __init__(self, rows=(), updated_row=None):
        self.rows = list(rows)
        self.updated_row = updated_row
        self.writes: list[tuple[str, dict]] = []

    async def execute(self, statement, params=None):
        sql = str(statement)
        if sql.strip().startswith("INSERT") or sql.strip().startswith("UPDATE"):
            self.writes.append((sql.split()[0], params))
            return _StubResult([])
        if "SELECT * FROM notifications" in sql:
            return _StubResult([self.updated_row])
        return _StubResult(self.rows)


@pytest.fixture(autouse=True)
def _allow_scope(monkeypatch):
    """Default: provider-boundary check passes; tests override to deny."""

    async def _yes(session, user, *, outlet_id, provider_id):
        return True

    monkeypatch.setattr(notif_mod, "can_access_scope", _yes)


# ---------------------------------------------------------- queue_notification
async def test_queue_notification_persists_payload_and_returns_id():
    session = _StubSession()
    nid = await notif_mod.queue_notification(
        session,
        case_id=CASE_ID,
        recipient_role="provider_ops",
        recipient_user_id=None,
        payload={"kind": "case_opened"},
    )
    verb, params = session.writes[0]
    assert verb == "INSERT"
    assert params["id"] == nid
    assert params["recipient_role"] == "provider_ops"
    assert params["payload"] == '{"kind": "case_opened"}'


# ---------------------------------------------------------- list_notifications
async def test_direct_recipient_sees_notification_regardless_of_role():
    direct = _row(recipient_user_id=OPS_USER.user_id, recipient_role="management")
    session = _StubSession(rows=[direct])
    out = await notif_mod.list_notifications(session, OPS_USER)
    assert [n.notification_id for n in out.notifications] == [direct["notification_id"]]


async def test_role_routed_notification_requires_matching_role():
    other_role = _row(recipient_role="management")
    session = _StubSession(rows=[other_role])
    out = await notif_mod.list_notifications(session, OPS_USER)
    assert out.notifications == []


async def test_role_routed_notification_requires_provider_scope(monkeypatch):
    async def _no(session, user, *, outlet_id, provider_id):
        return False

    monkeypatch.setattr(notif_mod, "can_access_scope", _no)
    session = _StubSession(rows=[_row()])
    out = await notif_mod.list_notifications(session, OPS_USER)
    assert out.notifications == []


async def test_role_and_scope_match_included_with_defaulted_payload():
    session = _StubSession(rows=[_row(payload=None)])
    out = await notif_mod.list_notifications(session, OPS_USER)
    assert len(out.notifications) == 1
    assert out.notifications[0].payload == {}


# ------------------------------------------------------------------- mark_read
async def test_mark_read_unknown_notification_raises_uniform_404():
    session = _StubSession(rows=[])
    with pytest.raises(SafeNotFoundError):
        await notif_mod.mark_read(session, OPS_USER, uuid4())


async def test_mark_read_forbidden_recipient_raises_uniform_404(monkeypatch):
    async def _no(session, user, *, outlet_id, provider_id):
        return False

    monkeypatch.setattr(notif_mod, "can_access_scope", _no)
    session = _StubSession(rows=[_row(recipient_role="management")])
    with pytest.raises(SafeNotFoundError):
        await notif_mod.mark_read(session, OPS_USER, uuid4())
    assert session.writes == []  # denied before any UPDATE


async def test_mark_read_updates_state_and_returns_read_row():
    target = _row()
    read_row = _row(
        notification_id=target["notification_id"],
        status="read",
        delivered_at=NOW,
        read_at=NOW,
    )
    session = _StubSession(rows=[target], updated_row=read_row)
    out = await notif_mod.mark_read(session, OPS_USER, target["notification_id"])
    assert out.status.value == "read"
    assert out.read_at == NOW
    verb, params = session.writes[0]
    assert verb == "UPDATE"
    assert params["id"] == target["notification_id"]
