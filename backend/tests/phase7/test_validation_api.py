"""GET /api/v1/validation/results: persistence-backed reads, filters, authz."""

from __future__ import annotations

from app.contracts.v1.validation import ValidationMetricPayload

RESULTS = "/api/v1/validation/results"


def test_admin_reads_persisted_runs(validation_run_summary, client, admin_headers):
    resp = client.get(RESULTS, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["runs"], "expected at least one persisted run"
    run = body["runs"][0]
    assert run["metrics"], "run should carry nested metric results"
    # Response conforms to the frozen contract.
    ValidationMetricPayload.model_validate(run)


def test_management_can_read(validation_run_summary, client, management_headers):
    resp = client.get(RESULTS, headers=management_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["runs"]


def test_filters_apply(validation_run_summary, client, admin_headers):
    run_id = validation_run_summary["validation_run_id"]
    completed = client.get(f"{RESULTS}?status=completed", headers=admin_headers).json()["runs"]
    assert any(r["validation_run_id"] == run_id for r in completed)

    held_out = client.get(f"{RESULTS}?dataset_split=held_out", headers=admin_headers).json()["runs"]
    assert all(r["dataset_split"] == "held_out" for r in held_out)

    demo = client.get(f"{RESULTS}?dataset_split=demo", headers=admin_headers).json()["runs"]
    assert demo == []

    single = client.get(f"{RESULTS}?validation_run_id={run_id}", headers=admin_headers).json()["runs"]
    assert len(single) == 1 and single[0]["validation_run_id"] == run_id


def test_agent_forbidden(client, agent_headers):
    resp = client.get(RESULTS, headers=agent_headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


def test_provider_ops_forbidden(client, bkash_ops_headers):
    assert client.get(RESULTS, headers=bkash_ops_headers).status_code == 403


def test_risk_analyst_forbidden(client, risk_headers):
    assert client.get(RESULTS, headers=risk_headers).status_code == 403


def test_unauthenticated_denied(client):
    assert client.get(RESULTS).status_code == 401
