"""Shared database DSN normalization — reused by migration runner and async app."""

from __future__ import annotations

import os
import re
from urllib.parse import quote, unquote, urlparse


def load_dotenv(env_path: str | None = None) -> None:
    """Minimal .env loader; existing environment variables win."""
    if env_path is None:
        from pathlib import Path

        env_path = str(Path(__file__).resolve().parents[2] / ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            if key and key not in os.environ:
                os.environ[key] = val


def project_ref() -> str | None:
    ref = os.environ.get("SUPABASE_PROJECT_REF")
    if ref and ref != "YOUR_PROJECT_REF":
        return ref
    for var in ("DIRECT_DATABASE_URL", "SUPABASE_URL", "DATABASE_URL"):
        v = os.environ.get(var, "")
        m = re.search(r"db\.([a-z0-9]{16,})\.supabase\.co", v) or re.search(
            r"https?://([a-z0-9]{16,})\.supabase\.co", v
        )
        if m:
            return m.group(1)
    return None


def clean_dsn(dsn: str) -> str:
    for bad in ("+asyncpg", "+psycopg2", "+psycopg"):
        dsn = dsn.replace(bad, "")
    if "pooler.supabase.com" in dsn and re.search(r"://postgres:", dsn):
        ref = project_ref()
        if ref:
            dsn = re.sub(r"(://)postgres(:)", rf"\1postgres.{ref}\2", dsn, count=1)
    return dsn


def session_variant(dsn: str) -> str | None:
    if "pooler.supabase.com" in dsn and ":6543/" in dsn:
        return re.sub(r":6543/", ":5432/", dsn, count=1)
    return None


def constructed_pooler_dsn() -> str | None:
    pw = os.environ.get("SUPABASE_DB_PASSWORD")
    ref = project_ref()
    if not pw or pw == "YOUR_DATABASE_PASSWORD" or not ref:
        return None
    host = None
    m = re.search(r"@([a-z0-9.-]*pooler\.supabase\.com)", os.environ.get("DATABASE_URL", ""))
    if m:
        host = m.group(1)
    if not host:
        return None
    return (
        f"postgresql://postgres.{ref}:{quote(pw, safe='')}@{host}:5432/postgres?sslmode=require"
    )


def candidate_dsns() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(label: str, dsn: str | None) -> None:
        if dsn and dsn not in seen:
            seen.add(dsn)
            out.append((label, dsn))

    add("SUPABASE_DB_PASSWORD(session-pooler)", constructed_pooler_dsn())
    direct = os.environ.get("DIRECT_DATABASE_URL")
    if direct:
        add("DIRECT_DATABASE_URL", clean_dsn(direct))
    pooler = os.environ.get("DATABASE_URL")
    if pooler:
        cleaned = clean_dsn(pooler)
        add("DATABASE_URL(session)", session_variant(cleaned))
        add("DATABASE_URL", cleaned)
    if not out:
        raise RuntimeError(
            "No database connection configured. Set DIRECT_DATABASE_URL (preferred) "
            "or DATABASE_URL in backend/.env."
        )
    return out


def get_sync_dsn() -> str:
    return candidate_dsns()[0][1]


def to_async_dsn(sync_dsn: str) -> str:
    cleaned = clean_dsn(sync_dsn)
    if cleaned.startswith("postgresql+asyncpg://"):
        return cleaned
    if cleaned.startswith("postgresql://"):
        return cleaned.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise ValueError("Unsupported database URL scheme.")


def safe_target(dsn: str) -> str:
    try:
        u = urlparse(dsn)
        host = u.hostname or "?"
        port = u.port or 5432
        db = unquote((u.path or "/").lstrip("/")) or "?"
        return f"{host}:{port}/{db}"
    except Exception:
        return "<unparseable dsn>"
