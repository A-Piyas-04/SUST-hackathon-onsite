"""Responsible-design regression: degraded data yields no confident alertable output.

Provider A/B boundary denial and alert/append-only immutability are covered by
tests/phase5 and tests/phase6, which run in the same suite; this module locks the
Scenario C safety guarantee at the Phase 7 gate (required matrix item 18).
"""

from __future__ import annotations

import random

from app.core.auth import OUTLET1

OUTLET = str(OUTLET1)


def _start_run(client, headers, scenario: str) -> str:
    body = {"scenario_code": scenario, "outlet_id": OUTLET, "seed": random.randrange(1, 2_000_000_000)}
    resp = client.post("/api/v1/simulations/runs", json=body, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["simulation_run_id"]


def test_scenario_c_degraded_data_is_suppressed_not_alertable(client, admin_headers):
    run_id = _start_run(client, admin_headers, "scenario_c")
    anomalies = client.post(
        "/api/v1/internal/analytics/anomalies/run",
        json={"simulation_run_id": run_id, "outlet_id": OUTLET},
        headers=admin_headers,
    ).json()

    suppressed = [f for f in anomalies["flags"] if f["disposition"] == "suppressed_data_quality"]
    assert suppressed and anomalies["suppressed_count"] >= 1
    for flag in suppressed:
        assert flag["suppression_reason"]
        # A suppressed flag must never present as a confident, actionable signal.
        assert flag["confidence_level"] in {"low", "unavailable"}
    # No suppressed evaluation becomes an alertable candidate.
    assert anomalies["candidates"] == []


def test_scenario_c_publish_produces_no_anomaly_alert(client, admin_headers):
    run_id = _start_run(client, admin_headers, "scenario_c")
    published = client.post(
        "/api/v1/internal/alerts/publish",
        json={"simulation_run_id": run_id, "outlet_id": OUTLET},
        headers=admin_headers,
    ).json()
    anomaly_alerts = [a for a in published["published"] if a["alert_type"] == "anomaly"]
    assert anomaly_alerts == [], "degraded Scenario C data must not publish an anomaly alert"
