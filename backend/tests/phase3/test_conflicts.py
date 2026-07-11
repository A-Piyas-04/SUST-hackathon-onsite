"""Conflicting snapshot coexistence tests."""

from __future__ import annotations

from app.core.auth import OUTLET1


def test_conflicting_snapshots_coexist(client, auth_headers, admin_headers):
    run = client.post(
        "/api/v1/simulations/runs",
        headers=admin_headers,
        json={"scenario_code": "normal", "seed": 6060, "outlet_id": str(OUTLET1)},
    )
    run_id = run.json()["simulation_run_id"]

    client.post(
        f"/api/v1/simulations/runs/{run_id}/faults",
        headers=admin_headers,
        json={
            "fault_type": "conflicting_balance",
            "outlet_id": str(OUTLET1),
            "parameters": {"target_provider": "nagad", "conflict_delta": "750.00"},
        },
    )

    reset = client.post(f"/api/v1/simulations/runs/{run_id}/reset", headers=admin_headers)
    assert reset.status_code == 200

    history = client.get(
        f"/api/v1/outlets/{OUTLET1}/balances/history",
        headers=auth_headers,
        params={"reserve_type": "provider_e_money", "provider_code": "nagad"},
    )
    assert history.status_code == 200
    items = history.json()["items"]
    conflicted = [i for i in items if i.get("is_conflicted")]
    assert len(conflicted) >= 1
