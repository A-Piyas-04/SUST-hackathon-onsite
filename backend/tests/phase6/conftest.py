"""Phase 5 coordination test fixtures and helpers."""

from __future__ import annotations

import os
import random

import pytest
from fastapi.testclient import TestClient

from app.core.auth import (
    ADMIN,
    AGENT1,
    AGENT2,
    BKASH,
    BKASH_OPS,
    MGMT,
    NAGAD,
    NAGAD_OPS,
    OUTLET1,
    RISK_BK,
    ROCKET_OPS,
)
from app.core.config import Settings, get_settings
from app.main import create_app

os.environ.setdefault(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/liquidity_platform",
)
os.environ["APP_ENV"] = "test"
os.environ["DIRECT_DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ.pop("DATABASE_URL", None)
os.environ.pop("SUPABASE_DB_PASSWORD", None)


@pytest.fixture
def settings() -> Settings:
    get_settings.cache_clear()
    return Settings(
        direct_database_url=os.environ["TEST_DATABASE_URL"],
        database_url=None,
        app_env="test",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


def token(user_id) -> dict[str, str]:
    return {"Authorization": f"Bearer demo:{user_id}"}


@pytest.fixture
def agent_headers() -> dict[str, str]:
    return token(AGENT1)


@pytest.fixture
def bkash_ops_headers() -> dict[str, str]:
    return token(BKASH_OPS)


@pytest.fixture
def nagad_ops_headers() -> dict[str, str]:
    return token(NAGAD_OPS)


@pytest.fixture
def bkash_ops_headers() -> dict[str, str]:
    return token(BKASH_OPS)


@pytest.fixture
def risk_headers() -> dict[str, str]:
    return token(RISK_BK)


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return token(ADMIN)


@pytest.fixture
def management_headers() -> dict[str, str]:
    return token(MGMT)


@pytest.fixture
def outlet_id():
    return OUTLET1


def start_run(client: TestClient, headers: dict[str, str], scenario: str, seed: int | None = None) -> str:
    if seed is None:
        seed = random.randrange(1, 2_000_000_000)
    body = {"scenario_code": scenario, "outlet_id": str(OUTLET1), "seed": seed}
    resp = client.post("/api/v1/simulations/runs", json=body, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["simulation_run_id"]


def publish(client: TestClient, headers: dict[str, str], run_id: str) -> dict:
    resp = client.post(
        "/api/v1/internal/alerts/publish",
        json={"simulation_run_id": run_id, "outlet_id": str(OUTLET1)},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def anomaly_alert(published: dict) -> dict | None:
    for a in published["published"]:
        if a["alert_type"] == "anomaly" and a["provider_id"] == str(BKASH):
            return a
    return None
