"""Row Level Security provider/outlet/area isolation (docs/schema.md §15, §13.16)."""
from helpers import (
    ACCT_O1_BK, ACCT_O1_NG, ACCT_O2_BK, AGENT1, AREA_MGR, BKASH, BKASH_OPS, MGMT,
    NAGAD, NAGAD_OPS, OUTLET1, OUTLET2, ROCKET_OPS, as_role, new_pbs, new_run,
)


def _seed_snapshots(cur):
    run = new_run(cur)
    new_pbs(cur, run, ACCT_O1_BK, BKASH, OUTLET1, balance="42000.00")   # bKash @ outlet1
    new_pbs(cur, run, ACCT_O1_NG, NAGAD, OUTLET1, balance="15000.00")   # Nagad @ outlet1
    new_pbs(cur, run, ACCT_O2_BK, BKASH, OUTLET2, balance="30000.00")   # bKash @ outlet2
    return run


def _providers_seen(cur, run_id=None):
    if run_id:
        cur.execute(
            "SELECT DISTINCT provider_id::text FROM provider_balance_snapshots "
            "WHERE simulation_run_id = %s ORDER BY 1",
            (run_id,),
        )
    else:
        cur.execute("SELECT DISTINCT provider_id::text FROM provider_balance_snapshots ORDER BY 1")
    return [r[0] for r in cur.fetchall()]


def test_bkash_ops_reads_only_bkash(conn):
    with conn.cursor() as setup:
        run = _seed_snapshots(setup)
    with as_role(conn, BKASH_OPS) as cur:
        assert _providers_seen(cur, run) == [BKASH]


def test_nagad_ops_cannot_read_rocket_or_bkash(conn):
    with conn.cursor() as setup:
        run = _seed_snapshots(setup)
    with as_role(conn, NAGAD_OPS) as cur:
        assert _providers_seen(cur, run) == [NAGAD]


def test_rocket_ops_sees_nothing_when_no_rocket_rows(conn):
    with conn.cursor() as setup:
        run = _seed_snapshots(setup)
    with as_role(conn, ROCKET_OPS) as cur:
        assert _providers_seen(cur, run) == []


def test_agent_limited_to_own_outlet(conn):
    with conn.cursor() as setup:
        run = _seed_snapshots(setup)
    # agent1 is scoped to outlet1: sees both providers there, none from outlet2
    with as_role(conn, AGENT1) as cur:
        cur.execute(
            "SELECT DISTINCT outlet_id::text FROM provider_balance_snapshots WHERE simulation_run_id = %s",
            (run,),
        )
        outlets = {r[0] for r in cur.fetchall()}
        assert outlets == {OUTLET1}


def test_area_manager_limited_to_area(conn):
    with conn.cursor() as setup:
        run = _seed_snapshots(setup)
    # area_mgr: provider=bKash, area=Market (outlet1). Must not see bKash @ outlet2 (Riverside).
    with as_role(conn, AREA_MGR) as cur:
        cur.execute(
            "SELECT DISTINCT outlet_id::text FROM provider_balance_snapshots WHERE simulation_run_id = %s",
            (run,),
        )
        outlets = {r[0] for r in cur.fetchall()}
        assert outlets == {OUTLET1}


def test_missing_provider_scope_is_not_a_wildcard(conn):
    with conn.cursor() as setup:
        run = _seed_snapshots(setup)
    with as_role(conn, MGMT) as cur:
        cur.execute(
            "SELECT count(*) FROM provider_balance_snapshots WHERE simulation_run_id = %s",
            (run,),
        )
        assert cur.fetchone()[0] == 0


def test_unauthorized_mutation_denied(conn):
    with conn.cursor() as setup:
        run = _seed_snapshots(setup)
    # authenticated has no UPDATE privilege on the ledger => permission denied
    with as_role(conn, BKASH_OPS) as cur:
        raised = False
        try:
            cur.execute("UPDATE provider_balance_snapshots SET balance=0")
        except Exception:
            raised = True
        assert raised, "authenticated must not be able to mutate the ledger"


def test_case_visibility_follows_provider_scope(conn):
    from helpers import new_alert, new_assessment, new_case
    with conn.cursor() as setup:
        run = new_run(setup)
        alert = new_alert(setup, run, OUTLET1, BKASH)
        assess = new_assessment(setup, run, OUTLET1, BKASH)
        setup.execute("INSERT INTO alert_quality_assessments (alert_id, data_quality_assessment_id) VALUES (%s,%s)",
                      (alert, assess))
        case = new_case(setup, alert, OUTLET1, BKASH)
    # Scope the assertion to this specific case so it is robust to other
    # committed cases (Phase 5 workflow tests persist provider-scoped cases).
    with as_role(conn, BKASH_OPS) as cur:
        cur.execute("SELECT count(*) FROM cases WHERE case_id = %s", (case,))
        assert cur.fetchone()[0] == 1
    with as_role(conn, NAGAD_OPS) as cur:
        cur.execute("SELECT count(*) FROM cases WHERE case_id = %s", (case,))
        assert cur.fetchone()[0] == 0
