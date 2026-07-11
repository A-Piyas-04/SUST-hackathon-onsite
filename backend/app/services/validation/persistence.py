"""Append-only persistence for validation runs, labels, and metric results."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.validation.ground_truth import GroundTruthLabel
from app.services.validation.metrics import MetricResult


async def create_validation_run(
    session: AsyncSession,
    *,
    name: str,
    dataset_split: str,
    engine_version: str,
    configuration: dict,
    created_by_user_id: UUID | None = None,
) -> UUID:
    run_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO validation_runs (
              validation_run_id, name, dataset_split, engine_version,
              configuration, started_at, status, created_by_user_id
            ) VALUES (
              :id, :name, :split, :engine_version, CAST(:config AS jsonb),
              :started_at, 'running', :user_id
            )
            """
        ),
        {
            "id": run_id,
            "name": name,
            "split": dataset_split,
            "engine_version": engine_version,
            "config": json.dumps(configuration),
            "started_at": datetime.now(timezone.utc),
            "user_id": created_by_user_id,
        },
    )
    return run_id


async def insert_labels(
    session: AsyncSession,
    *,
    validation_run_id: UUID,
    simulation_run_id: UUID,
    labels: list[GroundTruthLabel],
) -> int:
    for label in labels:
        await session.execute(
            text(
                """
                INSERT INTO ground_truth_labels (
                  ground_truth_label_id, validation_run_id, simulation_run_id,
                  outlet_id, provider_id, label_type, expected_value,
                  window_start, window_end
                ) VALUES (
                  gen_random_uuid(), :vr_id, :sim_id, :outlet_id, :provider_id,
                  :label_type, CAST(:expected AS jsonb), :window_start, :window_end
                )
                """
            ),
            {
                "vr_id": validation_run_id,
                "sim_id": simulation_run_id,
                "outlet_id": label.outlet_id,
                "provider_id": label.provider_id,
                "label_type": label.label_type,
                "expected": json.dumps(label.expected_value),
                "window_start": label.window_start,
                "window_end": label.window_end,
            },
        )
    return len(labels)


async def insert_metrics(
    session: AsyncSession, *, validation_run_id: UUID, metrics: list[MetricResult]
) -> int:
    for metric in metrics:
        await session.execute(
            text(
                """
                INSERT INTO metric_results (
                  metric_result_id, validation_run_id, metric_code, category,
                  value, unit, sample_size, method, limitations, details, computed_at
                ) VALUES (
                  gen_random_uuid(), :vr_id, :code, :category, :value, :unit,
                  :sample_size, :method, :limitations, CAST(:details AS jsonb), :computed_at
                )
                """
            ),
            {
                "vr_id": validation_run_id,
                "code": metric.metric_code,
                "category": metric.category.value,
                "value": metric.value,
                "unit": metric.unit,
                "sample_size": metric.sample_size,
                "method": metric.method,
                "limitations": metric.limitations,
                "details": json.dumps(metric.details or {}),
                "computed_at": datetime.now(timezone.utc),
            },
        )
    return len(metrics)


async def finish_validation_run(
    session: AsyncSession,
    *,
    validation_run_id: UUID,
    status: str,
) -> None:
    await session.execute(
        text(
            """
            UPDATE validation_runs
            SET status = :status, completed_at = :completed_at
            WHERE validation_run_id = :id
            """
        ),
        {
            "status": status,
            "completed_at": datetime.now(timezone.utc),
            "id": validation_run_id,
        },
    )
