"""Shared constants and row-builder helpers for the Phase 1 schema tests.

Builders insert synthetic rows (as the connecting superuser) and return the new
id via RETURNING. Tests wrap everything in a transaction that is rolled back, so
nothing persists between tests.
"""
from __future__ import annotations

import contextlib

# --- Seeded reference ids (see backend/seeds/reference_seed.sql) --------------
BKASH = "11111111-1111-1111-1111-111111111111"
NAGAD = "22222222-2222-2222-2222-222222222222"
ROCKET = "33333333-3333-3333-3333-333333333333"

OUTLET1 = "0b000000-0000-0000-0000-000000000001"
OUTLET2 = "0b000000-0000-0000-0000-000000000002"

ACCT_O1_BK = "e1000000-0000-0000-0000-000000000001"
ACCT_O1_NG = "e2000000-0000-0000-0000-000000000001"
ACCT_O1_RK = "e3000000-0000-0000-0000-000000000001"
ACCT_O2_BK = "e1000000-0000-0000-0000-000000000002"

AREA_MARKET = "a0000000-0000-0000-0000-000000000003"
AREA_RIVER = "a0000000-0000-0000-0000-000000000004"

SCENARIO_NORMAL = "5c000000-0000-0000-0000-000000000000"
RULE_NIA = "a9000000-0000-0000-0000-000000000001"

# demo users
AGENT1 = "d0000000-0000-0000-0000-000000000a01"
AGENT2 = "d0000000-0000-0000-0000-000000000a02"
BKASH_OPS = "d0000000-0000-0000-0000-000000000b01"
NAGAD_OPS = "d0000000-0000-0000-0000-000000000b02"
ROCKET_OPS = "d0000000-0000-0000-0000-000000000b03"
AREA_MGR = "d0000000-0000-0000-0000-000000000c01"
RISK_BK = "d0000000-0000-0000-0000-000000000d01"
MGMT = "d0000000-0000-0000-0000-000000000e01"
ADMIN = "d0000000-0000-0000-0000-000000000f01"

TS = "2026-07-11T08:00:00Z"
TS2 = "2026-07-11T08:05:00Z"


def scalar(cur, sql, params=()):
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


# --- builders ----------------------------------------------------------------
def new_run(cur, scenario_id=SCENARIO_NORMAL, seed=1001):
    return scalar(
        cur,
        "INSERT INTO simulation_runs (scenario_id, seed, config_snapshot) "
        "VALUES (%s,%s,'{}') RETURNING simulation_run_id",
        (scenario_id, seed),
    )


def new_batch(cur, run_id, provider_id, outlet_id, status="normalized", ref=None):
    ref = ref or f"BATCH-{provider_id[:4]}-{outlet_id[-4:]}-{status}"
    return scalar(
        cur,
        "INSERT INTO ingestion_batches (simulation_run_id, outlet_id, provider_id, "
        "source_batch_ref, received_at, normalization_status) "
        "VALUES (%s,%s,%s,%s, now(), %s) RETURNING ingestion_batch_id",
        (run_id, outlet_id, provider_id, ref, status),
    )


_ev_counter = {"n": 0}


def new_event(cur, batch_id, status="normalized", etype="transaction", ref=None):
    _ev_counter["n"] += 1
    ref = ref or f"EV-{_ev_counter['n']}"
    return scalar(
        cur,
        "INSERT INTO ingestion_events (ingestion_batch_id, event_type, source_event_ref, "
        "received_at, normalization_status) VALUES (%s,%s,%s, now(), %s) "
        "RETURNING ingestion_event_id",
        (batch_id, etype, ref, status),
    )


