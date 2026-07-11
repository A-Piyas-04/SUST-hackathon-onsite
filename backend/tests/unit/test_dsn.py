"""Unit tests for app.db.dsn — DSN normalization shared by the migration
runner and the async app. Pure logic, no database required."""

from __future__ import annotations

import pytest

from app.db import dsn as dsn_mod

POOLER = "aws-0-ap-southeast-2.pooler.supabase.com"
REF = "abcdefghijklmnop"  # 16 chars, matches the {16,} project-ref pattern


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Each test starts from a blank slate for the vars dsn.py reads."""
    for var in (
        "DIRECT_DATABASE_URL",
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_PROJECT_REF",
        "SUPABASE_DB_PASSWORD",
    ):
        monkeypatch.delenv(var, raising=False)


# --------------------------------------------------------------- project_ref
def test_project_ref_prefers_explicit_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_PROJECT_REF", REF)
    assert dsn_mod.project_ref() == REF


def test_project_ref_ignores_placeholder_and_derives_from_direct_url(monkeypatch):
    monkeypatch.setenv("SUPABASE_PROJECT_REF", "YOUR_PROJECT_REF")
    monkeypatch.setenv(
        "DIRECT_DATABASE_URL", f"postgresql://postgres:pw@db.{REF}.supabase.co:5432/postgres"
    )
    assert dsn_mod.project_ref() == REF


def test_project_ref_derives_from_supabase_url(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", f"https://{REF}.supabase.co")
    assert dsn_mod.project_ref() == REF


def test_project_ref_none_when_unconfigured():
    assert dsn_mod.project_ref() is None


# ----------------------------------------------------------------- clean_dsn
def test_clean_dsn_strips_sqlalchemy_driver_suffixes():
    assert (
        dsn_mod.clean_dsn("postgresql+asyncpg://u:p@h:5432/db")
        == "postgresql://u:p@h:5432/db"
    )
    assert (
        dsn_mod.clean_dsn("postgresql+psycopg2://u:p@h:5432/db")
        == "postgresql://u:p@h:5432/db"
    )


def test_clean_dsn_qualifies_bare_postgres_user_on_pooler(monkeypatch):
    monkeypatch.setenv("SUPABASE_PROJECT_REF", REF)
    cleaned = dsn_mod.clean_dsn(f"postgresql://postgres:pw@{POOLER}:5432/postgres")
    assert cleaned.startswith(f"postgresql://postgres.{REF}:pw@")


def test_clean_dsn_leaves_non_pooler_hosts_alone():
    dsn = "postgresql://postgres:pw@localhost:5432/db"
    assert dsn_mod.clean_dsn(dsn) == dsn


# ----------------------------------------------------------- session_variant
def test_session_variant_rewrites_transaction_pooler_port():
    dsn = f"postgresql://u:p@{POOLER}:6543/postgres"
    assert dsn_mod.session_variant(dsn) == f"postgresql://u:p@{POOLER}:5432/postgres"


def test_session_variant_none_for_direct_or_session_dsn():
    assert dsn_mod.session_variant("postgresql://u:p@localhost:6543/db") is None
    assert dsn_mod.session_variant(f"postgresql://u:p@{POOLER}:5432/db") is None


# ---------------------------------------------------- constructed_pooler_dsn
def test_constructed_pooler_dsn_urlencodes_password(monkeypatch):
    monkeypatch.setenv("SUPABASE_PROJECT_REF", REF)
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "p@ss/w:rd")
    monkeypatch.setenv("DATABASE_URL", f"postgresql://u:p@{POOLER}:6543/postgres")
    built = dsn_mod.constructed_pooler_dsn()
    assert built == (
        f"postgresql://postgres.{REF}:p%40ss%2Fw%3Ard@{POOLER}:5432/postgres?sslmode=require"
    )


def test_constructed_pooler_dsn_none_without_password_or_host(monkeypatch):
    monkeypatch.setenv("SUPABASE_PROJECT_REF", REF)
    assert dsn_mod.constructed_pooler_dsn() is None  # no password
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "YOUR_DATABASE_PASSWORD")
    assert dsn_mod.constructed_pooler_dsn() is None  # placeholder password
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "real-pw")
    assert dsn_mod.constructed_pooler_dsn() is None  # no pooler host in DATABASE_URL


# -------------------------------------------------------------- candidate_dsns
def test_candidate_dsns_prefers_direct_then_pooler_variants(monkeypatch):
    monkeypatch.setenv("DIRECT_DATABASE_URL", "postgresql://u:p@localhost:5432/db")
    monkeypatch.setenv("DATABASE_URL", f"postgresql://u:p@{POOLER}:6543/postgres")
    labels = [label for label, _ in dsn_mod.candidate_dsns()]
    assert labels == ["DIRECT_DATABASE_URL", "DATABASE_URL(session)", "DATABASE_URL"]


def test_candidate_dsns_deduplicates(monkeypatch):
    same = "postgresql://u:p@localhost:5432/db"
    monkeypatch.setenv("DIRECT_DATABASE_URL", same)
    monkeypatch.setenv("DATABASE_URL", same)
    assert [d for _, d in dsn_mod.candidate_dsns()] == [same]


def test_candidate_dsns_raises_clear_error_when_unconfigured():
    with pytest.raises(RuntimeError, match="No database connection configured"):
        dsn_mod.candidate_dsns()


# ---------------------------------------------------------------- to_async_dsn
def test_to_async_dsn_adds_driver_and_strips_libpq_params():
    out = dsn_mod.to_async_dsn("postgresql://u:p@h:5432/db?sslmode=require")
    assert out == "postgresql+asyncpg://u:p@h:5432/db"


def test_to_async_dsn_idempotent_for_asyncpg_scheme():
    out = dsn_mod.to_async_dsn("postgresql+asyncpg://u:p@h:5432/db")
    assert out == "postgresql+asyncpg://u:p@h:5432/db"


def test_to_async_dsn_rejects_unknown_scheme():
    with pytest.raises(ValueError, match="Unsupported database URL scheme"):
        dsn_mod.to_async_dsn("mysql://u:p@h:3306/db")


# ------------------------------------------------------------------ safe_target
def test_safe_target_never_exposes_credentials():
    desc = dsn_mod.safe_target("postgresql://user:secret@db.example.com:6543/mydb")
    assert desc == "db.example.com:6543/mydb"
    assert "secret" not in desc and "user" not in desc


def test_safe_target_defaults_port_and_handles_garbage():
    assert dsn_mod.safe_target("postgresql://u:p@host/db") == "host:5432/db"
    assert dsn_mod.safe_target("http://[") == "<unparseable dsn>"


# ------------------------------------------------------------------- load_dotenv
def test_load_dotenv_parses_file_and_existing_env_wins(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# comment\n"
        "\n"
        "NEW_KEY=from_file\n"
        "EXISTING_KEY=from_file\n"
        "not_a_pair\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("NEW_KEY", raising=False)
    monkeypatch.setenv("EXISTING_KEY", "from_env")
    dsn_mod.load_dotenv(str(env_file))
    assert dsn_mod.os.environ["NEW_KEY"] == "from_file"
    assert dsn_mod.os.environ["EXISTING_KEY"] == "from_env"
    monkeypatch.delenv("NEW_KEY", raising=False)


def test_load_dotenv_missing_file_is_noop(tmp_path):
    dsn_mod.load_dotenv(str(tmp_path / "does-not-exist.env"))  # must not raise
