#!/usr/bin/env python3
"""One-time idempotent demo seed: one outlet, three provider accounts, a
baseline "normal" simulation run, and calm/stable balances + projections so
GET /api/v1/outlets/{outletId}/dashboard shows real (not hardcoded-in-Python)
data immediately after `python migrations/run_migrations.py`.

Owner: Member 1. This is demo fixture data, not a real Member 3 simulator —
kept as a separate script (not a numbered migration) so schema DDL and demo
data stay cleanly separated. Safe to re-run (idempotent on synthetic_code).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/liquidity_platform"

DEMO_OUTLET_CODE = "OUTLET-001"


def load_dotenv_if_present() -> None:
    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    load_dotenv_if_present()
    database_url = os.environ.get("MIGRATIONS_DATABASE_URL", DEFAULT_DATABASE_URL)
    conn = psycopg2.connect(database_url)
    conn.autocommit = False

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT outlet_id FROM outlets WHERE synthetic_code = %s", (DEMO_OUTLET_CODE,))
            row = cur.fetchone()
            if row:
                print(f"Demo outlet {DEMO_OUTLET_CODE} already seeded (outlet_id={row['outlet_id']}). Nothing to do.")
                return 0

            cur.execute(
                """
                INSERT INTO areas (code, name, level)
                VALUES ('dhanmondi', 'Dhanmondi', 'thana')
                ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
                RETURNING area_id
                """
            )
            area_id = cur.fetchone()["area_id"]

            cur.execute(
                """
                INSERT INTO outlets (synthetic_code, display_name, area_id)
                VALUES (%s, 'Demo Market Outlet', %s)
                RETURNING outlet_id
                """,
                (DEMO_OUTLET_CODE, area_id),
            )
            outlet_id = cur.fetchone()["outlet_id"]

            cur.execute("SELECT provider_id, code FROM providers ORDER BY code")
            providers = {r["code"]: r["provider_id"] for r in cur.fetchall()}

            provider_accounts: dict[str, str] = {}
            starting_balances = {"bkash": "12000.00", "nagad": "38000.00", "rocket": "21000.00"}
            for code, provider_id in providers.items():
                cur.execute(
                    """
                    INSERT INTO outlet_provider_accounts (outlet_id, provider_id, synthetic_account_ref)
                    VALUES (%s, %s, %s)
                    RETURNING outlet_provider_account_id
                    """,
                    (outlet_id, provider_id, f"SYN-{code.upper()}-001"),
                )
                provider_accounts[code] = cur.fetchone()["outlet_provider_account_id"]

            cur.execute(
                """
                INSERT INTO simulation_scenarios (code, name, description, default_seed, default_config, validation_split)
                VALUES ('normal', 'Normal operation', 'Baseline calm state used to seed the demo dashboard before any scenario is triggered.', 42, '{}'::jsonb, 'demo')
                ON CONFLICT (code) DO NOTHING
                RETURNING scenario_id
                """
            )
            row = cur.fetchone()
            if row is None:
                cur.execute("SELECT scenario_id FROM simulation_scenarios WHERE code = 'normal'")
                row = cur.fetchone()
            scenario_id = row["scenario_id"]

            cur.execute(
                """
                INSERT INTO simulation_runs (scenario_id, seed, config_snapshot, status, started_at, completed_at)
                VALUES (%s, 42, '{}'::jsonb, 'completed', now(), now())
                RETURNING simulation_run_id
                """,
                (scenario_id,),
            )
            simulation_run_id = cur.fetchone()["simulation_run_id"]

            # Shared cash — seeded directly (source_kind='seed'), matching the
            # 002_simulation_and_ledger.sql decision record.
            cur.execute(
                """
                INSERT INTO cash_balance_snapshots (simulation_run_id, outlet_id, balance, observed_at, source_kind)
                VALUES (%s, %s, 45000.00, now(), 'seed')
                """,
                (simulation_run_id, outlet_id),
            )

            for code, balance in starting_balances.items():
                cur.execute(
                    """
                    INSERT INTO provider_balance_snapshots
                        (simulation_run_id, outlet_provider_account_id, provider_id, outlet_id, balance, observed_at, source_kind)
                    VALUES (%s, %s, %s, %s, %s, now(), 'seed')
                    """,
                    (simulation_run_id, provider_accounts[code], providers[code], outlet_id, balance),
                )

                cur.execute(
                    """
                    INSERT INTO data_quality_assessments
                        (simulation_run_id, outlet_id, provider_id, status, confidence_modifier, sample_count, latest_source_at, assessed_at, engine_version, summary)
                    VALUES (%s, %s, %s, 'fresh', 1.0, 10, now(), now(), 'seed-0.1', 'Feed is fresh; no data-quality issues observed.')
                    """,
                    (simulation_run_id, outlet_id, providers[code]),
                )

            cur.execute(
                """
                INSERT INTO analytics_runs (simulation_run_id, engine, engine_version, configuration, input_window_start, input_window_end, status, completed_at)
                VALUES (%s, 'liquidity', 'seed-0.1', '{}'::jsonb, now() - interval '30 minutes', now(), 'completed', now())
                RETURNING analytics_run_id
                """,
                (simulation_run_id,),
            )
            analytics_run_id = cur.fetchone()["analytics_run_id"]

            cur.execute(
                """
                INSERT INTO liquidity_projections
                    (analytics_run_id, outlet_id, reserve_type, as_of_at, current_balance, burn_rate_per_hour,
                     confidence_score, confidence_level, sample_count, is_actionable, non_actionable_reason)
                VALUES (%s, %s, 'shared_cash', now(), 45000.00, 0, 0.9000, 'high', 12, false, 'Shared cash balance is flat/replenishing; no shortage currently projected.')
                """,
                (analytics_run_id, outlet_id),
            )

            for code, balance in starting_balances.items():
                cur.execute(
                    """
                    INSERT INTO liquidity_projections
                        (analytics_run_id, outlet_id, reserve_type, outlet_provider_account_id, provider_id, as_of_at,
                         current_balance, burn_rate_per_hour, confidence_score, confidence_level, sample_count,
                         is_actionable, non_actionable_reason)
                    VALUES (%s, %s, 'provider_e_money', %s, %s, now(), %s, 0, 0.9000, 'high', 12, false,
                            'Balance is flat/replenishing; no shortage currently projected.')
                    """,
                    (analytics_run_id, outlet_id, provider_accounts[code], providers[code], balance),
                )

        conn.commit()
        print(f"Seeded demo outlet {DEMO_OUTLET_CODE} (outlet_id={outlet_id}) with calm baseline balances.")
        return 0
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(f"Seed failed: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
