"""Case workflow tests: transitions, concurrency, idempotency, resolution."""

from __future__ import annotations

from tests.phase5.conftest import anomaly_alert, publish, start_run


def _open_case(client, ops_headers, admin_headers):
    run_id = start_run(client, admin_headers, "scenario_b")
    published = publish(client, admin_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None, published
    resp = client.post(f"/api/v1/alerts/{alert['alert_id']}/cases", json={}, headers=ops_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_open_case_is_routed_and_idempotent(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    assert case["status"] == "open"
    assert case["current_owner_role"] == "provider_ops"  # bkash routing rule
    assert case["recommended_next_step"]
    # Re-opening the same alert returns the same case (idempotent), not a duplicate.
    alert_id = case["alert_id"]
    again = client.post(f"/api/v1/alerts/{alert_id}/cases", json={}, headers=bkash_ops_headers)
    assert again.status_code == 200
    assert again.json()["case_id"] == case["case_id"]


def test_legal_transition_matrix_enforced(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    ack = client.post(f"/api/v1/cases/{cid}/acknowledge", json={}, headers=bkash_ops_headers)
    assert ack.status_code == 200, ack.text
    assert ack.json()["status"] == "acknowledged"
    assert ack.json()["version"] == case["version"] + 1


def test_invalid_transition_rejected(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    # open -> resolved is illegal (must acknowledge/escalate first).
    resp = client.post(
        f"/api/v1/cases/{cid}/resolve",
        json={"resolution_summary": "closing"},
        headers=bkash_ops_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "illegal_transition"


def test_duplicate_acknowledge_is_illegal_transition(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    client.post(f"/api/v1/cases/{cid}/acknowledge", json={}, headers=bkash_ops_headers)
    # acknowledged -> acknowledged is not in the legal matrix.
    dup = client.post(f"/api/v1/cases/{cid}/acknowledge", json={}, headers=bkash_ops_headers)
    assert dup.status_code == 409


def test_resolution_precondition_requires_summary(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    client.post(f"/api/v1/cases/{cid}/acknowledge", json={}, headers=bkash_ops_headers)
    # Missing resolution_summary fails contract validation.
    resp = client.post(f"/api/v1/cases/{cid}/resolve", json={}, headers=bkash_ops_headers)
    assert resp.status_code == 422


def test_optimistic_concurrency_conflict(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    # Stale expected_version is rejected with a conflict.
    resp = client.post(
        f"/api/v1/cases/{cid}/acknowledge",
        json={"expected_version": 999},
        headers=bkash_ops_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "version_conflict"


def test_idempotent_duplicate_mutation(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    key = f"ack-{cid}"
    first = client.post(
        f"/api/v1/cases/{cid}/acknowledge",
        json={"idempotency_key": key},
        headers=bkash_ops_headers,
    )
    assert first.status_code == 200
    v = first.json()["version"]
    # Replaying the same idempotency key returns the original result, no new side effects.
    second = client.post(
        f"/api/v1/cases/{cid}/acknowledge",
        json={"idempotency_key": key},
        headers=bkash_ops_headers,
    )
    assert second.status_code == 200
    assert second.json()["version"] == v  # not bumped again

    events = client.get(f"/api/v1/cases/{cid}/audit-events", headers=bkash_ops_headers).json()
    ack_events = [e for e in events["events"] if e["action"] == "case_acknowledged"]
    assert len(ack_events) == 1  # exactly one, no duplicate history
