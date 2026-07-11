"""Provider / reserve separation invariants (docs/schema.md §8, §9.4, §13)."""
from helpers import (
    ACCT_O1_BK, BKASH, NAGAD, OUTLET1, expect_error, new_analytics_run, new_event,
    new_batch, new_projection, new_run,
)


def test_cash_snapshot_has_no_provider_column(cur):
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='cash_balance_snapshots' AND column_name='provider_id'"
    )
    assert cur.fetchone() is None, "shared-cash snapshots must not carry a provider_id"


def test_shared_cash_projection_rejects_provider(cur):
    run = new_run(cur)
    ar = new_analytics_run(cur, run)
    # shared_cash with a provider set violates the reserve XOR constraint.
    with expect_error(cur, "lp_reserve_xor"):
        cur.execute(
            "INSERT INTO liquidity_projections (analytics_run_id, outlet_id, reserve_type, "
            "provider_id, as_of_at, current_balance, burn_rate_per_hour, confidence_score, "
            "confidence_level, sample_count, is_actionable) "
            "VALUES (%s,%s,'shared_cash',%s, now(), 100, -1, 0.5, 'low', 3, true)",
            (ar, OUTLET1, BKASH),
        )


def test_provider_projection_requires_provider_and_account(cur):
    run = new_run(cur)
    ar = new_analytics_run(cur, run)
    # A provider_e_money projection with NULL account/provider is rejected (either
    # by the reserve-XOR CHECK or the account-consistency trigger — both are valid).
    with expect_error(cur):
        cur.execute(
            "INSERT INTO liquidity_projections (analytics_run_id, outlet_id, reserve_type, "
            "as_of_at, current_balance, burn_rate_per_hour, confidence_score, "
            "confidence_level, sample_count, is_actionable) "
            "VALUES (%s,%s,'provider_e_money', now(), 100, -1, 0.5, 'low', 3, true)",
            (ar, OUTLET1),
        )


def test_provider_projection_cross_provider_mismatch_rejected(cur):
    run = new_run(cur)
    ar = new_analytics_run(cur, run)
    # account ACCT_O1_BK belongs to bKash, but provider_id says Nagad.
    with expect_error(cur, "do not match account"):
        new_projection(cur, ar, OUTLET1, reserve_type="provider_e_money",
                       account_id=ACCT_O1_BK, provider_id=NAGAD)


def test_transaction_denormalized_mismatch_rejected(cur):
    run = new_run(cur)
    batch = new_batch(cur, run, BKASH, OUTLET1)
    event = new_event(cur, batch)
    with expect_error(cur, "do not match account"):
        cur.execute(
            "INSERT INTO transactions (ingestion_event_id, simulation_run_id, "
            "outlet_provider_account_id, provider_id, outlet_id, synthetic_transaction_ref, "
            "synthetic_party_ref, transaction_type, status, amount, occurred_at, received_at) "
            "VALUES (%s,%s,%s,%s,%s,'T1','P','cash_out','completed',100, now(), now())",
            (event, run, ACCT_O1_BK, NAGAD, OUTLET1),  # NAGAD provider on a bKash account
        )


def test_provider_balance_mismatch_rejected(cur):
    run = new_run(cur)
    with expect_error(cur, "do not match account"):
        cur.execute(
            "INSERT INTO provider_balance_snapshots (simulation_run_id, "
            "outlet_provider_account_id, provider_id, outlet_id, balance, observed_at, "
            "received_at, source_kind) VALUES (%s,%s,%s,%s,100, now(), now(),'feed')",
            (run, ACCT_O1_BK, NAGAD, OUTLET1),
        )


def test_dashboard_separates_reserves_and_has_no_blended_total(cur):
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name='v_outlet_dashboard'"
    )
    cols = {r[0] for r in cur.fetchall()}
    assert {"shared_cash", "providers"} <= cols
    assert not any("total" in c for c in cols), "dashboard must not expose a blended total"


def test_no_total_balance_column_anywhere(cur):
    cur.execute(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND column_name IN ('total_balance','blended_balance','combined_balance')"
    )
    assert cur.fetchall() == [], "no blended monetary total column may exist"
