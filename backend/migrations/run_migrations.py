#!/usr/bin/env python3
"""Forward-only, checksum-tracked migration runner for the Multi-Provider Agent
Liquidity & Coordination Platform (Phase 1).

Connections come from environment variables only (never hard-coded):
  * DIRECT_DATABASE_URL  (preferred — direct 5432 connection, needed for RLS
    session tests and role management)
  * DATABASE_URL         (fallback — pooler/session connection)

Secrets are never printed; only host/db are echoed.

Commands:
  apply | migrate   Apply pending migrations in numeric order (idempotent).
  reset             Drop and recreate the schema (development only).
  seed              Apply backend/seeds/reference_seed.sql (idempotent).
  verify            Run the pytest schema/RLS/view suite.
  dump              Write a schema-only snapshot to docs/verification/schema.sql.
  status            Show applied vs pending migrations.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import sys
from urllib.parse import urlparse, unquote

try:
    import psycopg2
except ImportError:  # pragma: no cover - dependency is declared in requirements.txt
    sys.stderr.write("ERROR: psycopg2 is required (pip install -r backend/requirements.txt)\n")
    raise SystemExit(2)

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
MIGRATIONS_DIR = BACKEND_DIR / "migrations"
SEED_FILE = BACKEND_DIR / "seeds" / "reference_seed.sql"
DUMP_FILE = REPO_ROOT / "docs" / "verification" / "schema.sql"

MIGRATION_GLOB = "0*.sql"


# --------------------------------------------------------------------------- #
# Environment / connection helpers
# --------------------------------------------------------------------------- #
def _load_dotenv() -> None:
    """Minimal .env loader (no external dependency). Existing env wins."""
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


def _project_ref() -> str | None:
    """Derive the Supabase project ref from env (for pooler user qualification)."""
    import re
    ref = os.environ.get("SUPABASE_PROJECT_REF")
    if ref and ref != "YOUR_PROJECT_REF":
        return ref
    for var in ("DIRECT_DATABASE_URL", "SUPABASE_URL", "DATABASE_URL"):
        v = os.environ.get(var, "")
        m = re.search(r"db\.([a-z0-9]{16,})\.supabase\.co", v) or \
            re.search(r"https?://([a-z0-9]{16,})\.supabase\.co", v)
        if m:
            return m.group(1)
    return None


def _clean(dsn: str) -> str:
    import re
    # SQLAlchemy-style async prefixes are not understood by psycopg2/libpq.
    for bad in ("+asyncpg", "+psycopg2", "+psycopg"):
        dsn = dsn.replace(bad, "")
    # Supabase poolers require a tenant-qualified user (postgres.<ref>), not the
    # bare 'postgres'. Normalise deterministically when we can derive the ref.
    if "pooler.supabase.com" in dsn and re.search(r"://postgres:", dsn):
        ref = _project_ref()
        if ref:
            dsn = re.sub(r"(://)postgres(:)", rf"\1postgres.{ref}\2", dsn, count=1)
    return dsn


def _session_variant(dsn: str) -> str | None:
    """For a transaction-mode pooler DSN (:6543), return the session variant
    (:5432), which supports SET ROLE / session settings needed by RLS tests."""
    import re
    if "pooler.supabase.com" in dsn and ":6543/" in dsn:
        return re.sub(r":6543/", ":5432/", dsn, count=1)
    return None


def _constructed_pooler_dsn() -> str | None:
    """Build a session-pooler DSN from parts when SUPABASE_DB_PASSWORD is set.

    Passing the password separately (URL-encoded here) avoids connection-string
    encoding pitfalls with special characters.
    """
    import re
    from urllib.parse import quote
    pw = os.environ.get("SUPABASE_DB_PASSWORD")
    ref = _project_ref()
    if not pw or pw == "YOUR_DATABASE_PASSWORD" or not ref:
        return None
    host = None
    for var in ("DATABASE_URL",):
        m = re.search(r"@([a-z0-9.-]*pooler\.supabase\.com)", os.environ.get(var, ""))
        if m:
            host = m.group(1)
    if not host:
        return None
    return f"postgresql://postgres.{ref}:{quote(pw, safe='')}@{host}:5432/postgres?sslmode=require"


def candidate_dsns() -> list[tuple[str, str]]:
    """Ordered connection candidates. Preference order:
      1. constructed session pooler from SUPABASE_DB_PASSWORD (if provided)
      2. DIRECT_DATABASE_URL (direct 5432)
      3. session variant (:5432) of a transaction-mode pooler DATABASE_URL
      4. DATABASE_URL as given (pooler fallback)

    Raises a clear, secret-free error when nothing is configured.
    """
    out: list[tuple[str, str]] = []
    seen = set()

    def add(label, dsn):
        if dsn and dsn not in seen:
            seen.add(dsn)
            out.append((label, dsn))

    add("SUPABASE_DB_PASSWORD(session-pooler)", _constructed_pooler_dsn())
    direct = os.environ.get("DIRECT_DATABASE_URL")
    if direct:
        add("DIRECT_DATABASE_URL", _clean(direct))
    pooler = os.environ.get("DATABASE_URL")
    if pooler:
        cleaned = _clean(pooler)
        add("DATABASE_URL(session)", _session_variant(cleaned))
        add("DATABASE_URL", cleaned)
    if not out:
        raise SystemExit(
            "ERROR: no database connection configured.\n"
            "Set DIRECT_DATABASE_URL (preferred) or DATABASE_URL in backend/.env "
            "(copy backend/.env.example). Never commit real credentials."
        )
    return out


def open_connection():
    """Connect using the first reachable candidate (direct -> pooler fallback).

    Returns (var_name, dsn, connection). Errors never include credentials.
    """
    errors = []
    for var, dsn in candidate_dsns():
        try:
            conn = psycopg2.connect(dsn, connect_timeout=15)
            return var, dsn, conn
        except Exception as exc:  # noqa: BLE001
            # str(exc) for psycopg2 contains host/port only, never the password.
            errors.append(f"  {var} ({safe_target(dsn)}): {type(exc).__name__}: {exc}".rstrip())
    raise SystemExit(
        "ERROR: could not connect via any configured DSN.\n" + "\n".join(errors)
    )


def get_dsn() -> str:
    return candidate_dsns()[0][1]


def safe_target(dsn: str) -> str:
    """Human-readable host/db description with NO credentials."""
    try:
        u = urlparse(dsn)
        host = u.hostname or "?"
        port = u.port or 5432
        db = unquote((u.path or "/").lstrip("/")) or "?"
        return f"{host}:{port}/{db}"
    except Exception:
        return "<unparseable dsn>"


def connect(dsn: str):
    conn = psycopg2.connect(dsn)
    return conn


# --------------------------------------------------------------------------- #
# Migration bookkeeping
# --------------------------------------------------------------------------- #
def ensure_history_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    text PRIMARY KEY,
                name       text NOT NULL,
                checksum   text NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT now()
            );
            """
        )
    conn.commit()


