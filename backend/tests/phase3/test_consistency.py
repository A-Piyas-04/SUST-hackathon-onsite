"""Provider/account/outlet consistency tests."""

from __future__ import annotations

from uuid import uuid4

from app.core.auth import OUTLET1, OUTLET2


def test_mismatched_account_rejected(client, admin_headers):
    run = client.post(
        "/api/v1/simulations/runs",
        headers=admin_headers,
        json={"scenario_code": "normal", "seed": 3333, "outlet_id": str(OUTLET1)},
    )
    run_id = run.json()["simulation_run_id"]

    response = client.post(
        "/api/v1/ingestion/batches",
        headers=admin_headers,
        json={
            "simulation_run_id": run_id,
            "outlet_id": str(OUTLET2),
            "provider_code": "bkash",
            "source_batch_ref": f"MISMATCH-{uuid4()}",
            "events": [
                {
                    "event_type": "transaction",
                    "source_event_ref": "MISMATCH-001",
                    "source_observed_at": "2026-07-11T10:00:00+00:00",
                    "payload": {
                        "bkash_trx_id": "MISMATCH-001",
                        "customer_token": "PARTY-X",
                        "merchant_account": "ACCT-O1-BKASH",
                        "trx_category": "cash_in",
                        "trx_state": "completed",
                        "trx_amount": "100.00",
                        "ccy": "BDT",
                        "event_time": "2026-07-11T10:00:00+00:00",
                    },
                }
            ],
        },
    )
    assert response.status_code == 201
    assert response.json()["rejected_event_count"] >= 1
