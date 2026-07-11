"""No blended monetary total in API responses."""

from __future__ import annotations

from app.core.auth import OUTLET1


def test_dashboard_has_no_blended_total(client, auth_headers, admin_headers):
    client.post(
        "/api/v1/simulations/runs",
        headers=admin_headers,
        json={"scenario_code": "normal", "seed": 1111, "outlet_id": str(OUTLET1)},
    )
    response = client.get(
        f"/api/v1/outlets/{OUTLET1}/dashboard",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert "total_balance" not in body
    assert "shared_cash" in body
    assert "providers" in body


def test_history_has_no_blended_total(client, auth_headers):
    response = client.get(
        f"/api/v1/outlets/{OUTLET1}/balances/history",
        headers=auth_headers,
        params={"reserve_type": "shared_cash"},
    )
    assert response.status_code == 200
    assert "total_balance" not in response.json()
