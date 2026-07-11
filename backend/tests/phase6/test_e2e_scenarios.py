"""Phase 6 end-to-end regression suite.

Drives the exact HTTP endpoints the thin frontend calls, exercising Scenarios
A–D deterministically and asserting the MVP freeze-gate guarantees:

  * shared cash + three provider reserves shown separately, never blended
  * shortage timing + confidence on actionable projections
  * evidence-backed anomaly with benign context; suppression under degraded data
  * full case lifecycle through the API with a complete, ordered audit trail
  * English + Bangla/Banglish explanation rendering
  * provider-boundary enforcement (safe not-found, no existence leak)
  * alert evidence immutable across workflow mutations
  * idempotent / concurrency-safe mutations
  * no definitive fraud language in user-visible text
"""

from __future__ import annotations

from decimal import Decimal

from app.core.auth import BKASH, OUTLET1
from tests.phase6.conftest import (
    anomaly_alert,
    publish,
    start_run,
    token,
)
from app.core.auth import NAGAD_OPS, RISK_BK

OUTLET = str(OUTLET1)

# Every confidential endpoint the UI depends on must be reachable + registered.
REQUIRED_PATHS = [
    "/api/v1/providers",
    "/api/v1/outlets",
    "/api/v1/outlets/{outlet_id}/dashboard",
    "/api/v1/simulations/scenarios",
    "/api/v1/simulations/runs",
    "/api/v1/outlets/{outlet_id}/liquidity-projections",
    "/api/v1/internal/analytics/liquidity/run",
    "/api/v1/outlets/{outlet_id}/anomaly-flags",
    "/api/v1/internal/analytics/anomalies/run",
    "/api/v1/auth/demo-login",
    "/api/v1/me",
    "/api/v1/alerts",
    "/api/v1/alerts/{alert_id}/explanations",
    "/api/v1/alerts/{alert_id}/cases",
    "/api/v1/cases",
    "/api/v1/cases/{case_id}/acknowledge",
    "/api/v1/cases/{case_id}/escalate",
    "/api/v1/cases/{case_id}/resolve",
    "/api/v1/cases/{case_id}/notes",
    "/api/v1/cases/{case_id}/review",
    "/api/v1/cases/{case_id}/timeline",
    "/api/v1/cases/{case_id}/audit-events",
    "/api/v1/notifications",
]

CONFIDENTIAL_ENDPOINTS = [
    ("GET", "/api/v1/me"),
    ("GET", "/api/v1/alerts"),
    ("GET", f"/api/v1/outlets/{OUTLET}/dashboard"),
    ("GET", f"/api/v1/outlets/{OUTLET}/liquidity-projections"),
    ("GET", f"/api/v1/outlets/{OUTLET}/anomaly-flags"),
    ("GET", "/api/v1/cases"),
    ("GET", "/api/v1/notifications"),
]

# Words that would constitute a definitive fraud/guilt claim (guardrail 6).
FORBIDDEN_WORDS = [
    "fraud",
    "fraudulent",
    "criminal",
    "guilty",
    "theft",
    "stole",
    "stolen",
    "embezzle",
    "launder",
    "scam",
]


# --------------------------------------------------------------------------- #
# Backend integration
# --------------------------------------------------------------------------- #
def test_all_required_routers_registered_and_openapi_matches(client):
    spec = client.get("/openapi.json").json()
    runtime_paths = set(spec["paths"].keys())
    missing = [p for p in REQUIRED_PATHS if p not in runtime_paths]
    assert not missing, f"missing registered routes: {missing}"


def test_unauthenticated_access_denied_on_confidential_endpoints(client):
    for method, path in CONFIDENTIAL_ENDPOINTS:
        resp = client.request(method, path)
        assert resp.status_code == 401, f"{method} {path} -> {resp.status_code} (expected 401)"


