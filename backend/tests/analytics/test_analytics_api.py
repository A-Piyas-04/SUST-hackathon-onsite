"""Integration tests for Phase 4 analytics endpoints and A/B/C scenarios."""

from __future__ import annotations

from decimal import Decimal

from tests.analytics.conftest import start_run


def _run_liquidity(client, headers, run_id, outlet_id):
    resp = client.post(
        "/api/v1/internal/analytics/liquidity/run",
        json={"simulation_run_id": run_id, "outlet_id": str(outlet_id)},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _run_anomalies(client, headers, run_id, outlet_id):
    resp = client.post(
        "/api/v1/internal/analytics/anomalies/run",
        json={"simulation_run_id": run_id, "outlet_id": str(outlet_id)},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# --------------------------------------------------------------------------- #
# Scenario A — hidden provider shortage
# --------------------------------------------------------------------------- #
def test_scenario_a_identifies_reserve_shortage(client, auth_headers, outlet_id):
    run_id = start_run(client, auth_headers, "scenario_a")
    result = _run_liquidity(client, auth_headers, run_id, outlet_id)

    # Shared cash is present and separated from provider reserves.
    shared = [p for p in result["projections"] if p["reserve_type"] == "shared_cash"]
    providers = [p for p in result["projections"] if p["reserve_type"] == "provider_e_money"]
    assert len(shared) == 1
    assert len(providers) == 3
    assert len({p["provider_id"] for p in providers}) == 3  # provider isolation

    # Concentrated cash-out demand on the target provider drains SHARED PHYSICAL
    # CASH (the agent hands out cash), not that provider's e-money — which in fact
    # RISES as customers send e-money in. This is the "hidden" pressure Scenario A
    # illustrates: the combined view looks healthy while the cash drawer depletes,
    # matching the Bangla alert in Problem_Statement.md §11 ("নগদ টাকা শেষ").
    cash = shared[0]
    assert cash["projected_shortage_at"] is not None, "shared cash should deplete under cash-out"
    assert Decimal(cash["burn_rate_per_hour"]) > 0
    assert cash["is_actionable"] is True
    assert cash["confidence_level"] in {"low", "medium", "high"}

    # The target provider's e-money must NOT be depleting under cash-out pressure;
    # cash-out increases its e-money balance, so no shortage is projected for it.
    bkash = next(
        p for p in providers if p["provider_id"] == "11111111-1111-1111-1111-111111111111"
    )
    assert bkash["projected_shortage_at"] is None
    assert Decimal(bkash["burn_rate_per_hour"]) <= 0

    # A liquidity candidate is produced through the seam.
    assert result["candidates"], "expected a liquidity alert candidate"
    assert all(c["is_alertable"] for c in result["candidates"])


def test_liquidity_projections_endpoint_round_trips(client, auth_headers, outlet_id):
    run_id = start_run(client, auth_headers, "scenario_a")
    _run_liquidity(client, auth_headers, run_id, outlet_id)
    resp = client.get(
        f"/api/v1/outlets/{outlet_id}/liquidity-projections", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["outlet_id"] == str(outlet_id)
    assert len(body["projections"]) >= 4
    # No blended total: shared cash and providers are distinct rows.
    reserve_types = {p["reserve_type"] for p in body["projections"]}
    assert reserve_types == {"shared_cash", "provider_e_money"}
    # Signals (contributing evidence) are attached.
    assert any(p["signals"] for p in body["projections"])


# --------------------------------------------------------------------------- #
# Scenario B — unusual activity with evidence and benign context
# --------------------------------------------------------------------------- #
def test_scenario_b_flags_unusual_pattern_with_benign_context(client, auth_headers, outlet_id):
    run_id = start_run(client, auth_headers, "scenario_b")
    result = _run_anomalies(client, auth_headers, run_id, outlet_id)

    review_flags = [f for f in result["flags"] if f["disposition"] == "requires_review"]
    assert review_flags, "expected an evidence-backed anomaly flag"
    flag = review_flags[0]
    assert flag["pattern"] == "near_identical_amounts"
    assert len(flag["transaction_ids"]) >= 5
    assert flag["plausible_benign_explanation"]
    assert flag["confidence_level"] in {"medium", "high"}
    # Evidence is structured, not free-form only.
    evidence_types = {e["evidence_type"] for e in flag["evidence_items"]}
    assert {"count", "amount_cluster", "distinct_parties", "detection_window"} <= evidence_types
    # Candidate produced.
    assert result["candidates"]


def test_anomaly_flag_detail_round_trips(client, auth_headers, outlet_id):
    run_id = start_run(client, auth_headers, "scenario_b")
    _run_anomalies(client, auth_headers, run_id, outlet_id)
    listing = client.get(
        f"/api/v1/outlets/{outlet_id}/anomaly-flags", headers=auth_headers
    ).json()
    assert listing["flags"]
    flag_id = listing["flags"][0]["anomaly_flag_id"]
    detail = client.get(f"/api/v1/anomaly-flags/{flag_id}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["anomaly_flag_id"] == flag_id
    assert body["evidence_items"]
    assert body["transaction_ids"]


def test_unknown_anomaly_flag_returns_not_found(client, auth_headers):
    resp = client.get(
        "/api/v1/anomaly-flags/00000000-0000-0000-0000-0000000000ff", headers=auth_headers
    )
    assert resp.status_code == 404


# --------------------------------------------------------------------------- #
# Scenario C — degraded data lowers confidence and suppresses alerts
# --------------------------------------------------------------------------- #
def test_scenario_c_suppresses_and_lowers_confidence(client, auth_headers, outlet_id):
    run_id = start_run(client, auth_headers, "scenario_c")
    anomalies = _run_anomalies(client, auth_headers, run_id, outlet_id)
    liquidity = _run_liquidity(client, auth_headers, run_id, outlet_id)

    # A cluster is present but suppressed due to degraded data quality.
    suppressed = [f for f in anomalies["flags"] if f["disposition"] == "suppressed_data_quality"]
    assert suppressed, "expected a suppressed anomaly evaluation"
    assert anomalies["suppressed_count"] >= 1
    for f in suppressed:
        assert f["suppression_reason"]
    # Suppressed evaluations never become alertable candidates.
    assert anomalies["candidates"] == []

    # The affected provider's liquidity confidence is reduced (conflicting feed).
    conflicted = [
        p
        for p in liquidity["projections"]
        if p["reserve_type"] == "provider_e_money"
        and Decimal(p["confidence_score"]) <= Decimal("0.5")
    ]
    assert conflicted, "expected reduced confidence under degraded quality"


def test_data_quality_history_reflects_engine_output(client, auth_headers, outlet_id):
    run_id = start_run(client, auth_headers, "scenario_c")
    _run_anomalies(client, auth_headers, run_id, outlet_id)
    resp = client.get(
        f"/api/v1/outlets/{outlet_id}/data-quality/history", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    statuses = {item["assessment"]["status"] for item in resp.json()["assessments"]}
    # The Phase 4 engine persists a conflicting assessment for the degraded feed.
    assert "conflicting" in statuses
    engines = {item["assessment"]["engine_version"] for item in resp.json()["assessments"]}
    assert "quality-v1" in engines  # forward-compatible with Phase 4 engine output


# --------------------------------------------------------------------------- #
# Reproducibility
# --------------------------------------------------------------------------- #
def test_repeated_runs_are_reproducible(client, auth_headers, outlet_id):
    run_id = start_run(client, auth_headers, "scenario_a", seed=4242)
    first = _run_liquidity(client, auth_headers, run_id, outlet_id)
    second = _run_liquidity(client, auth_headers, run_id, outlet_id)

    def _fingerprint(result):
        return sorted(
            (
                p["reserve_type"],
                p.get("provider_id"),
                p["burn_rate_per_hour"],
                p["current_balance"],
                p["confidence_score"],
                p["projected_shortage_at"],
            )
            for p in result["projections"]
        )

    assert _fingerprint(first) == _fingerprint(second)


def test_run_requires_authentication(client, outlet_id):
    resp = client.post(
        "/api/v1/internal/analytics/liquidity/run",
        json={"simulation_run_id": "00000000-0000-0000-0000-000000000001"},
    )
    assert resp.status_code == 401


def test_run_unknown_simulation_returns_not_found(client, auth_headers):
    resp = client.post(
        "/api/v1/internal/analytics/liquidity/run",
        json={"simulation_run_id": "00000000-0000-0000-0000-0000000000aa"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
