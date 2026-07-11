"""Performance + reliability metrics are measured and persisted honestly."""

from __future__ import annotations

from decimal import Decimal


def _by_code(summary) -> dict:
    return {m["metric_code"]: m for m in summary["metrics"]}


def test_latency_metrics_recorded(validation_run_summary):
    metrics = _by_code(validation_run_summary)
    for code in ("api_avg_ms", "api_p95_ms"):
        assert code in metrics, f"missing {code}"
        assert metrics[code]["category"] == "performance"
        assert metrics[code]["sample_size"] > 0
        assert Decimal(metrics[code]["value"]) >= 0


def test_explanation_coverage_reflects_published_alerts(validation_run_summary):
    metrics = _by_code(validation_run_summary)
    assert "alert_explanation_coverage" in metrics
    cov = metrics["alert_explanation_coverage"]
    assert cov["category"] == "reliability"
    assert cov["sample_size"] >= 1  # at least one held-out alert published
    assert Decimal("0") <= Decimal(cov["value"]) <= Decimal("1")


def test_data_quality_incident_rate_recorded(validation_run_summary):
    metrics = _by_code(validation_run_summary)
    assert "data_quality_incident_rate" in metrics
    dq = metrics["data_quality_incident_rate"]
    assert dq["category"] == "reliability"
    assert Decimal("0") <= Decimal(dq["value"]) <= Decimal("1")


def test_metric_categories_span_multiple_types(validation_run_summary):
    categories = {m["category"] for m in validation_run_summary["metrics"]}
    assert {"analytics", "performance", "reliability"} <= categories
