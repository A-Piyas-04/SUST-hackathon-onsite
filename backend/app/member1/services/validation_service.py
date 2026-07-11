from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.adapters.validation_payload import ValidationMetricPayload, get_placeholder_metrics
from app.member1.repositories import validation as validation_repo


async def get_validation_metrics(session: AsyncSession) -> list[ValidationMetricPayload]:
    rows = await validation_repo.list_validation_summary(session)
    if not rows:
        return get_placeholder_metrics()
    return [
        ValidationMetricPayload(
            metric_code=r["metric_code"],
            category=r["category"],
            value=float(r["value"]),
            unit=r["unit"],
            sample_size=r["sample_size"],
            method=r["method"],
            limitations=r["limitations"],
            computed_at=r["computed_at"] or datetime.now(timezone.utc),
        )
        for r in rows
    ]
