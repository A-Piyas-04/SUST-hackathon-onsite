"""Scenario D — coordinated response and closure, end-to-end through the API only.

Demonstrates: publish -> route -> open -> acknowledge -> note -> escalate ->
review -> resolve, with a complete audit trail and immutable alert evidence.
No direct database edits are used anywhere in this flow.
"""

from __future__ import annotations

from tests.phase5.conftest import anomaly_alert, publish, start_run, token
from app.core.auth import RISK_BK


def test_scenario_d_full_lifecycle(client, bkash_ops_headers):
    # 1) Analytical evidence -> immutable alert.
    run_id = start_run(client, bkash_ops_headers, "scenario_b")
    published = publish(client, bkash_ops_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None, published
    alert_id = alert["alert_id"]
    evidence_before = alert["structured_payload"]

    # 2) Localized explanations exist (EN + Bangla/Banglish).
    explanations = client.get(
        f"/api/v1/alerts/{alert_id}/explanations", headers=bkash_ops_headers
    ).json()["explanations"]
    locales = {e["locale"] for e in explanations}
    assert "en" in locales and ({"bn", "bn_latn"} & locales)

    # 3) Open (routed) case with owner + next step.
    case = client.post(
        f"/api/v1/alerts/{alert_id}/cases", json={}, headers=bkash_ops_headers
    ).json()
    cid = case["case_id"]
    assert case["status"] == "open"
    assert case["current_owner_role"] == "provider_ops"
    assert case["recommended_next_step"]

    # 4) Acknowledge.
    ack = client.post(f"/api/v1/cases/{cid}/acknowledge", json={}, headers=bkash_ops_headers)
    assert ack.status_code == 200 and ack.json()["status"] == "acknowledged"

    # 5) Add a coordination note.
    note = client.post(
        f"/api/v1/cases/{cid}/notes",
        json={"note_text": "Contacted outlet for review.", "note_type": "contact_attempt"},
        headers=bkash_ops_headers,
    )
    assert note.status_code == 201

    # 6) Escalate to risk analyst.
    esc = client.post(
        f"/api/v1/cases/{cid}/escalate",
        json={"target_role": "risk_analyst", "reason": "requires review"},
        headers=bkash_ops_headers,
    )
    assert esc.status_code == 200 and esc.json()["status"] == "escalated"
    assert esc.json()["current_owner_role"] == "risk_analyst"

    # 7) Risk analyst reviews (advisory; never a fraud verdict).
    risk = token(RISK_BK)
    review = client.post(
        f"/api/v1/cases/{cid}/review",
        json={
            "disposition": "requires_follow_up",
            "review_summary": "Pattern is unusual and requires operational follow-up.",
            "was_false_positive": False,
        },
        headers=risk,
    )
    assert review.status_code == 201, review.text

    # 8) Resolve with a summary.
    resolved = client.post(
        f"/api/v1/cases/{cid}/resolve",
        json={"resolution_summary": "Confirmed unusual; operational review completed."},
        headers=risk,
    )
    assert resolved.status_code == 200 and resolved.json()["status"] == "resolved"

    # 9) Full timeline + audit history are queryable.
    timeline = client.get(f"/api/v1/cases/{cid}/timeline", headers=bkash_ops_headers).json()
    tl_types = {e["event_type"] for e in timeline["events"]}
    assert {"case_opened", "status_change", "note", "review"} <= tl_types

    audit = client.get(f"/api/v1/cases/{cid}/audit-events", headers=bkash_ops_headers).json()
    actions = {e["action"] for e in audit["events"]}
    assert {
        "case_opened",
        "case_acknowledged",
        "note_added",
        "case_escalated",
        "case_reviewed",
        "case_resolved",
    } <= actions

    # 10) Alert analytical evidence remained immutable throughout.
    evidence_after = client.get(
        f"/api/v1/alerts/{alert_id}", headers=bkash_ops_headers
    ).json()["structured_payload"]
    assert evidence_after == evidence_before
