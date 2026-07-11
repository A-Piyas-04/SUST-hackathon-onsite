"""Dashboard API contract tests."""

from __future__ import annotations

from app.core.auth import OUTLET1


def test_dashboard_separated_reserves(client, auth_headers):
    client.post(
        "/api/v1/simulations/runs",
        headers=auth_headers,
        json={"scenario_code": "normal", "seed": 1001, "outlet_id": str(OUTLET1)},
    )
    response = client.get(
        f"/api/v1/outlets/{OUTLET1}/dashboard",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["shared_cash"]["balance"] is not None
    provider_codes = {p["provider"]["code"] for p in body["providers"]}
    assert provider_codes == {"bkash", "nagad", "rocket"}