# --------------------------------------------------------------------------- #
# Scenario A — hidden shared-cash shortage (dashboard + liquidity)
# --------------------------------------------------------------------------- #
def test_scenario_a_shared_cash_shortage_visible_no_blended_total(client, agent_headers):
    run_id = start_run(client, agent_headers, "scenario_a")
    liq = client.post(
        "/api/v1/internal/analytics/liquidity/run",
        json={"simulation_run_id": run_id, "outlet_id": OUTLET},
        headers=agent_headers,
    )
    assert liq.status_code == 201, liq.text

    # Dashboard keeps the four reserves separate and exposes no blended total.
    dash = client.get(f"/api/v1/outlets/{OUTLET}/dashboard", headers=agent_headers).json()
    assert "shared_cash" in dash and "providers" in dash
    assert len(dash["providers"]) == 3
    assert {p["provider"]["code"] for p in dash["providers"]} == {"bkash", "nagad", "rocket"}
    # No key at any level blends reserves into a single figure.
    for banned in ("total", "combined_balance", "total_balance", "net_balance"):
        assert banned not in dash
        assert banned not in dash["shared_cash"]

    # Shared cash carries a shortage estimate + confidence; provider e-money does not
    # falsely show an e-money shortage under cash-out pressure.
    projections = client.get(
        f"/api/v1/outlets/{OUTLET}/liquidity-projections", headers=agent_headers
    ).json()["projections"]
    shared = [p for p in projections if p["reserve_type"] == "shared_cash"]
    providers = [p for p in projections if p["reserve_type"] == "provider_e_money"]
    assert len(shared) == 1 and len(providers) == 3
    assert shared[0]["projected_shortage_at"] is not None
    assert shared[0]["confidence_level"] in {"low", "medium", "high"}
    assert shared[0]["is_actionable"] is True
    bkash = next(p for p in providers if p["provider_id"] == str(BKASH))
    assert bkash["projected_shortage_at"] is None  # e-money not falsely depleting


