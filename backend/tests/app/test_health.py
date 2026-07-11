import pytest

from tests.app.conftest import auth_headers, client


@pytest.mark.integration
def test_health_reports_database_readiness(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "database" in body
    assert response.headers.get("X-Request-ID")
