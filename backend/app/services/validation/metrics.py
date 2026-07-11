"""Pure scoring functions producing honest, reproducible metric results.

Each metric carries an explicit ``method`` and honest ``limitations`` (synthetic
data, small held-out sample, single rule) per the Phase 7 quality bar. Values are
deterministic given the same seeded held-out inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from app.contracts.v1.enums import MetricCategory

_RATIO_QUANT = Decimal("0.0001")
_MIN_QUANT = Decimal("0.01")

_SYNTHETIC_LIMIT = (
    "Synthetic held-out data only; small sample; single anomaly rule "
    "(near_identical_amounts). Not production evidence."
)


@dataclass(frozen=True)
class MetricResult:
    metric_code: str
    category: MetricCategory
    value: Decimal
    unit: str
    sample_size: int
    method: str
    limitations: str
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class AnomalyCell:
    """One (scenario, provider) evaluation unit for the anomaly task."""

    scenario: str
    provider_code: str
    ground_truth_anomaly: bool  # labelled alertable anomaly expected
    predicted_alertable: bool  # detector emitted a requires_review flag


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return Decimal("0")
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        _RATIO_QUANT, rounding=ROUND_HALF_UP
    )


def anomaly_metrics(cells: list[AnomalyCell]) -> list[MetricResult]:
    """Precision, recall, and false-positive rate against held-out labels.

    A prediction is "alertable" when the detector emits a ``requires_review``
    anomaly flag. Suppressed (data-quality) flags are correctly non-alertable.
    """
    tp = sum(1 for c in cells if c.ground_truth_anomaly and c.predicted_alertable)
    fp = sum(1 for c in cells if not c.ground_truth_anomaly and c.predicted_alertable)
    fn = sum(1 for c in cells if c.ground_truth_anomaly and not c.predicted_alertable)
    tn = sum(1 for c in cells if not c.ground_truth_anomaly and not c.predicted_alertable)

    confusion = {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "cells": len(cells)}
    results: list[MetricResult] = []

    if tp + fp > 0:
        results.append(
            MetricResult(
                metric_code="anomaly_precision",
                category=MetricCategory.ANALYTICS,
                value=_ratio(tp, tp + fp),
                unit="ratio",
                sample_size=tp + fp,
                method=(
                    "true_positives / (true_positives + false_positives) over "
                    "held-out (scenario x provider) anomaly cells; alertable = "
                    "requires_review flag"
                ),
                limitations=_SYNTHETIC_LIMIT,
                details=confusion,
            )
        )
    if tp + fn > 0:
        results.append(
            MetricResult(
                metric_code="anomaly_recall",
                category=MetricCategory.ANALYTICS,
                value=_ratio(tp, tp + fn),
                unit="ratio",
                sample_size=tp + fn,
                method=(
                    "true_positives / (true_positives + false_negatives) over "
                    "held-out labelled anomaly cells"
                ),
                limitations=_SYNTHETIC_LIMIT,
                details=confusion,
            )
        )
    if fp + tn > 0:
        results.append(
            MetricResult(
                metric_code="anomaly_false_positive_rate",
                category=MetricCategory.ANALYTICS,
                value=_ratio(fp, fp + tn),
                unit="ratio",
                sample_size=fp + tn,
                method=(
                    "false_positives / (false_positives + true_negatives) over "
                    "held-out anomaly-negative cells (includes suppressed data-"
                    "quality case, which must not alert)"
                ),
                limitations=_SYNTHETIC_LIMIT,
                details=confusion,
            )
        )
    return results


def shortage_lead_time_metric(
    *, as_of_at: datetime, projected_shortage_at: datetime | None, sample_size: int
) -> MetricResult | None:
    """Lead time (minutes) between analysis time and the projected shortage.

    Measured on the held-out Scenario A shared-cash projection: how far ahead the
    forecast warns of the depletion it detects.
    """
    if projected_shortage_at is None or sample_size <= 0:
        return None
    minutes = Decimal(
        str((projected_shortage_at - as_of_at).total_seconds() / 60.0)
    ).quantize(_MIN_QUANT, rounding=ROUND_HALF_UP)
    return MetricResult(
        metric_code="shortage_lead_time_minutes",
        category=MetricCategory.ANALYTICS,
        value=minutes,
        unit="minutes",
        sample_size=sample_size,
        method=(
            "projected_shortage_at - as_of_at for the held-out Scenario A "
            "shared-cash liquidity projection"
        ),
        limitations=(
            "Single held-out shortage on synthetic data; lead time reflects the "
            "seeded depletion slope, not real-world demand."
        ),
        details={"as_of_at": as_of_at.isoformat(), "shortage_at": projected_shortage_at.isoformat()},
    )


def data_quality_incident_rate(*, incident_count: int, total_assessments: int) -> MetricResult | None:
    """Share of held-out provider feed assessments classified stale/missing/conflicting."""
    if total_assessments <= 0:
        return None
    return MetricResult(
        metric_code="data_quality_incident_rate",
        category=MetricCategory.RELIABILITY,
        value=_ratio(incident_count, total_assessments),
        unit="ratio",
        sample_size=total_assessments,
        method=(
            "provider feed assessments with status in {stale,missing,conflicting} "
            "/ total provider assessments across held-out runs"
        ),
        limitations="Synthetic feeds; incidents are seeded via Scenario C fault injection.",
        details={"incident_count": incident_count, "total_assessments": total_assessments},
    )


def alert_explanation_coverage(
    *, complete_alerts: int, total_alerts: int, sections: list[str]
) -> MetricResult | None:
    """Fraction of published high-impact alerts with a complete EN explanation."""
    if total_alerts <= 0:
        return None
    return MetricResult(
        metric_code="alert_explanation_coverage",
        category=MetricCategory.RELIABILITY,
        value=_ratio(complete_alerts, total_alerts),
        unit="ratio",
        sample_size=total_alerts,
        method=(
            "published high-impact alerts whose EN explanation has all sections "
            f"({', '.join(sections)}) / total published high-impact alerts"
        ),
        limitations="Held-out published alerts only; completeness checks non-empty text, not quality.",
        details={"complete_alerts": complete_alerts, "total_alerts": total_alerts},
    )
