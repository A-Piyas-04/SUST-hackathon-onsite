"""App-level test fixtures."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.core.auth import AGENT1
from app.core.config import Settings, get_settings
from app.main import create_app

os.environ.setdefault(
    "DIRECT_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/liquidity_platform",
)


@pytest.fixture
def settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def client(settings: Settings) -> TestClient:
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer demo:{AGENT1}"}
