"""Determinism and replay tests."""

from __future__ import annotations

from app.core.auth import OUTLET1


def _start_run(client, headers, seed: int = 1001):
    return client.post(
        "/api/v1/simulations/runs",
        headers=headers,
        json={"scenario_code": "normal", "seed": seed, "outlet_id": str(OUTLET1)},
    )


def _semantic_fingerprint(client, headers):
    txns = client.get(
        f"/api/v1/outlets/{OUTLET1}/transactions",
        headers=headers,
    ).json()["transactions"]
    return sorted(
        (t["synthetic_transaction_ref"], t["amount"], t["occurred_at"]) for t in txns
    )


def test_same_seed_produces_equal_semantic_outputs(client, auth_headers):
    r1 = _start_run(client, auth_headers, seed=4242)
    assert r1.status_code == 201
    fp1 = _semantic_fingerprint(client, auth_headers)

    r2 = _start_run(client, auth_headers, seed=4242)
    assert r2.status_code == 201
    fp2 = _semantic_fingerprint(client, auth_headers)
    assert fp1 == fp2


def test_reset_rerun_reproduces_artifacts(client, auth_headers):
    start = _start_run(client, auth_headers, seed=7777)
    assert start.status_code == 201
    run_id = start.json()["simulation_run_id"]
    before = start.json()["artifacts"]

    reset = client.post(f"/api/v1/simulations/runs/{run_id}/reset", headers=auth_headers)
    assert reset.status_code == 200
    after = reset.json()["artifacts"]

    assert after["ingestion_batches"] >= before["ingestion_batches"]
    assert after["cash_snapshots"] >= before["cash_snapshots"]
    assert after["provider_snapshots"] >= before["provider_snapshots"]
