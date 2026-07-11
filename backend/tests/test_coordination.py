"""Alert / case coordination constraints (docs/schema.md §10, §13)."""
from helpers import (
    ACCT_O1_BK, BKASH, NAGAD, OUTLET1, OUTLET2, expect_error, new_alert,
    new_analytics_run, new_assessment, new_case, new_run,
)


def test_case_without_alert_rejected(cur):
    # a random, non-existent alert_id violates the NOT NULL FK
    with expect_error(cur):
        cur.execute(
            "INSERT INTO cases (case_number, alert_id, outlet_id, provider_id, "
            "current_owner_role, recommended_next_step) "
            "VALUES ('C-NONE', gen_random_uuid(), %s, %s, 'provider_ops', 'x')",
            (OUTLET1, BKASH),
        )


def test_legal_transition_allowed(cur):
    run = new_run(cur)
    alert = new_alert(cur, run, OUTLET1, BKASH)
    _link_source(cur, alert, run)
    case = new_case(cur, alert, OUTLET1, BKASH, status="open")
    cur.execute("UPDATE cases SET status='acknowledged', acknowledged_at=now() WHERE case_id=%s", (case,))
    cur.execute("SELECT status FROM cases WHERE case_id=%s", (case,))
    assert cur.fetchone()[0] == "acknowledged"


def test_illegal_transition_rejected(cur):
    run = new_run(cur)
    alert = new_alert(cur, run, OUTLET1, BKASH)
    _link_source(cur, alert, run)
    case = new_case(cur, alert, OUTLET1, BKASH, status="open")
    with expect_error(cur, "illegal case transition"):
        cur.execute(
            "UPDATE cases SET status='resolved', resolved_at=now(), resolution_summary='x' "
            "WHERE case_id=%s",
            (case,),
        )


def test_resolve_without_summary_rejected(cur):
    run = new_run(cur)
    alert = new_alert(cur, run, OUTLET1, BKASH)
    _link_source(cur, alert, run)
    case = new_case(cur, alert, OUTLET1, BKASH, status="acknowledged")
    with expect_error(cur, "case_resolved_needs_summary"):
        cur.execute("UPDATE cases SET status='resolved', resolved_at=now() WHERE case_id=%s", (case,))


def test_case_scope_must_match_alert(cur):
    run = new_run(cur)
    alert = new_alert(cur, run, OUTLET1, BKASH)  # scope: outlet1 / bkash
    _link_source(cur, alert, run)
    with expect_error(cur, "does not match alert scope"):
        new_case(cur, alert, OUTLET2, NAGAD)  # wrong outlet + provider


def test_alert_requires_at_least_one_source_link(cur):
    run = new_run(cur)
    alert = new_alert(cur, run, OUTLET1, BKASH)
    # deferred constraint fires when checked; force immediate to observe it in-tx
    with expect_error(cur, "at least one"):
        cur.execute("SET CONSTRAINTS ALL IMMEDIATE")
    # (savepoint rollback in expect_error restores; now link a source and it passes)
    _link_source(cur, alert, run)
    cur.execute("SET CONSTRAINTS ALL IMMEDIATE")  # no error


def test_explanation_requires_benign_for_combined(cur):
    run = new_run(cur)
    alert = new_alert(cur, run, OUTLET1, BKASH, alert_type="combined")
    _link_source(cur, alert, run)
    cur.execute(
        "INSERT INTO explanation_templates (template_key, locale, version, alert_type, "
        "situation_template, evidence_template, uncertainty_template, next_step_template) "
        "VALUES ('t','en',9,'combined','s','e','u','n') RETURNING explanation_template_id"
    )
    tmpl = cur.fetchone()[0]
    with expect_error(cur, "benign_context_text is required"):
        cur.execute(
            "INSERT INTO alert_explanations (alert_id, explanation_template_id, locale, "
            "situation_text, evidence_text, uncertainty_text, next_step_text) "
            "VALUES (%s,%s,'en','s','e','u','n')",
            (alert, tmpl),
        )


def _link_source(cur, alert, run):
    assess = new_assessment(cur, run, OUTLET1, BKASH)
    cur.execute(
        "INSERT INTO alert_quality_assessments (alert_id, data_quality_assessment_id) "
        "VALUES (%s,%s) ON CONFLICT DO NOTHING",
        (alert, assess),
    )
