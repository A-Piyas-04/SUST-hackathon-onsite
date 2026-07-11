"""App-level test fixtures."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.core.auth import AGENT1
from app.core.config import Settings, get_settings
from app.main import create_app

from helpers import resolve_test_dsn

_test_dsn = resolve_test_dsn()
os.environ["APP_ENV"] = "test"
os.environ["DIRECT_DATABASE_URL"] = _test_dsn
os.environ.pop("DATABASE_URL", None)
os.environ.pop("SUPABASE_DB_PASSWORD", None)


@pytest.fixture
def settings() -> Settings:
    get_settings.cache_clear()
    return Settings(
        direct_database_url=_test_dsn,
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
