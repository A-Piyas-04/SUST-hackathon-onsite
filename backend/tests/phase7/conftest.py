"""Phase 7 validation/observability/safety test fixtures."""

from __future__ import annotations

import asyncio
import os

import pytest
from fastapi.testclient import TestClient

from app.core.auth import ADMIN, AGENT1, BKASH_OPS, MGMT, RISK_BK
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


def token(user_id) -> dict[str, str]:
    return {"Authorization": f"Bearer demo:{user_id}"}


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
def admin_headers() -> dict[str, str]:
    return token(ADMIN)


@pytest.fixture
def management_headers() -> dict[str, str]:
    return token(MGMT)


@pytest.fixture
def agent_headers() -> dict[str, str]:
    return token(AGENT1)


@pytest.fixture
def bkash_ops_headers() -> dict[str, str]:
    return token(BKASH_OPS)


@pytest.fixture
def risk_headers() -> dict[str, str]:
    return token(RISK_BK)


async def _run_harness_async() -> dict:
    from app.db.engine import create_engine, dispose_engine, set_engine
    from app.db.session import get_session_factory, init_session_factory
    from app.db.transaction import transaction
    from app.services.validation.harness import run_validation

    get_settings.cache_clear()
    settings = Settings(
        direct_database_url=os.environ["TEST_DATABASE_URL"],
        database_url=None,
        app_env="test",
    )
    engine = create_engine(settings)
    set_engine(engine)
    init_session_factory()
    factory = get_session_factory()
    try:
        async with factory() as session:
            async with transaction(session):
                return await run_validation(session)
    finally:
        await dispose_engine()


def run_harness_once() -> dict:
    """Run the held-out harness once (fresh event loop) and commit results."""
    return asyncio.run(_run_harness_async())


@pytest.fixture(scope="session")
def validation_run_summary() -> dict:
    """A committed completed validation run available to the whole module."""
    return run_harness_once()
