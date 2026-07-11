"""Performance metrics: in-process latency of representative read handlers.

Times the exact service functions behind the dashboard, liquidity-projections,
and anomaly-flags endpoints over a documented iteration count. This is honest but
in-process: it excludes network/TLS/serialization transport (stated in method).
Performance values vary run to run and are NOT part of the determinism guarantee.
"""

from __future__ import annotations

import time
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import MetricCategory
from app.services.analytics import reader as analytics_reader
from app.services.ledger import reader as ledger_reader
from app.services.validation.metrics import MetricResult

_MS_QUANT = Decimal("0.01")

_ENDPOINTS = ("outlet_dashboard", "liquidity_projections", "anomaly_flags")


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    idx = min(len(ordered) - 1, max(0, round(pct * (len(ordered) - 1))))
    return ordered[idx]


def _ms(value: float) -> Decimal:
    return Decimal(str(value)).quantize(_MS_QUANT, rounding=ROUND_HALF_UP)


async def measure_latency(
    session: AsyncSession, *, outlet_id: UUID, iterations: int
) -> list[MetricResult]:
    """Measure avg + p95 latency across representative read handlers."""
    durations_ms: list[float] = []
    for _ in range(iterations):
        for endpoint in _ENDPOINTS:
            start = time.perf_counter()
            if endpoint == "outlet_dashboard":
                await ledger_reader.get_dashboard(session, outlet_id)
            elif endpoint == "liquidity_projections":
                await analytics_reader.list_liquidity_projections(session, outlet_id)
            else:
                await analytics_reader.list_anomaly_flags(session, outlet_id)
            durations_ms.append((time.perf_counter() - start) * 1000.0)

    sample_size = len(durations_ms)
    if sample_size == 0:
        return []

    avg = sum(durations_ms) / sample_size
    p95 = _percentile(durations_ms, 0.95)
    details = {
        "endpoints": list(_ENDPOINTS),
        "iterations_per_endpoint": iterations,
        "total_requests": sample_size,
        "concurrency": 1,
    }
    method = (
        f"in-process handler timing over {iterations} iterations x "
        f"{len(_ENDPOINTS)} read endpoints ({', '.join(_ENDPOINTS)}); "
        "excludes network/serialization transport"
    )
    limit = "In-process timing on a single connection; not a networked load test."
    return [
        MetricResult(
            metric_code="api_avg_ms",
            category=MetricCategory.PERFORMANCE,
            value=_ms(avg),
            unit="milliseconds",
            sample_size=sample_size,
            method=method,
            limitations=limit,
            details=details,
        ),
        MetricResult(
            metric_code="api_p95_ms",
            category=MetricCategory.PERFORMANCE,
            value=_ms(p95),
            unit="milliseconds",
            sample_size=sample_size,
            method=method,
            limitations=limit,
            details=details,
        ),
    ]
