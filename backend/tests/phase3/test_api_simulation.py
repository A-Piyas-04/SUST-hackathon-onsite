"""Simulation and fault route validation tests."""

from __future__ import annotations

from app.core.auth import OUTLET1


def test_run_request_validation(client, auth_headers):
    response = client.post(
        "/api/v1/simulations/runs",
        headers=auth_headers,
        json={"scenario_code": "not_a_scenario"},
    )
    assert response.status_code == 422


def test_fault_request_validation(client, auth_headers):
    run = client.post(
        "/api/v1/simulations/runs",
        headers=auth_headers,
        json={"scenario_code": "normal", "seed": 1001, "outlet_id": str(OUTLET1)},
    )
    run_id = run.json()["simulation_run_id"]

    bad = client.post(
        f"/api/v1/simulations/runs/{run_id}/faults",
        headers=auth_headers,
        json={"fault_type": "invalid_fault", "outlet_id": str(OUTLET1)},
    )
    assert bad.status_code == 422
