"""Authorization and provider-boundary tests (Phase 5 step 2)."""

from __future__ import annotations

from app.core.auth import AGENT1, AGENT2, BKASH, MGMT, NAGAD_OPS, OUTLET1, OUTLET2, RISK_BK
from tests.phase5.conftest import anomaly_alert, publish, start_run, token

_MISSING = "00000000-0000-0000-0000-0000000000ff"


def test_unauthenticated_confidential_routes_denied(client):
    assert client.get("/api/v1/alerts").status_code == 401
    assert client.get("/api/v1/cases").status_code == 401
    assert client.get(f"/api/v1/alerts/{_MISSING}").status_code == 401


def test_cross_provider_access_denied_and_absent_from_list(client, bkash_ops_headers, admin_headers):
    run_id = start_run(client, admin_headers, "scenario_b")
    published = publish(client, admin_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None, published
    alert_id = alert["alert_id"]

    nagad = token(NAGAD_OPS)
    # Detail is denied for the other provider.
    assert client.get(f"/api/v1/alerts/{alert_id}", headers=nagad).status_code == 404
    # And the confidential alert never appears in the other provider's list.
    listing = client.get("/api/v1/alerts", headers=nagad).json()
    assert all(a["alert_id"] != alert_id for a in listing["alerts"])


def test_safe_not_found_identical_for_missing_and_forbidden(client, bkash_ops_headers, admin_headers):
    run_id = start_run(client, admin_headers, "scenario_b")
    published = publish(client, admin_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None

    nagad = token(NAGAD_OPS)
    forbidden = client.get(f"/api/v1/alerts/{alert['alert_id']}", headers=nagad)
    missing = client.get(f"/api/v1/alerts/{_MISSING}", headers=nagad)
    assert forbidden.status_code == missing.status_code == 404
    # Same safe body policy: identical code + message, no existence leak.
    assert forbidden.json()["error"]["code"] == missing.json()["error"]["code"] == "not_found"
    assert forbidden.json()["error"]["message"] == missing.json()["error"]["message"]


def test_agent_outlet_scope_can_read_provider_alert(client, bkash_ops_headers, admin_headers):
    run_id = start_run(client, admin_headers, "scenario_b")
    published = publish(client, admin_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None
    # Outlet-scoped agent has combined context at the outlet.
    resp = client.get(f"/api/v1/alerts/{alert['alert_id']}", headers=token(AGENT1))
    assert resp.status_code == 200, resp.text
    assert resp.json()["provider_id"] == str(BKASH)


def test_agent_cannot_read_other_outlet_dashboard(client, admin_headers):
    client.post(
        "/api/v1/simulations/runs",
        headers=admin_headers,
        json={"scenario_code": "normal", "seed": 909090, "outlet_id": str(OUTLET1)},
    )
    resp = client.get(
        f"/api/v1/outlets/{OUTLET2}/dashboard",
        headers=token(AGENT1),
    )
    assert resp.status_code == 404


def test_agent_cannot_start_simulation(client, agent_headers):
    resp = client.post(
        "/api/v1/simulations/runs",
        headers=agent_headers,
        json={"scenario_code": "normal", "seed": 1234, "outlet_id": str(OUTLET1)},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


def test_management_cannot_resolve_case(client, bkash_ops_headers, management_headers, admin_headers):
    run_id = start_run(client, admin_headers, "scenario_b")
    published = publish(client, admin_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None
    case = client.post(
        f"/api/v1/alerts/{alert['alert_id']}/cases", json={}, headers=bkash_ops_headers
    ).json()
    client.post(f"/api/v1/cases/{case['case_id']}/acknowledge", json={}, headers=bkash_ops_headers)
    resp = client.post(
        f"/api/v1/cases/{case['case_id']}/resolve",
        json={"resolution_summary": "should not apply"},
        headers=management_headers,
    )
    assert resp.status_code == 403


def test_agent_outlets_list_is_scoped(client, agent_headers):
    outlets = client.get("/api/v1/outlets", headers=agent_headers).json()
    assert len(outlets) == 1
    assert outlets[0]["outlet_id"] == str(OUTLET1)


def test_non_admin_cannot_publish_alerts(client, bkash_ops_headers, admin_headers):
    run_id = start_run(client, admin_headers, "scenario_b")
    resp = client.post(
        "/api/v1/internal/alerts/publish",
        json={"simulation_run_id": run_id, "outlet_id": str(OUTLET1)},
        headers=bkash_ops_headers,
    )
    assert resp.status_code == 403


def test_risk_analyst_can_review_but_not_resolve(client, bkash_ops_headers, risk_headers, admin_headers):
    run_id = start_run(client, admin_headers, "scenario_b")
    published = publish(client, admin_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None
    case = client.post(
        f"/api/v1/alerts/{alert['alert_id']}/cases", json={}, headers=bkash_ops_headers
    ).json()
    client.post(f"/api/v1/cases/{case['case_id']}/acknowledge", json={}, headers=bkash_ops_headers)
    client.post(
        f"/api/v1/cases/{case['case_id']}/escalate",
        json={"target_role": "risk_analyst"},
        headers=bkash_ops_headers,
    )
    review = client.post(
        f"/api/v1/cases/{case['case_id']}/review",
        json={
            "disposition": "requires_follow_up",
            "review_summary": "Operational follow-up warranted.",
            "was_false_positive": False,
        },
        headers=risk_headers,
    )
    assert review.status_code == 201, review.text
    resolve = client.post(
        f"/api/v1/cases/{case['case_id']}/resolve",
        json={"resolution_summary": "Reviewed and coordinated; no further action required at this time."},
        headers=risk_headers,
    )
    assert resolve.status_code == 403
