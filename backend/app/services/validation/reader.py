"""Read persisted validation runs and metrics into API contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import MetricCategory, ValidationSplit
from app.contracts.v1.validation import MetricResultDetail, ValidationMetricPayload


async def _metrics_for_run(session: AsyncSession, run_id: UUID) -> list[MetricResultDetail]:
    result = await session.execute(
        text(
            """
            SELECT metric_code, category, value, unit, sample_size, method,
                   limitations, details, computed_at
            FROM metric_results
            WHERE validation_run_id = :id
            ORDER BY category, metric_code
            """
        ),
        {"id": run_id},
    )
    return [
        MetricResultDetail(
            metric_code=r["metric_code"],
            category=MetricCategory(r["category"]),
            value=r["value"],
            unit=r["unit"],
            sample_size=r["sample_size"],
            method=r["method"],
            limitations=r["limitations"],
            details=r["details"],
            computed_at=r["computed_at"],
        )
        for r in result.mappings().all()
    ]


async def list_validation_runs(
    session: AsyncSession,
    *,
    validation_run_id: UUID | None = None,
    dataset_split: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[ValidationMetricPayload]:
    clauses: list[str] = []
    params: dict = {"limit": limit}
    if validation_run_id is not None:
        clauses.append("validation_run_id = :vr_id")
        params["vr_id"] = validation_run_id
    if dataset_split is not None:
        clauses.append("dataset_split = :split")
        params["split"] = dataset_split
    if status is not None:
        clauses.append("status = :status")
        params["status"] = status
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    result = await session.execute(
        text(
            f"""
            SELECT validation_run_id, name, dataset_split, engine_version,
                   configuration, status, started_at, completed_at
            FROM validation_runs
            {where}
            ORDER BY started_at DESC
            LIMIT :limit
            """
        ),
        params,
    )
    payloads: list[ValidationMetricPayload] = []
    for row in result.mappings().all():
        metrics = await _metrics_for_run(session, row["validation_run_id"])
        payloads.append(
            ValidationMetricPayload(
                validation_run_id=row["validation_run_id"],
                name=row["name"],
                dataset_split=ValidationSplit(row["dataset_split"]),
                engine_version=row["engine_version"],
                configuration=row["configuration"],
                status=row["status"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                metrics=metrics,
            )
        )
    return payloads


async def latest_summary_metrics(session: AsyncSession) -> list[dict]:
    """Latest completed metric per code, from ``v_validation_summary`` (for /metrics)."""
    result = await session.execute(
        text(
            """
            SELECT metric_code, category, value, unit, sample_size, method,
                   limitations, computed_at, validation_run_id,
                   validation_run_name, engine_version
            FROM v_validation_summary
            ORDER BY category, metric_code
            """
        )
    )
    rows = result.mappings().all()
    return [
        {
            "metric_code": r["metric_code"],
            "category": r["category"],
            "value": str(r["value"]),
            "unit": r["unit"],
            "sample_size": r["sample_size"],
            "method": r["method"],
            "limitations": r["limitations"],
            "computed_at": r["computed_at"].astimezone(timezone.utc).isoformat()
            if isinstance(r["computed_at"], datetime)
            else r["computed_at"],
            "validation_run_id": str(r["validation_run_id"]),
            "validation_run_name": r["validation_run_name"],
            "engine_version": r["engine_version"],
        }
        for r in rows
    ]
