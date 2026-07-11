"""Authorization and provider-boundary tests (Phase 5 step 2)."""

from __future__ import annotations

from app.core.auth import BKASH, NAGAD_OPS
from tests.phase5.conftest import anomaly_alert, publish, start_run, token

_MISSING = "00000000-0000-0000-0000-0000000000ff"


def test_unauthenticated_confidential_routes_denied(client):
    assert client.get("/api/v1/alerts").status_code == 401
    assert client.get("/api/v1/cases").status_code == 401
    assert client.get(f"/api/v1/alerts/{_MISSING}").status_code == 401


def test_cross_provider_access_denied_and_absent_from_list(client, bkash_ops_headers):
    run_id = start_run(client, bkash_ops_headers, "scenario_b")
    published = publish(client, bkash_ops_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None, published
    alert_id = alert["alert_id"]

    nagad = token(NAGAD_OPS)
    # Detail is denied for the other provider.
    assert client.get(f"/api/v1/alerts/{alert_id}", headers=nagad).status_code == 404
    # And the confidential alert never appears in the other provider's list.
    listing = client.get("/api/v1/alerts", headers=nagad).json()
    assert all(a["alert_id"] != alert_id for a in listing["alerts"])


def test_safe_not_found_identical_for_missing_and_forbidden(client, bkash_ops_headers):
    run_id = start_run(client, bkash_ops_headers, "scenario_b")
    published = publish(client, bkash_ops_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None

    nagad = token(NAGAD_OPS)
    forbidden = client.get(f"/api/v1/alerts/{alert['alert_id']}", headers=nagad)
    missing = client.get(f"/api/v1/alerts/{_MISSING}", headers=nagad)
    assert forbidden.status_code == missing.status_code == 404
    # Same safe body policy: identical code + message, no existence leak.
    assert forbidden.json()["error"]["code"] == missing.json()["error"]["code"] == "not_found"
    assert forbidden.json()["error"]["message"] == missing.json()["error"]["message"]


def test_agent_outlet_scope_can_read_provider_alert(client, bkash_ops_headers):
    from app.core.auth import AGENT1

    run_id = start_run(client, bkash_ops_headers, "scenario_b")
    published = publish(client, bkash_ops_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None
    # Outlet-scoped agent has combined context at the outlet.
    resp = client.get(f"/api/v1/alerts/{alert['alert_id']}", headers=token(AGENT1))
    assert resp.status_code == 200, resp.text
    assert resp.json()["provider_id"] == str(BKASH)
