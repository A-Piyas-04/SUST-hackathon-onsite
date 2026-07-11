"""Validation harness: held-out split, ground truth, determinism, metric counts."""

from __future__ import annotations

from uuid import UUID

from tests.phase7.conftest import run_harness_once

ANALYTICS_METRICS = {
    "anomaly_precision",
    "anomaly_recall",
    "anomaly_false_positive_rate",
    "shortage_lead_time_minutes",
}


def test_run_uses_held_out_split_and_completes(validation_run_summary, cur):
    summary = validation_run_summary
    assert summary["dataset_split"] == "held_out"
    assert summary["status"] == "completed"
    run_id = UUID(summary["validation_run_id"])
    cur.execute(
        "SELECT dataset_split, status FROM validation_runs WHERE validation_run_id = %s",
        (str(run_id),),
    )
    row = cur.fetchone()
    assert row == ("held_out", "completed")


def test_at_least_three_metrics_persisted_with_method_and_limitations(
    validation_run_summary, cur
):
    run_id = validation_run_summary["validation_run_id"]
    cur.execute(
        """
        SELECT metric_code, sample_size, method, limitations
        FROM metric_results WHERE validation_run_id = %s
        """,
        (run_id,),
    )
    rows = cur.fetchall()
    assert len(rows) >= 3
    for code, sample_size, method, limitations in rows:
        assert sample_size > 0, f"{code} has non-positive sample_size"
        assert method and method.strip(), f"{code} missing method"
        assert limitations and limitations.strip(), f"{code} missing limitations"


def test_ground_truth_labels_link_to_held_out_sims_and_outlet(validation_run_summary, cur):
    run_id = validation_run_summary["validation_run_id"]
    cur.execute(
        """
        SELECT gtl.simulation_run_id, gtl.outlet_id, sc.validation_split, sr.simulation_run_id
        FROM ground_truth_labels gtl
        JOIN simulation_runs sr ON sr.simulation_run_id = gtl.simulation_run_id
        JOIN simulation_scenarios sc ON sc.scenario_id = sr.scenario_id
        WHERE gtl.validation_run_id = %s
        """,
        (run_id,),
    )
    rows = cur.fetchall()
    assert rows, "expected ground-truth labels"
    outlet1 = "0b000000-0000-0000-0000-000000000001"
    for sim_id, outlet_id, split, joined_sim in rows:
        assert joined_sim is not None, "label must link to an existing simulation run"
        assert str(outlet_id) == outlet1
        # Reported metrics must never use demo/tuning splits.
        assert split == "held_out"


def test_determinism_same_seed_same_analytics_metrics(validation_run_summary):
    first = {
        m["metric_code"]: m["value"]
        for m in validation_run_summary["metrics"]
        if m["metric_code"] in ANALYTICS_METRICS
    }
    second_summary = run_harness_once()
    second = {
        m["metric_code"]: m["value"]
        for m in second_summary["metrics"]
        if m["metric_code"] in ANALYTICS_METRICS
    }
    assert first, "expected analytics metrics in first run"
    assert first == second, f"analytics metrics not deterministic: {first} vs {second}"


def test_held_out_anomaly_is_actually_detected(validation_run_summary):
    """The frozen held-out cluster must be detected — guards against a silently
    empty evaluation (e.g. ledger dedup returning zero transactions on re-run)."""
    values = {m["metric_code"]: m["value"] for m in validation_run_summary["metrics"]}
    assert values.get("anomaly_recall") == "1.0000", "held-out Scenario B cluster not detected"
    assert values.get("anomaly_precision") == "1.0000"
    assert values.get("anomaly_false_positive_rate") == "0.0000"


def test_release_candidate_recorded_in_configuration(validation_run_summary, cur):
    run_id = validation_run_summary["validation_run_id"]
    cur.execute(
        "SELECT configuration FROM validation_runs WHERE validation_run_id = %s",
        (run_id,),
    )
    config = cur.fetchone()[0]
    rc = config.get("release_candidate")
    assert rc and "commit" in rc and "contract_version" in rc
    assert "engine_versions" in rc