# --------------------------------------------------------------------------- #
# Scenario B — unusual activity with evidence + benign context; publishable
# --------------------------------------------------------------------------- #
def test_scenario_b_anomaly_evidence_benign_context_and_publish(client, agent_headers, risk_headers):
    run_id = start_run(client, agent_headers, "scenario_b")
    anomalies = client.post(
        "/api/v1/internal/analytics/anomalies/run",
        json={"simulation_run_id": run_id, "outlet_id": OUTLET},
        headers=agent_headers,
    ).json()
    review = [f for f in anomalies["flags"] if f["disposition"] == "requires_review"]
    assert review, "expected an evidence-backed anomaly"
    flag = review[0]
    assert flag["pattern"] == "near_identical_amounts"
    assert flag["plausible_benign_explanation"]  # benign context present
    evidence_types = {e["evidence_type"] for e in flag["evidence_items"]}
    assert {"count", "amount_cluster", "distinct_parties", "detection_window"} <= evidence_types

    published = publish(client, risk_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None, "anomaly alert should be publishable"
    # Immutable evidence is present on the published alert.
    assert alert["structured_payload"].get("evidence_summary")


# --------------------------------------------------------------------------- #
# Scenario C — degraded data lowers confidence and suppresses alerts
# --------------------------------------------------------------------------- #
def test_scenario_c_degraded_confidence_and_suppression(client, agent_headers):
    run_id = start_run(client, agent_headers, "scenario_c")
    anomalies = client.post(
        "/api/v1/internal/analytics/anomalies/run",
        json={"simulation_run_id": run_id, "outlet_id": OUTLET},
        headers=agent_headers,
    ).json()
    liquidity = client.post(
        "/api/v1/internal/analytics/liquidity/run",
        json={"simulation_run_id": run_id, "outlet_id": OUTLET},
        headers=agent_headers,
    ).json()

    suppressed = [f for f in anomalies["flags"] if f["disposition"] == "suppressed_data_quality"]
    assert suppressed and anomalies["suppressed_count"] >= 1
    for f in suppressed:
        assert f["suppression_reason"]
    # Suppressed evaluations never become alertable candidates (no false alert).
    assert anomalies["candidates"] == []

    # At least one provider reserve shows reduced confidence under the degraded feed.
    conflicted = [
        p
        for p in liquidity["projections"]
        if p["reserve_type"] == "provider_e_money" and Decimal(p["confidence_score"]) <= Decimal("0.5")
    ]
    assert conflicted, "expected reduced confidence under degraded quality"


# --------------------------------------------------------------------------- #
# Scenario D — coordinated response and closure (full lifecycle, no DB edits)
# --------------------------------------------------------------------------- #
def test_scenario_d_full_case_lifecycle_and_immutable_evidence(client, agent_headers, risk_headers):
    run_id = start_run(client, agent_headers, "scenario_b")
    published = publish(client, risk_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None
    alert_id = alert["alert_id"]
    evidence_before = alert["structured_payload"]

    # Open case (idempotent) from the alert.
    opened = client.post(f"/api/v1/alerts/{alert_id}/cases", json={}, headers=risk_headers)
    assert opened.status_code in (200, 201), opened.text
    case = opened.json()
    case_id = case["case_id"]
    assert case["status"] == "open"
    assert case["current_owner_role"]
    assert case["recommended_next_step"]

    # Idempotency: re-opening returns the SAME case, not a duplicate.
    reopened = client.post(f"/api/v1/alerts/{alert_id}/cases", json={}, headers=risk_headers)
    assert reopened.json()["case_id"] == case_id

    # acknowledge -> note -> escalate -> review -> resolve, driving optimistic versions.
    ack = client.post(
        f"/api/v1/cases/{case_id}/acknowledge",
        json={"expected_version": case["version"]},
        headers=risk_headers,
    ).json()
    assert ack["status"] == "acknowledged" and ack["version"] == case["version"] + 1

    note = client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"note_text": "Contacted outlet; reviewing recent cluster.", "note_type": "contact_attempt"},
        headers=risk_headers,
    )
    assert note.status_code == 201, note.text

    esc = client.post(
        f"/api/v1/cases/{case_id}/escalate",
        json={"expected_version": ack["version"], "target_role": "risk_analyst"},
        headers=risk_headers,
    ).json()
    assert esc["status"] == "escalated"

    review = client.post(
        f"/api/v1/cases/{case_id}/review",
        json={"disposition": "requires_follow_up", "review_summary": "Pattern requires review; benign context plausible."},
        headers=risk_headers,
    )
    assert review.status_code == 201, review.text

    resolved = client.post(
        f"/api/v1/cases/{case_id}/resolve",
        json={"expected_version": esc["version"], "resolution_summary": "Reviewed and coordinated; no further action needed."},
        headers=risk_headers,
    ).json()
    assert resolved["status"] == "resolved"

    # Timeline + audit are complete and ordered.
    timeline = client.get(f"/api/v1/cases/{case_id}/timeline", headers=risk_headers).json()["events"]
    audit = client.get(f"/api/v1/cases/{case_id}/audit-events", headers=risk_headers).json()["events"]
    assert len(timeline) >= 5
    assert [e["occurred_at"] for e in audit] == sorted(e["occurred_at"] for e in audit)
    actions = {e["action"] for e in audit}
    assert {"case_opened", "case_acknowledged", "case_escalated", "case_resolved"} <= actions

    # Alert analytical evidence is unchanged after all workflow mutations (immutable).
    after = client.get(f"/api/v1/alerts/{alert_id}", headers=risk_headers).json()
    for key in ("evidence", "evidence_summary", "confidence", "confidence_level"):
        assert after["structured_payload"].get(key) == evidence_before.get(key)


# --------------------------------------------------------------------------- #
# Explanations — English + Bangla + Banglish
# --------------------------------------------------------------------------- #
def test_explanations_render_en_and_bangla(client, agent_headers, risk_headers):
    run_id = start_run(client, agent_headers, "scenario_b")
    published = publish(client, risk_headers, run_id)
    alert = anomaly_alert(published) or published["published"][0]
    resp = client.get(f"/api/v1/alerts/{alert['alert_id']}/explanations", headers=risk_headers)
    assert resp.status_code == 200, resp.text
    locales = {e["locale"] for e in resp.json()["explanations"]}
    assert "en" in locales
    assert locales & {"bn", "bn_latn"}, "expected a Bangla or Banglish explanation"
    for e in resp.json()["explanations"]:
        assert e["situation_text"] and e["next_step_text"]


