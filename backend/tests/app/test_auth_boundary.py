import pytest

from tests.app.conftest import auth_headers, client

CONFIDENTIAL_ROUTES_STILL_STUBBED = [
    ("GET", "/api/v1/alerts"),
    ("GET", "/api/v1/cases"),
    ("GET", "/api/v1/me"),
    ("GET", "/api/v1/notifications"),
    ("POST", "/api/v1/internal/analytics/liquidity/run"),
    ("POST", "/api/v1/internal/analytics/anomalies/run"),
]

CONFIDENTIAL_ROUTES_IMPLEMENTED = [
    ("GET", "/api/v1/outlets/0b000000-0000-0000-0000-000000000001/dashboard"),
]


@pytest.mark.parametrize("method,path", CONFIDENTIAL_ROUTES_STILL_STUBBED + CONFIDENTIAL_ROUTES_IMPLEMENTED)
def test_confidential_routes_require_auth(client, method, path):
    response = client.request(method, path)
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "unauthorized"


@pytest.mark.parametrize("method,path", CONFIDENTIAL_ROUTES_STILL_STUBBED)
def test_confidential_routes_do_not_bypass_with_auth(client, auth_headers, method, path):
    response = client.request(method, path, headers=auth_headers)
    assert response.status_code == 501
    body = response.json()
    assert body["error"]["code"] == "not_implemented"


@pytest.mark.parametrize("method,path", CONFIDENTIAL_ROUTES_IMPLEMENTED)
def test_phase3_routes_work_with_auth(client, auth_headers, method, path):
    response = client.request(method, path, headers=auth_headers)
    assert response.status_code == 200
