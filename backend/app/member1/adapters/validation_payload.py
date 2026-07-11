"""Validation-metric payload contract for /metrics and
/api/v1/validation/results (schema.md Section 11.3 `metric_results` /
`v_validation_summary`).

Owner: Member 1 for the contract + placeholder; Analytics/QA (Member 3) and
Member 2 both contribute real measured metrics later (Phase 7).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

MetricCategory = Literal["analytics", "performance", "reliability", "explainability"]


class ValidationMetricPayload(BaseModel):
    metric_code: str
    category: MetricCategory
    value: float
    unit: str
    sample_size: int = Field(gt=0)
    method: str
    limitations: str
    computed_at: datetime


def get_placeholder_metrics() -> list[ValidationMetricPayload]:
    """At least one placeholder metric so /metrics returns a valid shape
    immediately, even before any real analytics run has executed (matches
    the `bootstrap_placeholder` row seeded in
    migrations/005_validation_and_reads.sql)."""
    return [
        ValidationMetricPayload(
            metric_code="api_p95_latency_ms",
            category="performance",
            value=0.0,
            unit="ms",
            sample_size=1,
            method="Placeholder scaffold value; not yet measured.",
            limitations="Phase 1 scaffold only — replace with a real measured p95 latency in Phase 7 before reporting.",
            computed_at=datetime.now(timezone.utc),
        )
    ]


__all__ = ["ValidationMetricPayload", "MetricCategory", "get_placeholder_metrics"]
