"""Ingestion rejection and ledger integrity tests."""

from __future__ import annotations

from uuid import uuid4

from app.core.auth import OUTLET1


def _start_run(client, headers):
    return client.post(
        "/api/v1/simulations/runs",
        headers=headers,
        json={"scenario_code": "normal", "seed": 9001, "outlet_id": str(OUTLET1)},
    )


def test_malformed_payload_rejected_with_reason(client, auth_headers):
    run = _start_run(client, auth_headers)
    run_id = run.json()["simulation_run_id"]

    response = client.post(
        "/api/v1/ingestion/batches",
        headers=auth_headers,
        json={
            "simulation_run_id": run_id,
            "outlet_id": str(OUTLET1),
            "provider_code": "bkash",
            "source_batch_ref": f"MALFORMED-{uuid4()}",
            "events": [
                {
                    "event_type": "transaction",
                    "source_event_ref": "BAD-001",
                    "source_observed_at": "2026-07-11T08:00:00+00:00",
                    "payload": {"__corrupt__": True},
                }
            ],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["rejected_event_count"] == 1
    assert body["events"][0]["rejection_code"] == "malformed_payload"


def test_rejected_payload_zero_ledger_mutation(client, auth_headers):
    run = _start_run(client, auth_headers)
    run_id = run.json()["simulation_run_id"]
    before = run.json()["artifacts"]

    client.post(
        "/api/v1/ingestion/batches",
        headers=auth_headers,
        json={
            "simulation_run_id": run_id,
            "outlet_id": str(OUTLET1),
            "provider_code": "nagad",
            "source_batch_ref": f"REJECT-{uuid4()}",
            "events": [
                {
                    "event_type": "transaction",
                    "source_event_ref": "BAD-002",
                    "payload": {"invalid": "data"},
                }
            ],
        },
    )

    status = client.get(f"/api/v1/simulations/runs/{run_id}", headers=auth_headers)
    after = status.json()["artifacts"]
    assert after["transactions"] == before["transactions"]
    assert after["cash_snapshots"] == before["cash_snapshots"]
    assert after["provider_snapshots"] == before["provider_snapshots"]
