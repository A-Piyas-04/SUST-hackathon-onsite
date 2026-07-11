"""Phase 4 analytics test fixtures."""

from __future__ import annotations

import os
import random

import pytest
from fastapi.testclient import TestClient

from app.core.auth import AGENT1, OUTLET1
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


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer demo:{AGENT1}"}


@pytest.fixture
def outlet_id():
    return OUTLET1


def start_run(client: TestClient, headers: dict[str, str], scenario: str, seed: int | None = None) -> str:
    # The ledger is append-only and transactions are globally idempotent by
    # (provider, synthetic_transaction_ref), where the ref embeds the run seed.
    # Use a unique seed per run so each run owns its own transactions rather than
    # being deduplicated against transactions from an earlier run/session.
    if seed is None:
        seed = random.randrange(1, 2_000_000_000)
    body: dict = {"scenario_code": scenario, "outlet_id": str(OUTLET1), "seed": seed}
    resp = client.post("/api/v1/simulations/runs", json=body, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["simulation_run_id"]
