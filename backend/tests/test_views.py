"""Read-model / view behaviour (docs/schema.md §12)."""
from helpers import (
    ACCT_O1_BK, BKASH, OUTLET1, TS, TS2, new_alert, new_analytics_run, new_assessment,
    new_cash, new_case, new_pbs, new_projection, new_run,
)

VIEWS = [
    "v_latest_cash_balance", "v_latest_provider_balances", "v_current_feed_health",
    "v_latest_liquidity_projections", "v_outlet_dashboard", "v_case_timeline",
    "v_validation_summary",
]


def test_every_view_is_queryable(cur):
    for v in VIEWS:
        cur.execute(f"SELECT count(*) FROM {v}")
        assert cur.fetchone()[0] >= 0


def test_latest_cash_balance_is_deterministic(cur):
    run = new_run(cur)
    new_cash(cur, run, OUTLET1, balance="50000.00", observed_at=TS)
    new_cash(cur, run, OUTLET1, balance="90000.00", observed_at=TS2)  # newer
    cur.execute("SELECT balance FROM v_latest_cash_balance WHERE outlet_id=%s", (OUTLET1,))
    assert str(cur.fetchone()[0]) == "90000.00"


def test_provider_balances_view_never_sums(cur):
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='v_latest_provider_balances'")
    cols = {r[0] for r in cur.fetchall()}
    assert "outlet_provider_account_id" in cols and "provider_id" in cols
    assert not any("total" in c or "sum" in c for c in cols)


def test_dashboard_exposes_separated_reserves(cur):
    run = new_run(cur)
    new_cash(cur, run, OUTLET1, balance="85000.00", observed_at=TS)
    new_pbs(cur, run, ACCT_O1_BK, BKASH, OUTLET1, balance="42000.00", observed_at=TS)
    cur.execute(
        "SELECT shared_cash->>'balance', jsonb_array_length(providers), "
        "       jsonb_typeof(shared_cash), jsonb_typeof(providers) "
        "FROM v_outlet_dashboard WHERE outlet_id=%s",
        (OUTLET1,),
    )
    cash_balance, n_providers, cash_type, prov_type = cur.fetchone()
    assert cash_balance == "85000.00"
    assert cash_type == "object" and prov_type == "array"
    assert n_providers >= 1
    # ensure no blended total key appears anywhere in the row
    cur.execute("SELECT row_to_json(d)::text FROM v_outlet_dashboard d WHERE outlet_id=%s", (OUTLET1,))
    blob = cur.fetchone()[0].lower()
    assert "total_balance" not in blob and "blended" not in blob


def test_case_timeline_is_ordered(cur):
    run = new_run(cur)
    alert = new_alert(cur, run, OUTLET1, BKASH)
    assess = new_assessment(cur, run, OUTLET1, BKASH)
    cur.execute("INSERT INTO alert_quality_assessments (alert_id, data_quality_assessment_id) VALUES (%s,%s)",
                (alert, assess))
    case = new_case(cur, alert, OUTLET1, BKASH)
    cur.execute(
        "INSERT INTO case_notes (case_id, author_user_id, note_text, note_type) "
        "VALUES (%s,%s,'note','general')",
        (case, "d0000000-0000-0000-0000-000000000b01"),
    )
    cur.execute("SELECT event_at FROM v_case_timeline WHERE case_id=%s", (case,))
    rows = [r[0] for r in cur.fetchall()]
    assert rows == sorted(rows), "timeline events must be chronologically ordered"


def test_validation_summary_returns_completed_metrics(cur):
    cur.execute(
        "INSERT INTO validation_runs (name, dataset_split, engine_version, status, completed_at) "
        "VALUES ('vr','held_out','v1','completed', now()) RETURNING validation_run_id"
    )
    vr = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO metric_results (validation_run_id, metric_code, category, value, unit, "
        "sample_size, method, limitations) "
        "VALUES (%s,'anomaly_precision','analytics',0.9,'ratio',20,'holdout','small sample')",
        (vr,),
    )
    cur.execute("SELECT metric_code, sample_size, method, limitations FROM v_validation_summary "
                "WHERE metric_code='anomaly_precision'")
    row = cur.fetchone()
    assert row is not None and row[1] == 20 and row[2] == "holdout"
