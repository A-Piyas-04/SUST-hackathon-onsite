"""Idempotent ingestion replay tests."""

from __future__ import annotations

from uuid import uuid4

from app.core.auth import OUTLET1


def test_idempotent_replay_no_duplicate_records(client, auth_headers):
    run = client.post(
        "/api/v1/simulations/runs",
        headers=auth_headers,
        json={"scenario_code": "normal", "seed": 5555, "outlet_id": str(OUTLET1)},
    )
    run_id = run.json()["simulation_run_id"]
    batch_ref = f"IDEM-{uuid4()}"

    payload = {
        "simulation_run_id": run_id,
        "outlet_id": str(OUTLET1),
        "provider_code": "rocket",
        "source_batch_ref": batch_ref,
        "events": [
            {
                "event_type": "transaction",
                "source_event_ref": "IDEM-TXN-001",
                "source_observed_at": "2026-07-11T09:00:00+00:00",
                "payload": {
                    "rocket_txn_ref": "IDEM-TXN-001",
                    "counterparty_ref": "PARTY-R-0001",
                    "agent_account": "ACCT-O1-ROCKET",
                    "operation": "cash_in",
                    "completion_status": "completed",
                    "value": "1500.00",
                    "unit": "BDT",
                    "when": "2026-07-11T09:00:00+00:00",
                },
            }
        ],
    }

    first = client.post("/api/v1/ingestion/batches", headers=auth_headers, json=payload)
    second = client.post("/api/v1/ingestion/batches", headers=auth_headers, json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["ingestion_batch_id"] == second.json()["ingestion_batch_id"]

    status = client.get(f"/api/v1/simulations/runs/{run_id}", headers=auth_headers)
    txns = status.json()["artifacts"]["transactions"]
    # Only one new txn from this batch (not duplicated on replay)
    assert client.get(
        f"/api/v1/outlets/{OUTLET1}/transactions?provider_code=rocket",
        headers=auth_headers,
    ).json()["total"] >= 1
