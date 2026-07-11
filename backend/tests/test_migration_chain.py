"""Migration-chain, object-existence, and idempotency tests."""
import os
import pathlib
import subprocess
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
RUNNER = BACKEND_DIR / "migrations" / "run_migrations.py"

REQUIRED_TABLES = {
    "areas", "providers", "outlets", "outlet_provider_accounts", "app_users",
    "user_access_scopes", "simulation_scenarios", "simulation_runs", "fault_injections",
    "ingestion_batches", "ingestion_events", "transactions", "cash_balance_snapshots",
    "provider_balance_snapshots", "data_quality_assessments", "data_quality_issues",
    "analytics_runs", "liquidity_projections", "liquidity_projection_quality_assessments",
    "liquidity_signals", "anomaly_rules", "anomaly_flags", "anomaly_evidence_items",
    "anomaly_flag_transactions", "alerts", "alert_liquidity_projections",
    "alert_anomaly_flags", "alert_quality_assessments", "explanation_templates",
    "alert_explanations", "routing_rules", "cases", "case_assignments",
    "case_status_history", "case_notes", "notifications", "case_reviews", "audit_events",
    "validation_runs", "ground_truth_labels", "metric_results", "schema_migrations",
    "coordination_idempotency_keys",
}

REQUIRED_VIEWS = {
    "v_latest_cash_balance", "v_latest_provider_balances", "v_current_feed_health",
    "v_latest_liquidity_projections", "v_outlet_dashboard", "v_case_timeline",
    "v_validation_summary",
}

REQUIRED_INDEXES = {
    "ix_txn_outlet_provider_time", "ix_txn_provider_party_time", "ix_cash_outlet_time",
    "ix_pbs_account_time", "ix_batch_outlet_provider_time", "ix_dqa_outlet_provider_time",
    "ix_lp_outlet_reserve_time", "ix_af_outlet_provider_time", "ix_alerts_queue",
    "ix_cases_provider_status", "ix_cases_outlet_status", "ix_notifications_recipient",
    "ix_audit_case_time", "uq_alerts_active_dedup",
}

REQUIRED_APP_FUNCS = {
    "current_user_id", "has_provider_scope", "has_outlet_scope", "has_case_access",
    "has_alert_access", "has_flag_access", "has_projection_access", "has_assessment_access",
    "has_batch_access",
}


def test_required_tables_exist(cur):
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    present = {r[0] for r in cur.fetchall()}
    missing = REQUIRED_TABLES - present
    assert not missing, f"missing tables: {sorted(missing)}"


def test_required_views_exist(cur):
    cur.execute("SELECT viewname FROM pg_views WHERE schemaname='public'")
    present = {r[0] for r in cur.fetchall()}
    assert REQUIRED_VIEWS <= present, f"missing views: {sorted(REQUIRED_VIEWS - present)}"


def test_required_indexes_exist(cur):
    cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname='public'")
    present = {r[0] for r in cur.fetchall()}
    missing = REQUIRED_INDEXES - present
    assert not missing, f"missing indexes: {sorted(missing)}"


def test_app_helper_functions_exist(cur):
    cur.execute(
        "SELECT p.proname FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
        "WHERE n.nspname='app'"
    )
    present = {r[0] for r in cur.fetchall()}
    assert REQUIRED_APP_FUNCS <= present, f"missing app funcs: {sorted(REQUIRED_APP_FUNCS - present)}"


def test_append_only_triggers_exist(cur):
    cur.execute(
        "SELECT c.relname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
        "JOIN pg_proc p ON p.oid=t.tgfoid WHERE p.proname='reject_mutation'"
    )
    guarded = {r[0] for r in cur.fetchall()}
    for tbl in ("transactions", "cash_balance_snapshots", "provider_balance_snapshots",
                "anomaly_evidence_items", "audit_events", "case_notes", "alert_explanations"):
        assert tbl in guarded, f"{tbl} missing append-only guard"


def test_rls_enabled_on_confidential_tables(cur):
    cur.execute(
        "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname='public' AND c.relrowsecurity"
    )
    rls = {r[0] for r in cur.fetchall()}
    for tbl in ("transactions", "provider_balance_snapshots", "alerts", "cases",
                "cash_balance_snapshots", "audit_events", "notifications"):
        assert tbl in rls, f"RLS not enabled on {tbl}"


def test_migration_history_recorded(cur):
    cur.execute("SELECT version, checksum FROM schema_migrations ORDER BY version")
    rows = cur.fetchall()
    versions = [r[0] for r in rows]
    assert versions == ["001", "002", "003", "004", "005", "006", "007", "008", "009"], versions
    assert all(len(r[1]) == 64 for r in rows), "checksums must be sha256 hex"


def test_reapply_is_idempotent(cur):
    cur.execute("SELECT count(*) FROM schema_migrations")
    before = cur.fetchone()[0]
    env = {**os.environ, "APP_ENV": "test"}
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "apply"],
        capture_output=True, text=True, env=env, cwd=str(BACKEND_DIR),
    )
    assert proc.returncode == 0, proc.stderr
    assert "nothing to apply" in proc.stdout.lower()
    cur.execute("SELECT count(*) FROM schema_migrations")
    assert cur.fetchone()[0] == before == 9