def new_txn(cur, run_id, account_id, provider_id, outlet_id, *, event_id=None,
            amount="1000.00", txn_type="cash_out", status="completed", ref=None):
    if event_id is None:
        batch = new_batch(cur, run_id, provider_id, outlet_id)
        event_id = new_event(cur, batch)
    _ev_counter["n"] += 1
    ref = ref or f"TXN-{_ev_counter['n']}"
    return scalar(
        cur,
        "INSERT INTO transactions (ingestion_event_id, simulation_run_id, "
        "outlet_provider_account_id, provider_id, outlet_id, synthetic_transaction_ref, "
        "synthetic_party_ref, transaction_type, status, amount, occurred_at, received_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now(), now()) RETURNING transaction_id",
        (event_id, run_id, account_id, provider_id, outlet_id, ref, "PARTY-X",
         txn_type, status, amount),
    )


def new_pbs(cur, run_id, account_id, provider_id, outlet_id, balance="42000.00",
            observed_at=TS, source_kind="feed"):
    return scalar(
        cur,
        "INSERT INTO provider_balance_snapshots (simulation_run_id, "
        "outlet_provider_account_id, provider_id, outlet_id, balance, observed_at, "
        "received_at, source_kind) VALUES (%s,%s,%s,%s,%s,%s, now(), %s) "
        "RETURNING provider_balance_snapshot_id",
        (run_id, account_id, provider_id, outlet_id, balance, observed_at, source_kind),
    )


def new_cash(cur, run_id, outlet_id, balance="85000.00", observed_at=TS, source_kind="feed"):
    return scalar(
        cur,
        "INSERT INTO cash_balance_snapshots (simulation_run_id, outlet_id, balance, "
        "observed_at, received_at, source_kind) VALUES (%s,%s,%s,%s, now(), %s) "
        "RETURNING cash_balance_snapshot_id",
        (run_id, outlet_id, balance, observed_at, source_kind),
    )


def new_assessment(cur, run_id, outlet_id, provider_id, status="fresh",
                   confidence="1.0000", samples=10):
    return scalar(
        cur,
        "INSERT INTO data_quality_assessments (simulation_run_id, outlet_id, provider_id, "
        "status, confidence_modifier, sample_count, assessed_at, engine_version) "
        "VALUES (%s,%s,%s,%s,%s,%s, now(), 'dq-1') RETURNING data_quality_assessment_id",
        (run_id, outlet_id, provider_id, status, confidence, samples),
    )


def new_analytics_run(cur, run_id, engine="liquidity"):
    return scalar(
        cur,
        "INSERT INTO analytics_runs (simulation_run_id, engine, engine_version, "
        "input_window_start, input_window_end) VALUES (%s,%s,'v1', now()-interval '1 hour', now()) "
        "RETURNING analytics_run_id",
        (run_id, engine),
    )


def new_projection(cur, analytics_run_id, outlet_id, reserve_type="provider_e_money",
                   account_id=ACCT_O1_BK, provider_id=BKASH, balance="42000.00",
                   burn="-100.0000", shortage_at=None, confidence="0.8000",
                   level="high", samples=10, actionable=True, reason=None,
                   assessment_id=None):
    if reserve_type == "shared_cash":
        account_id, provider_id = None, None
    return scalar(
        cur,
        "INSERT INTO liquidity_projections (analytics_run_id, outlet_id, reserve_type, "
        "outlet_provider_account_id, provider_id, primary_data_quality_assessment_id, "
        "as_of_at, current_balance, burn_rate_per_hour, projected_shortage_at, "
        "confidence_score, confidence_level, sample_count, is_actionable, non_actionable_reason) "
        "VALUES (%s,%s,%s,%s,%s,%s, now(), %s,%s,%s,%s,%s,%s,%s,%s) "
        "RETURNING liquidity_projection_id",
        (analytics_run_id, outlet_id, reserve_type, account_id, provider_id, assessment_id,
         balance, burn, shortage_at, confidence, level, samples, actionable, reason),
    )