def discover_migrations() -> list[pathlib.Path]:
    files = sorted(p for p in MIGRATIONS_DIR.glob(MIGRATION_GLOB) if p.is_file())
    if not files:
        raise SystemExit(f"ERROR: no migration files found in {MIGRATIONS_DIR}")
    return files


def checksum(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version_of(path: pathlib.Path) -> str:
    return path.name.split("_", 1)[0]


def applied_map(conn) -> dict[str, str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version, checksum FROM schema_migrations")
        return {v: c for v, c in cur.fetchall()}


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_apply(conn) -> int:
    ensure_history_table(conn)
    applied = applied_map(conn)
    pending = 0
    for path in discover_migrations():
        ver, name, cksum = version_of(path), path.name, checksum(path)
        if ver in applied:
            if applied[ver] != cksum:
                raise SystemExit(
                    f"ERROR: migration {name} was modified after being applied "
                    f"(recorded checksum != file checksum). Never edit an applied "
                    f"migration; add a new forward migration instead."
                )
            continue
        sql = path.read_text(encoding="utf-8")
        print(f"  applying {name} ...", flush=True)
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (version, name, checksum) "
                    "VALUES (%s, %s, %s)",
                    (ver, name, cksum),
                )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            raise SystemExit(f"ERROR: migration {name} failed and was rolled back:\n{exc}")
        pending += 1
    if pending == 0:
        print("  up to date — nothing to apply.")
    else:
        print(f"  applied {pending} migration(s).")
    return 0


def cmd_status(conn) -> int:
    ensure_history_table(conn)
    applied = applied_map(conn)
    for path in discover_migrations():
        ver = version_of(path)
        state = "applied" if ver in applied else "PENDING"
        print(f"  [{state:8}] {path.name}")
    return 0


def cmd_reset(conn) -> int:
    env = os.environ.get("APP_ENV", "").lower()
    if env not in ("development", "local", "test"):
        raise SystemExit(
            f"REFUSED: reset is destructive and only runs when APP_ENV is "
            f"development/local/test (got '{env or 'unset'}')."
        )
    with conn.cursor() as cur:
        cur.execute(
            """
            DROP SCHEMA IF EXISTS app CASCADE;
            DROP SCHEMA IF EXISTS public CASCADE;
            CREATE SCHEMA public;
            -- Drop the local auth shim only (Supabase-managed auth is never reset
            -- from here; on Supabase this schema is owned by the platform and the
            -- DROP will simply be skipped by permissions if attempted). We guard
            -- by only dropping when the shim table is our minimal one.
            """
        )
        cur.execute(
            """
            DO $$
            BEGIN
              IF to_regclass('auth.users') IS NOT NULL
                 AND (SELECT count(*) FROM information_schema.columns
                      WHERE table_schema='auth' AND table_name='users') <= 4 THEN
                DROP SCHEMA IF EXISTS auth CASCADE;
              END IF;
            END
            $$;
            """
        )
    conn.commit()
    print("  reset complete — schema dropped and recreated (development only).")
    return 0


def cmd_seed(conn) -> int:
    if not SEED_FILE.exists():
        raise SystemExit(f"ERROR: seed file not found: {SEED_FILE}")
    sql = SEED_FILE.read_text(encoding="utf-8")
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise SystemExit(f"ERROR: seed failed and was rolled back:\n{exc}")
    print("  reference/demo seed applied (idempotent).")
    return 0


def cmd_dump(dsn: str) -> int:
    DUMP_FILE.parent.mkdir(parents=True, exist_ok=True)
    pg_dump = os.environ.get("PG_DUMP", "pg_dump")
    # Keep GRANTs and RLS policies in the snapshot (security evidence); drop only
    # owner noise. The snapshot is schema DDL only and contains no credentials.
    cmd = [pg_dump, "--schema-only", "--no-owner", "--dbname", dsn, "-f", str(DUMP_FILE)]
    print(f"  dumping schema of {safe_target(dsn)} -> {DUMP_FILE.relative_to(REPO_ROOT)}")
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        raise SystemExit("ERROR: pg_dump not found on PATH (set PG_DUMP=/path/to/pg_dump).")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"ERROR: pg_dump failed (exit {exc.returncode}).")
    print("  schema dump written.")
    return 0


def cmd_verify() -> int:
    print("  running pytest schema/RLS/view suite ...", flush=True)
    return subprocess.call([sys.executable, "-m", "pytest", "-q", str(BACKEND_DIR / "tests")])


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main(argv: list[str]) -> int:
    _load_dotenv()
    command = (argv[0] if argv else "apply").lower()
    if command == "migrate":
        command = "apply"

    if command == "verify":
        return cmd_verify()

    if command == "dump":
        var, dsn, probe = open_connection()
        probe.close()
        print(f"target: {safe_target(dsn)} (via {var})")
        return cmd_dump(dsn)

    var, dsn, conn = open_connection()
    print(f"target: {safe_target(dsn)} (via {var})")
    try:
        if command == "apply":
            return cmd_apply(conn)
        if command == "status":
            return cmd_status(conn)
        if command == "reset":
            return cmd_reset(conn)
        if command == "seed":
            return cmd_seed(conn)
        raise SystemExit(
            f"ERROR: unknown command '{command}'. "
            f"Use: apply | migrate | reset | seed | verify | dump | status."
        )
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
