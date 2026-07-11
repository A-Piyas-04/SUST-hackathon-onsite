"""GET /metrics: protected JSON summary with release id + validation metrics."""

from __future__ import annotations

METRICS = "/metrics"


def test_admin_gets_release_and_validation_summary(validation_run_summary, client, admin_headers):
    resp = client.get(METRICS, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["contract_version"]
    rc = body["release_candidate"]
    assert "commit" in rc and "engine_versions" in rc
    assert isinstance(body["process"]["request_count"], int)
    assert isinstance(body["process"]["error_count"], int)
    codes = {m["metric_code"] for m in body["validation_metrics"]}
    assert codes, "expected latest validation metrics in /metrics"
    # No confidential provider/outlet identifiers leak into aggregate metrics.
    assert "outlet_id" not in body
    for m in body["validation_metrics"]:
        assert "provider_id" not in m


def test_management_allowed(validation_run_summary, client, management_headers):
    assert client.get(METRICS, headers=management_headers).status_code == 200


def test_agent_forbidden(client, agent_headers):
    assert client.get(METRICS, headers=agent_headers).status_code == 403


def test_unauthenticated_denied(client):
    assert client.get(METRICS).status_code == 401


def test_health_still_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["contract_version"]