# --------------------------------------------------------------------------- #
# Provider isolation — safe not-found, no existence leak
# --------------------------------------------------------------------------- #
def test_provider_isolation_returns_safe_not_found(client, agent_headers, risk_headers):
    run_id = start_run(client, agent_headers, "scenario_b")
    published = publish(client, risk_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None  # bKash-confidential anomaly alert
    alert_id = alert["alert_id"]

    # bKash-scoped identity can read it.
    assert client.get(f"/api/v1/alerts/{alert_id}", headers=token(RISK_BK)).status_code == 200
    # Nagad ops gets the SAME response shape as a missing record (safe not-found).
    forbidden = client.get(f"/api/v1/alerts/{alert_id}", headers=token(NAGAD_OPS))
    missing = client.get(
        "/api/v1/alerts/00000000-0000-0000-0000-0000000000ff", headers=token(NAGAD_OPS)
    )
    assert forbidden.status_code == missing.status_code == 404
    assert forbidden.json()["error"]["code"] == missing.json()["error"]["code"] == "not_found"
    # No wording that reveals a cross-provider record exists.
    body = forbidden.text.lower()
    assert "forbidden" not in body and "access denied" not in body and "permission" not in body


# --------------------------------------------------------------------------- #
# Concurrency — stale version conflicts fail safely
# --------------------------------------------------------------------------- #
def test_stale_version_mutation_fails_safely(client, agent_headers, risk_headers):
    run_id = start_run(client, agent_headers, "scenario_b")
    published = publish(client, risk_headers, run_id)
    alert = anomaly_alert(published) or published["published"][0]
    case = client.post(f"/api/v1/alerts/{alert['alert_id']}/cases", json={}, headers=risk_headers).json()
    case_id = case["case_id"]

    ack = client.post(
        f"/api/v1/cases/{case_id}/acknowledge",
        json={"expected_version": case["version"]},
        headers=risk_headers,
    ).json()
    assert ack["version"] == case["version"] + 1

    # Escalate with the now-stale original version -> must not silently apply.
    stale = client.post(
        f"/api/v1/cases/{case_id}/escalate",
        json={"expected_version": case["version"], "target_role": "risk_analyst"},
        headers=risk_headers,
    )
    assert stale.status_code >= 400
    current = client.get(f"/api/v1/cases/{case_id}", headers=risk_headers).json()
    assert current["version"] == ack["version"]  # unchanged by the stale attempt


# --------------------------------------------------------------------------- #
# Safe language — no definitive fraud claims in user-visible text
# --------------------------------------------------------------------------- #
def test_no_definitive_fraud_language_in_user_visible_text(client, agent_headers, risk_headers):
    run_id = start_run(client, agent_headers, "scenario_b")
    anomalies = client.post(
        "/api/v1/internal/analytics/anomalies/run",
        json={"simulation_run_id": run_id, "outlet_id": OUTLET},
        headers=agent_headers,
    ).json()
    published = publish(client, risk_headers, run_id)

    texts: list[str] = []
    for f in anomalies["flags"]:
        texts += [f["evidence_summary"], f["plausible_benign_explanation"], f.get("suppression_reason") or ""]
    for a in published["published"]:
        texts.append(a["title_key"])
        payload = a["structured_payload"]
        texts += [str(payload.get("recommended_next_step", "")), str(payload.get("evidence_summary", ""))]
        expl = client.get(f"/api/v1/alerts/{a['alert_id']}/explanations", headers=risk_headers).json()
        for e in expl["explanations"]:
            texts += [
                e["situation_text"],
                e["evidence_text"],
                e["uncertainty_text"],
                e["next_step_text"],
                e.get("benign_context_text") or "",
            ]

    joined = " ".join(texts).lower()
    hits = [w for w in FORBIDDEN_WORDS if w in joined]
    assert not hits, f"definitive fraud language found in user-visible text: {hits}"
