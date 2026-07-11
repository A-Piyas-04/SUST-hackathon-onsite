"""Route registration + scaffolding-behaviour tests.

Proves Member 1 can compose the Member 2 surface (all 19 MVP endpoints appear
under /api/v1), that unimplemented actions return an honest 501 (never a fake
200), and that the idempotency/version header policy is frozen and consistent.
"""
from __future__ import annotations

import json

from fastapi import FastAPI

from app.coordination.router import get_member2_routers, include_member2_routers
from app.coordination.shared.http import not_implemented
from app.coordination.shared.idempotency import (
    IDEMPOTENT_ENDPOINTS,
    requires_idempotency_key,
)

EXPECTED_ENDPOINTS = {
    ("POST", "/api/v1/auth/demo-login"),
    ("GET", "/api/v1/me"),
    ("PATCH", "/api/v1/me/preferences"),
    ("GET", "/api/v1/alerts"),
    ("GET", "/api/v1/alerts/{alert_id}"),
    ("GET", "/api/v1/alerts/{alert_id}/explanations"),
    ("POST", "/api/v1/alerts/{alert_id}/cases"),
    ("GET", "/api/v1/cases"),
    ("GET", "/api/v1/cases/{case_id}"),
    ("GET", "/api/v1/cases/{case_id}/timeline"),
    ("POST", "/api/v1/cases/{case_id}/assignments"),
    ("POST", "/api/v1/cases/{case_id}/acknowledge"),
    ("POST", "/api/v1/cases/{case_id}/escalate"),
    ("POST", "/api/v1/cases/{case_id}/resolve"),
    ("POST", "/api/v1/cases/{case_id}/notes"),
    ("POST", "/api/v1/cases/{case_id}/review"),
    ("GET", "/api/v1/notifications"),
    ("POST", "/api/v1/notifications/{notification_id}/read"),
    ("GET", "/api/v1/cases/{case_id}/audit-events"),
}


def _composed_paths():
    app = FastAPI()
    include_member2_routers(app)
    paths = app.openapi()["paths"]
    return {(m.upper(), p) for p, ops in paths.items() for m in ops}


def test_all_routers_import_and_register():
    routers = get_member2_routers()
    assert len(routers) == 5


def test_all_19_mvp_endpoints_compose_under_api_v1():
    composed = _composed_paths()
    assert EXPECTED_ENDPOINTS <= composed, EXPECTED_ENDPOINTS - composed
    # Exactly the 19 owned endpoints, nothing extra registered.
    assert composed == EXPECTED_ENDPOINTS
    assert len(EXPECTED_ENDPOINTS) == 19


def test_composition_does_not_require_member1_or_member3():
    # include_member2_routers must work on a bare app with no other packages.
    app = FastAPI()
    include_member2_routers(app)  # must not raise
    assert app.openapi()["info"]["title"]


def test_unimplemented_action_returns_honest_501():
    resp = not_implemented("Case resolve", None)
    assert resp.status_code == 501
    body = json.loads(bytes(resp.body))
    assert body["error"]["code"] == "NOT_IMPLEMENTED"
    assert body["error"]["request_id"]
    assert body["error"]["details"] == {}


def test_idempotency_required_for_all_mutating_posts():
    mutating_posts = {(m, p) for (m, p) in EXPECTED_ENDPOINTS if m == "POST" and p != "/api/v1/auth/demo-login"}
    idem = set(IDEMPOTENT_ENDPOINTS)
    assert mutating_posts == idem


def test_requires_idempotency_key_policy():
    assert requires_idempotency_key("POST", "/api/v1/cases/{case_id}/resolve")
    assert not requires_idempotency_key("GET", "/api/v1/cases")
    assert not requires_idempotency_key("POST", "/api/v1/auth/demo-login")
