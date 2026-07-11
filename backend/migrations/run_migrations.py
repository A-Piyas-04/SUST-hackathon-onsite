#!/usr/bin/env python3
"""Tiny numbered-SQL migration runner.

Owner: Member 1. Applies migrations/*.sql in numeric filename order against
MIGRATIONS_DATABASE_URL (plain psycopg2 connection string — kept separate from
the app's async SQLAlchemy DATABASE_URL so this script has zero dependency on
the FastAPI app package and can run standalone). Applied filenames are tracked
in a `schema_migrations` table so re-runs are idempotent.

Usage:
    python migrations/run_migrations.py            # apply all pending migrations
    python migrations/run_migrations.py --check     # list pending migrations only, apply nothing
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import psycopg2

MIGRATIONS_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/liquidity_platform"


def load_dotenv_if_present() -> None:
    """Minimal .env loader so this script works without importing the app package."""
    env_path = MIGRATIONS_DIR.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def get_database_url() -> str:
    return os.environ.get("MIGRATIONS_DATABASE_URL", DEFAULT_DATABASE_URL)


def discover_migration_files() -> list[Path]:
    """Numbered *.sql files in this directory, sorted by their numeric prefix."""
    files = sorted(
        p for p in MIGRATIONS_DIR.glob("*.sql") if p.stem[:3].isdigit()
    )
    return files


def ensure_tracking_table(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename    text PRIMARY KEY,
            applied_at  timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def get_applied_filenames(cur) -> set[str]:
    cur.execute("SELECT filename FROM schema_migrations")
    return {row[0] for row in cur.fetchall()}


def is_reserved_placeholder(sql_text: str) -> bool:
    """004_coordination.sql / 006_security.sql are single-line reserved
    placeholders owned by Member 2 — apply-as-a-no-op rather than skipping,
    so schema_migrations still records that the numbering slot was reviewed,
    without creating any Member 2 tables/objects."""
    meaningful_lines = [
        line for line in sql_text.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    return len(meaningful_lines) == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="List pending migrations without applying them.",
    )
    args = parser.parse_args()

    load_dotenv_if_present()
    database_url = get_database_url()

    migration_files = discover_migration_files()
    if not migration_files:
        print("No migration files found in", MIGRATIONS_DIR)
        return 1

    try:
        conn = psycopg2.connect(database_url)
    except psycopg2.OperationalError as exc:
        print(f"Failed to connect to database at {database_url!r}: {exc}", file=sys.stderr)
        return 1

    conn.autocommit = False
    try:
        with conn:
            with conn.cursor() as cur:
                ensure_tracking_table(cur)
                conn.commit()

            with conn.cursor() as cur:
                applied = get_applied_filenames(cur)

            pending = [f for f in migration_files if f.name not in applied]

            if not pending:
                print("No pending migrations. Database is up to date.")
                return 0

            print(f"Pending migrations ({len(pending)}):")
            for f in pending:
                print(f"  - {f.name}")

            if args.check:
                return 0

            for migration_file in pending:
                print(f"Applying {migration_file.name} ...", end=" ", flush=True)
                sql_text = migration_file.read_text(encoding="utf-8")
                with conn.cursor() as cur:
                    try:
                        if sql_text.strip() and not is_reserved_placeholder(sql_text):
                            cur.execute(sql_text)
                        cur.execute(
                            "INSERT INTO schema_migrations (filename) VALUES (%s)",
                            (migration_file.name,),
                        )
                        conn.commit()
                        print("OK" + (" (reserved placeholder)" if is_reserved_placeholder(sql_text) else ""))
                    except Exception as exc:  # noqa: BLE001
                        conn.rollback()
                        print("FAILED")
                        print(f"Error applying {migration_file.name}: {exc}", file=sys.stderr)
                        return 1

            print("All pending migrations applied successfully.")
            return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