def new_flag(cur, analytics_run_id, outlet_id, provider_id, account_id, assessment_id,
             disposition="requires_review", benign="May reflect normal demand.",
             suppression=None, confidence="0.7000", level="medium"):
    return scalar(
        cur,
        "INSERT INTO anomaly_flags (analytics_run_id, anomaly_rule_id, outlet_id, provider_id, "
        "outlet_provider_account_id, data_quality_assessment_id, window_start, window_end, "
        "confidence_score, confidence_level, disposition, reason_code, evidence_summary, "
        "plausible_benign_explanation, suppression_reason) "
        "VALUES (%s,%s,%s,%s,%s,%s, now()-interval '15 min', now(), %s,%s,%s,'near_identical', "
        "'5 near-identical amounts', %s, %s) RETURNING anomaly_flag_id",
        (analytics_run_id, RULE_NIA, outlet_id, provider_id, account_id, assessment_id,
         confidence, level, disposition, benign, suppression),
    )


def new_alert(cur, run_id, outlet_id, provider_id=BKASH, alert_type="combined",
              severity="high", requires_case=True, dedup=None, state="active"):
    dedup = dedup or f"dedup-{outlet_id[-4:]}-{alert_type}-{severity}"
    return scalar(
        cur,
        "INSERT INTO alerts (simulation_run_id, outlet_id, provider_id, alert_type, severity, "
        "state, deduplication_key, title_key, requires_case, detected_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,'alert.title', %s, now()) RETURNING alert_id",
        (run_id, outlet_id, provider_id, alert_type, severity, state, dedup, requires_case),
    )


def link_alert_flag(cur, alert_id, flag_id):
    cur.execute(
        "INSERT INTO alert_anomaly_flags (alert_id, anomaly_flag_id) VALUES (%s,%s)",
        (alert_id, flag_id),
    )


def link_alert_projection(cur, alert_id, projection_id):
    cur.execute(
        "INSERT INTO alert_liquidity_projections (alert_id, liquidity_projection_id) VALUES (%s,%s)",
        (alert_id, projection_id),
    )


def link_alert_assessment(cur, alert_id, assessment_id):
    cur.execute(
        "INSERT INTO alert_quality_assessments (alert_id, data_quality_assessment_id) VALUES (%s,%s)",
        (alert_id, assessment_id),
    )


def new_case(cur, alert_id, outlet_id, provider_id=BKASH, status="open",
             owner_role="provider_ops", next_step="Review the transactions.",
             number=None, resolution=None, resolved=False):
    number = number or f"CASE-{alert_id[:8]}"
    cur.execute(
        "INSERT INTO cases (case_number, alert_id, outlet_id, provider_id, status, "
        "current_owner_role, recommended_next_step, resolution_summary, resolved_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s, %s) RETURNING case_id",
        (number, alert_id, outlet_id, provider_id, status, owner_role, next_step,
         resolution, "now()" if resolved else None),
    )
    return cur.fetchone()[0]


@contextlib.contextmanager
def expect_error(cur, match=None):
    """Assert the wrapped statements raise a database error (savepoint-isolated)."""
    cur.execute("SAVEPOINT ee")
    failed = False
    try:
        yield
    except Exception as exc:  # noqa: BLE001 - any DB error is acceptable
        failed = True
        cur.execute("ROLLBACK TO SAVEPOINT ee")
        if match and match.lower() not in str(exc).lower():
            raise AssertionError(f"error {str(exc)!r} did not contain {match!r}")
    if not failed:
        cur.execute("ROLLBACK TO SAVEPOINT ee")
        raise AssertionError("expected a database error but the statement succeeded")


@contextlib.contextmanager
def as_role(conn, user_id, role="authenticated"):
    """Run queries as a Supabase-style authenticated user via a savepoint.

    Rolls back the savepoint on exit so the SET LOCAL ROLE / claims and any
    writes are undone, while fixture rows created before the savepoint remain.
    """
    cur = conn.cursor()
    cur.execute("SAVEPOINT rls_probe")
    cur.execute(f"SET LOCAL ROLE {role}")
    cur.execute("SELECT set_config('request.jwt.claims', %s, true)",
                (f'{{"sub":"{user_id}","role":"{role}"}}',))
    try:
        yield cur
    finally:
        cur.execute("ROLLBACK TO SAVEPOINT rls_probe")
        cur.close()
