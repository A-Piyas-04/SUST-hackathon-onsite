from tests.app.conftest import client


def test_health_is_public(client):
    response = client.get("/health")
    assert response.status_code in {200, 503}
