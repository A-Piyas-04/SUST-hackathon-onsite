"""Alert publication, dedup, immutability, and localized explanation tests."""

from __future__ import annotations

from tests.phase5.conftest import anomaly_alert, publish, start_run


def test_publish_creates_alert_with_sources(client, bkash_ops_headers):
    run_id = start_run(client, bkash_ops_headers, "scenario_b")
    published = publish(client, bkash_ops_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None, published
    # Typed analytical source link is present (no evidence recomputation).
    assert alert["source_links"]["anomaly_flag_ids"], alert["source_links"]
    assert alert["requires_case"] is True
    assert alert["structured_payload"]["evidence_summary"]


def test_deduplicates_active_equivalent_alerts(client, bkash_ops_headers):
    run_id = start_run(client, bkash_ops_headers, "scenario_b")
    first = publish(client, bkash_ops_headers, run_id)
    assert first["published"], first
    second = publish(client, bkash_ops_headers, run_id)
    # A re-run over the same window republishes nothing; equivalents deduplicate.
    assert second["published"] == []
    assert second["deduplicated_alert_ids"]


def test_alert_evidence_immutable_across_case_lifecycle(client, bkash_ops_headers):
    run_id = start_run(client, bkash_ops_headers, "scenario_b")
    published = publish(client, bkash_ops_headers, run_id)
    alert = anomaly_alert(published)
    before = client.get(f"/api/v1/alerts/{alert['alert_id']}", headers=bkash_ops_headers).json()

    # Drive a full case lifecycle and confirm alert analytical content is frozen.
    case = client.post(
        f"/api/v1/alerts/{alert['alert_id']}/cases", json={}, headers=bkash_ops_headers
    ).json()
    client.post(f"/api/v1/cases/{case['case_id']}/acknowledge", json={}, headers=bkash_ops_headers)

    after = client.get(f"/api/v1/alerts/{alert['alert_id']}", headers=bkash_ops_headers).json()
    assert after["structured_payload"] == before["structured_payload"]
    assert after["detected_at"] == before["detected_at"]
    assert after["severity"] == before["severity"]


def test_explanations_rendered_in_en_and_bangla(client, bkash_ops_headers):
    run_id = start_run(client, bkash_ops_headers, "scenario_b")
    published = publish(client, bkash_ops_headers, run_id)
    alert = anomaly_alert(published)
    resp = client.get(
        f"/api/v1/alerts/{alert['alert_id']}/explanations", headers=bkash_ops_headers
    )
    assert resp.status_code == 200, resp.text
    by_locale = {e["locale"]: e for e in resp.json()["explanations"]}
    assert "en" in by_locale
    assert "bn" in by_locale or "bn_latn" in by_locale
    # Anomaly explanations must carry benign context and full structure.
    en = by_locale["en"]
    assert en["situation_text"] and en["uncertainty_text"] and en["next_step_text"]
    assert en["benign_context_text"]


def test_candidate_validation_normal_scenario_has_no_anomaly_alert(client, bkash_ops_headers):
    run_id = start_run(client, bkash_ops_headers, "normal")
    published = publish(client, bkash_ops_headers, run_id)
    assert anomaly_alert(published) is None
