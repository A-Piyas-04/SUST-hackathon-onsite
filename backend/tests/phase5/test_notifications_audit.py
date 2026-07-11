"""Notification and audit-trail tests (Phase 5 step 6)."""

from __future__ import annotations

from tests.phase5.conftest import anomaly_alert, publish, start_run


def _open_case(client, ops_headers, admin_headers):
    run_id = start_run(client, admin_headers, "scenario_b")
    published = publish(client, admin_headers, run_id)
    alert = anomaly_alert(published)
    resp = client.post(f"/api/v1/alerts/{alert['alert_id']}/cases", json={}, headers=ops_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_mutation_writes_audit_event_atomically(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    before = client.get(f"/api/v1/cases/{cid}/audit-events", headers=bkash_ops_headers).json()
    n_before = len(before["events"])

    client.post(f"/api/v1/cases/{cid}/acknowledge", json={}, headers=bkash_ops_headers)
    after = client.get(f"/api/v1/cases/{cid}/audit-events", headers=bkash_ops_headers).json()
    actions = [e["action"] for e in after["events"]]
    assert len(after["events"]) == n_before + 1
    assert "case_acknowledged" in actions
    # Every audit event carries actor + scope context.
    ack = next(e for e in after["events"] if e["action"] == "case_acknowledged")
    assert ack["actor_user_id"] and ack["outlet_id"]


def test_failed_mutation_writes_no_audit_event(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    before = client.get(f"/api/v1/cases/{cid}/audit-events", headers=bkash_ops_headers).json()
    # Illegal open -> resolved must not leave a partial audit trail.
    client.post(
        f"/api/v1/cases/{cid}/resolve",
        json={"resolution_summary": "x"},
        headers=bkash_ops_headers,
    )
    after = client.get(f"/api/v1/cases/{cid}/audit-events", headers=bkash_ops_headers).json()
    assert len(after["events"]) == len(before["events"])


def test_timeline_completeness_and_ordering(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    client.post(f"/api/v1/cases/{cid}/acknowledge", json={}, headers=bkash_ops_headers)
    client.post(
        f"/api/v1/cases/{cid}/notes",
        json={"note_text": "contacted the outlet", "note_type": "contact_attempt"},
        headers=bkash_ops_headers,
    )
    resp = client.get(f"/api/v1/cases/{cid}/timeline", headers=bkash_ops_headers)
    assert resp.status_code == 200, resp.text
    events = resp.json()["events"]
    types = {e["event_type"] for e in events}
    assert {"case_opened", "alert_created", "status_change", "note"} <= types
    # Deterministic non-decreasing ordering by event_at.
    times = [e["event_at"] for e in events]
    assert times == sorted(times)


def test_notification_list_and_read_persist(client, bkash_ops_headers, admin_headers):
    case = _open_case(client, bkash_ops_headers, admin_headers)
    listing = client.get("/api/v1/notifications", headers=bkash_ops_headers).json()
    mine = [n for n in listing["notifications"] if n["case_id"] == case["case_id"]]
    assert mine, listing
    assert mine[0]["status"] == "queued"

    nid = mine[0]["notification_id"]
    read = client.post(f"/api/v1/notifications/{nid}/read", headers=bkash_ops_headers)
    assert read.status_code == 200, read.text
    assert read.json()["status"] == "read"
    assert read.json()["read_at"] is not None

    # Read-state persists.
    again = client.get("/api/v1/notifications", headers=bkash_ops_headers).json()
    persisted = next(n for n in again["notifications"] if n["notification_id"] == nid)
    assert persisted["status"] == "read"
