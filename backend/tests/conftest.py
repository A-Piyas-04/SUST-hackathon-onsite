"""pytest configuration for Phase 1 schema tests.

- Ensures a freshly migrated + seeded database before the session (idempotent).
- Provides a function-scoped connection whose work is rolled back per test.
- Connection comes from env only (DIRECT_DATABASE_URL / DATABASE_URL).
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import psycopg2
import pytest

os.environ.setdefault(
    "DIRECT_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5433/liquidity_platform",
)

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
RUNNER = BACKEND_DIR / "migrations" / "run_migrations.py"

sys.path.insert(0, str(BACKEND_DIR / "tests"))


def _load_dotenv() -> None:
    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key and key not in os.environ:
            os.environ[key] = val


sys.path.insert(0, str(BACKEND_DIR / "migrations"))
import run_migrations  # noqa: E402  (shared DSN normalization / fallback)


def _dsn() -> str:
    """First reachable connection (direct first, then pooler fallback)."""
    _load_dotenv()
    last = None
    for _var, dsn in run_migrations.candidate_dsns():
        try:
            psycopg2.connect(dsn, connect_timeout=15).close()
            return dsn
        except Exception as exc:  # noqa: BLE001
            last = exc
    pytest.exit(f"Could not connect via any configured DSN: {type(last).__name__ if last else 'none'}", 2)


def _session_needs_database(session) -> bool:
    """Only Phase 1 schema/RLS tests require a migrated PostgreSQL instance."""
    for item in session.items:
        path = str(item.path).replace("\\", "/")
        if "/tests/contracts/" in path or "/tests/app/" in path:
            continue
        return True
    return False


@pytest.fixture(scope="session", autouse=True)
def _prepared_db(request):
    """Apply migrations and seeds once per test session (idempotent)."""
    if not _session_needs_database(request.session):
        yield
        return
    env = {**os.environ, "APP_ENV": os.environ.get("APP_ENV", "test")}
    for cmd in ("apply", "seed"):
        proc = subprocess.run(
            [sys.executable, str(RUNNER), cmd],
            capture_output=True, text=True, env=env, cwd=str(BACKEND_DIR),
        )
        if proc.returncode != 0:
            raise RuntimeError(f"run_migrations {cmd} failed:\n{proc.stdout}\n{proc.stderr}")
    yield


@pytest.fixture()
def conn():
    """Superuser connection; each test's writes are rolled back on teardown."""
    c = psycopg2.connect(_dsn())
    try:
        yield c
    finally:
        c.rollback()
        c.close()


@pytest.fixture()
def cur(conn):
    with conn.cursor() as c:
        yield c
    conn.rollback()
