"""Print sanitized lock blockers relevant to the moderate dataset loader."""
from __future__ import annotations

import argparse

from migrations.run_migrations import _load_dotenv, open_connection, safe_target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--terminate-stale-moderate-pid', type=int)
    args = parser.parse_args()
    _load_dotenv()
    label, dsn, conn = open_connection()
    conn.autocommit = True
    if args.terminate_stale_moderate_pid:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT state, now() - xact_start, query
                FROM pg_stat_activity
                WHERE pid = %s AND usename = current_user
                """,
                (args.terminate_stale_moderate_pid,),
            )
            row = cur.fetchone()
            allowed_tables = (
                'areas', 'outlets', 'outlet_provider_accounts', 'simulation_runs',
                'fault_injections', 'ingestion_batches', 'ingestion_events',
                'transactions', 'cash_balance_snapshots', 'provider_balance_snapshots',
            )
            if not row:
                raise SystemExit('REFUSED: target PID no longer exists for the current database user')
            state, age, query = row
            looks_like_loader = query.lstrip().upper().startswith('INSERT INTO') and any(
                f'"{table}"' in query for table in allowed_tables
            )
            if state != 'idle in transaction' or age.total_seconds() < 300 or not looks_like_loader:
                raise SystemExit(
                    f'REFUSED: PID does not match a stale moderate-loader transaction '
                    f'(state={state}, age={age}, loader_query={looks_like_loader})'
                )
            cur.execute('SELECT pg_terminate_backend(%s)', (args.terminate_stale_moderate_pid,))
            if not cur.fetchone()[0]:
                raise SystemExit('Termination request was not accepted')
            print(f'Terminated stale moderate-loader PID {args.terminate_stale_moderate_pid}; its transaction was rolled back.')
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.pid, a.usename, a.application_name, a.state,
                   a.xact_start, a.query_start,
                   now() - a.xact_start AS transaction_age,
                   pg_blocking_pids(a.pid) AS blocked_by,
                   left(regexp_replace(a.query, E'[\\n\\r\\t]+', ' ', 'g'), 180) AS query_excerpt
            FROM pg_stat_activity a
            WHERE a.datname = current_database()
              AND a.pid <> pg_backend_pid()
              AND (a.state <> 'idle' OR cardinality(pg_blocking_pids(a.pid)) > 0)
            ORDER BY a.xact_start NULLS LAST, a.query_start
            """
        )
        rows = cur.fetchall()
    conn.close()
    print(f"target: {safe_target(dsn)} (via {label})")
    if not rows:
        print("No non-idle or blocked sessions found.")
        return
    for pid, user, app, state, xact, query_start, age, blocked_by, query in rows:
        print(
            f"pid={pid} user={user} app={app or '<unset>'} state={state} "
            f"xact_start={xact} age={age} blocked_by={blocked_by} "
            f"query_start={query_start} query={query}"
        )


if __name__ == '__main__':
    main()
