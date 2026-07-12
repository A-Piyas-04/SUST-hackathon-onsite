"""Re-trigger idempotency: running the same scenario/analytics cycle twice must
not accumulate duplicate transactions, analytics runs, anomaly flags/evidence,
quality assessments, liquidity projections, alerts, cases, or notifications.

This guards the demo-visible duplication that came from re-running analytics for
an already-analyzed simulation run (see app/services/analytics/runner.py's
``_existing_analytics_run`` guard) and from run-scoped alert/case dedup.
"""

from __future__ import annotations

import os

import psycopg2

from app.core.auth import OUTLET1
from tests.phase5.conftest import anomaly_alert, publish, start_run


def _run_analytics(client, headers, run_id: str) -> None:
    body = {"simulation_run_id": run_id, "outlet_id": str(OUTLET1)}
    assert client.post(
        "/api/v1/internal/analytics/liquidity/run", json=body, headers=headers
    ).status_code == 201
    assert client.post(
        "/api/v1/internal/analytics/anomalies/run", json=body, headers=headers
    ).status_code == 201


def _counts(run_id: str) -> dict[str, int]:
    """Row counts scoped to a single simulation run, so unrelated test data in the
    shared database cannot influence the assertion."""
    conn = psycopg2.connect(os.environ["DIRECT_DATABASE_URL"])
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  (SELECT count(*) FROM transactions WHERE simulation_run_id = %(r)s),
                  (SELECT count(*) FROM analytics_runs WHERE simulation_run_id = %(r)s),
                  (SELECT count(*) FROM anomaly_flags af
                     JOIN analytics_runs ar USING (analytics_run_id)
                    WHERE ar.simulation_run_id = %(r)s),
                  (SELECT count(*) FROM anomaly_evidence_items ei
                     JOIN anomaly_flags af USING (anomaly_flag_id)
                     JOIN analytics_runs ar USING (analytics_run_id)
                    WHERE ar.simulation_run_id = %(r)s),
                  (SELECT count(*) FROM data_quality_assessments WHERE simulation_run_id = %(r)s),
                  (SELECT count(*) FROM liquidity_projections lp
                     JOIN analytics_runs ar USING (analytics_run_id)
                    WHERE ar.simulation_run_id = %(r)s),
                  (SELECT count(*) FROM alerts WHERE simulation_run_id = %(r)s),
                  (SELECT count(*) FROM cases c
                     JOIN alerts a USING (alert_id)
                    WHERE a.simulation_run_id = %(r)s),
                  (SELECT count(*) FROM notifications n
                     JOIN cases c USING (case_id)
                     JOIN alerts a USING (alert_id)
                    WHERE a.simulation_run_id = %(r)s)
                """,
                {"r": run_id},
            )
            row = cur.fetchone()
    finally:
        conn.close()
    keys = (
        "transactions",
        "analytics_runs",
        "anomaly_flags",
        "anomaly_evidence_items",
        "data_quality_assessments",
        "liquidity_projections",
        "alerts",
        "cases",
        "notifications",
    )
    return dict(zip(keys, row))


def test_second_identical_trigger_produces_no_duplicates(
    client, admin_headers, bkash_ops_headers
):
    # --- First trigger: generate, analyze, publish, open a case ----------------
    run_id = start_run(client, admin_headers, "scenario_b")
    first = publish(client, admin_headers, run_id)
    alert = anomaly_alert(first)
    assert alert is not None, first
    case = client.post(
        f"/api/v1/alerts/{alert['alert_id']}/cases", json={}, headers=bkash_ops_headers
    )
    assert case.status_code in (200, 201), case.text

    before = _counts(run_id)
    # Sanity: the first cycle actually produced the artifacts we care about.
    assert before["transactions"] > 0
    assert before["analytics_runs"] == 2  # one liquidity + one anomaly
    assert before["anomaly_flags"] > 0
    assert before["data_quality_assessments"] > 0
    assert before["liquidity_projections"] > 0
    assert before["alerts"] > 0
    assert before["cases"] == 1

    # --- Second identical trigger: must be a no-op at every layer ---------------
    second = publish(client, admin_headers, run_id)
    assert second["published"] == [], second  # active-equivalent alerts deduplicate
    _run_analytics(client, admin_headers, run_id)  # re-running analytics directly
    reopen = client.post(
        f"/api/v1/alerts/{alert['alert_id']}/cases", json={}, headers=bkash_ops_headers
    )
    assert reopen.status_code in (200, 201), reopen.text

    after = _counts(run_id)
    assert after == before, {
        "before": before,
        "after": after,
        "duplicated_layers": {k: (before[k], after[k]) for k in before if before[k] != after[k]},
    }
