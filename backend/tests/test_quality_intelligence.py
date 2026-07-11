"""Quality / intelligence integrity constraints (docs/schema.md §9, §13)."""
from helpers import (
    ACCT_O1_BK, ACCT_O1_NG, BKASH, NAGAD, OUTLET1, expect_error, new_analytics_run,
    new_alert, new_assessment, new_flag, new_projection, new_run, new_txn,
)


def test_invalid_quality_status_rejected(cur):
    run = new_run(cur)
    with expect_error(cur):
        cur.execute(
            "INSERT INTO data_quality_assessments (simulation_run_id, outlet_id, provider_id, "
            "status, confidence_modifier, sample_count, assessed_at, engine_version) "
            "VALUES (%s,%s,%s,'bogus',1.0,1, now(),'v1')",
            (run, OUTLET1, BKASH),
        )


def test_confidence_out_of_range_rejected(cur):
    run = new_run(cur)
    with expect_error(cur):
        cur.execute(
            "INSERT INTO data_quality_assessments (simulation_run_id, outlet_id, provider_id, "
            "status, confidence_modifier, sample_count, assessed_at, engine_version) "
            "VALUES (%s,%s,%s,'fresh',1.5,1, now(),'v1')",
            (run, OUTLET1, BKASH),
        )


def test_negative_sample_count_rejected(cur):
    run = new_run(cur)
    with expect_error(cur):
        cur.execute(
            "INSERT INTO data_quality_assessments (simulation_run_id, outlet_id, provider_id, "
            "status, confidence_modifier, sample_count, assessed_at, engine_version) "
            "VALUES (%s,%s,%s,'fresh',1.0,-1, now(),'v1')",
            (run, OUTLET1, BKASH),
        )


def test_actionable_flag_requires_benign_context(cur):
    run = new_run(cur)
    ar = new_analytics_run(cur, run, "anomaly")
    assess = new_assessment(cur, run, OUTLET1, BKASH)
    with expect_error(cur, "af_actionable_needs_benign"):
        new_flag(cur, ar, OUTLET1, BKASH, ACCT_O1_BK, assess,
                 disposition="requires_review", benign=None)


def test_suppressed_flag_requires_suppression_reason(cur):
    run = new_run(cur)
    ar = new_analytics_run(cur, run, "anomaly")
    assess = new_assessment(cur, run, OUTLET1, BKASH, status="stale")
    with expect_error(cur, "af_suppressed_needs_reason"):
        new_flag(cur, ar, OUTLET1, BKASH, ACCT_O1_BK, assess,
                 disposition="suppressed_data_quality", benign=None, suppression=None)


def test_nonpositive_burn_cannot_have_shortage(cur):
    run = new_run(cur)
    ar = new_analytics_run(cur, run)
    with expect_error(cur, "lp_nonpositive_burn_no_shortage"):
        new_projection(cur, ar, OUTLET1, reserve_type="provider_e_money",
                       account_id=ACCT_O1_BK, provider_id=BKASH,
                       burn="0.0000", shortage_at="2026-07-11T10:00:00Z")


def test_provider_crossing_evidence_rejected(cur):
    run = new_run(cur)
    ar = new_analytics_run(cur, run, "anomaly")
    assess = new_assessment(cur, run, OUTLET1, BKASH)
    flag = new_flag(cur, ar, OUTLET1, BKASH, ACCT_O1_BK, assess)   # bKash flag
    nagad_txn = new_txn(cur, run, ACCT_O1_NG, NAGAD, OUTLET1)      # Nagad transaction
    with expect_error(cur, "provider-crossing"):
        cur.execute(
            "INSERT INTO anomaly_flag_transactions (anomaly_flag_id, transaction_id) VALUES (%s,%s)",
            (flag, nagad_txn),
        )


def test_suppressed_flag_cannot_back_anomaly_alert(cur):
    run = new_run(cur)
    ar = new_analytics_run(cur, run, "anomaly")
    assess = new_assessment(cur, run, OUTLET1, BKASH, status="stale")
    supp = new_flag(cur, ar, OUTLET1, BKASH, ACCT_O1_BK, assess,
                    disposition="suppressed_data_quality", benign=None,
                    suppression="stale feed")
    alert = new_alert(cur, run, OUTLET1, BKASH, alert_type="anomaly")
    with expect_error(cur, "suppressed"):
        cur.execute(
            "INSERT INTO alert_anomaly_flags (alert_id, anomaly_flag_id) VALUES (%s,%s)",
            (alert, supp),
        )
