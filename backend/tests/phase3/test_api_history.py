"""Balance history API tests."""

from __future__ import annotations

from app.core.auth import OUTLET1


def test_history_requires_reserve_type(client, auth_headers):
    response = client.get(
        f"/api/v1/outlets/{OUTLET1}/balances/history",
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_history_returns_typed_records(client, auth_headers):
    client.post(
        "/api/v1/simulations/runs",
        headers=auth_headers,
        json={"scenario_code": "normal", "seed": 1001, "outlet_id": str(OUTLET1)},
    )
    cash = client.get(
        f"/api/v1/outlets/{OUTLET1}/balances/history",
        headers=auth_headers,
        params={"reserve_type": "shared_cash"},
    )
    assert cash.status_code == 200
    assert cash.json()["reserve_type"] == "shared_cash"
    assert all(i["reserve_type"] == "shared_cash" for i in cash.json()["items"])

    prov = client.get(
        f"/api/v1/outlets/{OUTLET1}/balances/history",
        headers=auth_headers,
        params={"reserve_type": "provider_e_money", "provider_code": "bkash"},
    )
    assert prov.status_code == 200
    assert prov.json()["reserve_type"] == "provider_e_money"
