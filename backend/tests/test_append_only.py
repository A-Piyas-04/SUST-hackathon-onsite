"""Append-only / immutability invariants (docs/schema.md §3, §8, §10, §13)."""
from helpers import (
    ACCT_O1_BK, BKASH, OUTLET1, TS, expect_error, new_analytics_run, new_alert,
    new_assessment, new_cash, new_flag, new_pbs, new_run, new_txn,
)


def test_transactions_cannot_be_updated_or_deleted(cur):
    run = new_run(cur)
    txn = new_txn(cur, run, ACCT_O1_BK, BKASH, OUTLET1)
    with expect_error(cur, "append-only"):
        cur.execute("UPDATE transactions SET amount=1 WHERE transaction_id=%s", (txn,))
    with expect_error(cur, "append-only"):
        cur.execute("DELETE FROM transactions WHERE transaction_id=%s", (txn,))


def test_provider_balance_snapshots_immutable(cur):
    run = new_run(cur)
    pbs = new_pbs(cur, run, ACCT_O1_BK, BKASH, OUTLET1)
    with expect_error(cur, "append-only"):
        cur.execute("UPDATE provider_balance_snapshots SET balance=1 WHERE provider_balance_snapshot_id=%s", (pbs,))


def test_cash_snapshots_immutable(cur):
    run = new_run(cur)
    cash = new_cash(cur, run, OUTLET1)
    with expect_error(cur, "append-only"):
        cur.execute("DELETE FROM cash_balance_snapshots WHERE cash_balance_snapshot_id=%s", (cash,))


def test_audit_events_cannot_be_modified(cur):
    cur.execute(
        "INSERT INTO audit_events (actor_type, action) VALUES ('system','test') RETURNING audit_event_id"
    )
    aid = cur.fetchone()[0]
    with expect_error(cur, "append-only"):
        cur.execute("UPDATE audit_events SET action='x' WHERE audit_event_id=%s", (aid,))
    with expect_error(cur, "append-only"):
        cur.execute("DELETE FROM audit_events WHERE audit_event_id=%s", (aid,))


def test_anomaly_evidence_cannot_be_modified(cur):
    run = new_run(cur)
    ar = new_analytics_run(cur, run, "anomaly")
    assess = new_assessment(cur, run, OUTLET1, BKASH)
    flag = new_flag(cur, ar, OUTLET1, BKASH, ACCT_O1_BK, assess)
    cur.execute(
        "INSERT INTO anomaly_evidence_items (anomaly_flag_id, evidence_type, label, value) "
        "VALUES (%s,'count','n','{}') RETURNING anomaly_evidence_item_id",
        (flag,),
    )
    ev = cur.fetchone()[0]
    with expect_error(cur, "append-only"):
        cur.execute("UPDATE anomaly_evidence_items SET label='x' WHERE anomaly_evidence_item_id=%s", (ev,))


def test_published_alert_analytical_fields_immutable_but_state_mutable(cur):
    run = new_run(cur)
    alert = new_alert(cur, run, OUTLET1, BKASH)
    assess = new_assessment(cur, run, OUTLET1, BKASH)
    cur.execute("INSERT INTO alert_quality_assessments (alert_id, data_quality_assessment_id) VALUES (%s,%s)",
                (alert, assess))
    # analytical content is frozen
    with expect_error(cur, "immutable"):
        cur.execute("UPDATE alerts SET severity='low' WHERE alert_id=%s", (alert,))
    with expect_error(cur, "cannot be deleted"):
        cur.execute("DELETE FROM alerts WHERE alert_id=%s", (alert,))
    # lifecycle metadata may change
    cur.execute("UPDATE alerts SET state='closed' WHERE alert_id=%s", (alert,))
    cur.execute("SELECT state FROM alerts WHERE alert_id=%s", (alert,))
    assert cur.fetchone()[0] == "closed"


def test_conflicting_snapshots_coexist(cur):
    run = new_run(cur)
    # two snapshots for the same account at the same observed_at, different balances
    new_pbs(cur, run, ACCT_O1_BK, BKASH, OUTLET1, balance="42000.00", observed_at=TS)
    new_pbs(cur, run, ACCT_O1_BK, BKASH, OUTLET1, balance="17000.00", observed_at=TS)
    cur.execute(
        "SELECT count(*) FROM provider_balance_snapshots "
        "WHERE outlet_provider_account_id=%s AND observed_at=%s",
        (ACCT_O1_BK, TS),
    )
    assert cur.fetchone()[0] == 2, "conflicting snapshots must be preserved, not overwritten"
    cur.execute("SELECT is_conflicted, balance FROM v_latest_provider_balances WHERE outlet_provider_account_id=%s",
                (ACCT_O1_BK,))
    is_conflicted, balance = cur.fetchone()
    assert is_conflicted is True
    assert balance is None, "a conflicted feed must not silently expose one candidate as truth"


def test_rejected_ingestion_event_cannot_produce_ledger(cur):
    from helpers import new_batch, new_event
    run = new_run(cur)
    batch = new_batch(cur, run, BKASH, OUTLET1)
    bad_event = new_event(cur, batch, status="rejected")
    with expect_error(cur, "rejected ingestion"):
        cur.execute(
            "INSERT INTO transactions (ingestion_event_id, simulation_run_id, "
            "outlet_provider_account_id, provider_id, outlet_id, synthetic_transaction_ref, "
            "synthetic_party_ref, transaction_type, status, amount, occurred_at, received_at) "
            "VALUES (%s,%s,%s,%s,%s,'TR','P','cash_out','completed',100, now(), now())",
            (bad_event, run, ACCT_O1_BK, BKASH, OUTLET1),
        )
