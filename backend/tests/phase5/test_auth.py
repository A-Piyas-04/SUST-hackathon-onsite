"""Auth and principal-context tests (Phase 5 step 1)."""

from __future__ import annotations

from app.core.auth import AGENT1, BKASH
from tests.phase5.conftest import token


def test_demo_login_by_role_returns_scoped_principal(client):
    resp = client.post("/api/v1/auth/demo-login", json={"role": "provider_ops", "provider": "bkash"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token"].startswith("demo:")
    assert body["user"]["roles"] == ["provider_ops"]
    assert body["user"]["scopes"][0]["provider_id"] == str(BKASH)


def test_demo_login_by_user_key(client):
    resp = client.post("/api/v1/auth/demo-login", json={"user_key": "agent"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["user_id"] == str(AGENT1)


def test_me_requires_authentication(client):
    assert client.get("/api/v1/me").status_code == 401


def test_me_returns_current_principal(client):
    resp = client.get("/api/v1/me", headers=token(AGENT1))
    assert resp.status_code == 200, resp.text
    assert resp.json()["user_id"] == str(AGENT1)


def test_update_preferences_persists_locale(client):
    headers = token(AGENT1)
    resp = client.patch("/api/v1/me/preferences", json={"preferred_locale": "bn"}, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["preferred_locale"] == "bn"
    # Persisted across a fresh read.
    assert client.get("/api/v1/me", headers=headers).json()["preferred_locale"] == "bn"
    # Restore default for other tests.
    client.patch("/api/v1/me/preferences", json={"preferred_locale": "en"}, headers=headers)
