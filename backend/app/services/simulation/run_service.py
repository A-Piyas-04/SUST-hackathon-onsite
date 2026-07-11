"""Simulation run lifecycle orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import ScenarioCode, SimulationRunStatus
from app.contracts.v1.simulation import (
    CreateRunRequest,
    RunArtifactCounts,
    RunResponse,
    ScenarioListResponse,
    ScenarioResponse,
)
from app.core.auth import UserContext
from app.core.errors import AppError
from app.db.transaction import transaction
from app.services.ingestion.fault_effects import apply_faults_to_batches
from app.services.ingestion.pipeline import ingest_generated_batches, load_active_faults
from app.services.ledger.writer import count_ledger_rows
from app.services.simulation import fault_service, reset as reset_service
from app.services.synthetic import catalog
from app.services.synthetic.generator import generate_dataset


async def list_scenarios(session: AsyncSession) -> ScenarioListResponse:
    rows = await catalog.list_scenarios(session)
    return ScenarioListResponse(
        scenarios=[
            ScenarioResponse(
                scenario_id=r["scenario_id"],
                code=ScenarioCode(r["code"]),
                name=r["name"],
                description=r["description"],
                default_seed=int(r["default_seed"]),
                default_config=r["default_config"],
                validation_split=r["validation_split"],
                is_active=r["is_active"],
            )
            for r in rows
        ]
    )


async def create_run(
    session: AsyncSession,
    request: CreateRunRequest,
    user: UserContext | None = None,
) -> RunResponse:
    scenario_id, seed, config = await catalog.resolve_run_params(
        session, request.scenario_code, request.seed, request.config_overrides
    )
    config = dict(config)
    config["outlet_id"] = str(request.outlet_id)
    run_id = uuid4()
    started_at = datetime.now(timezone.utc)

    async with transaction(session):
        await session.execute(
            text(
                """
                INSERT INTO simulation_runs (
                  simulation_run_id, scenario_id, seed, config_snapshot, status,
                  started_by_user_id, started_at
                ) VALUES (
                  :id, :scenario_id, :seed, CAST(:config AS jsonb), :status,
                  :user_id, :started_at
                )
                """
            ),
            {
                "id": run_id,
                "scenario_id": scenario_id,
                "seed": seed,
                "config": json.dumps(config),
                "status": SimulationRunStatus.RUNNING.value,
                "user_id": user.user_id if user else None,
                "started_at": started_at,
            },
        )

        try:
            await _execute_run(
                session,
                run_id=run_id,
                scenario_code=request.scenario_code,
                seed=seed,
                config=config,
                outlet_id=request.outlet_id,
            )
            await session.execute(
                text(
                    """
                    UPDATE simulation_runs
                    SET status = :status, completed_at = :completed_at
                    WHERE simulation_run_id = :id
                    """
                ),
                {
                    "status": SimulationRunStatus.COMPLETED.value,
                    "completed_at": datetime.now(timezone.utc),
                    "id": run_id,
                },
            )
        except Exception as exc:
            await session.execute(
                text(
                    """
                    UPDATE simulation_runs
                    SET status = :status, completed_at = :completed_at, error_summary = :err
                    WHERE simulation_run_id = :id
                    """
                ),
                {
                    "status": SimulationRunStatus.FAILED.value,
                    "completed_at": datetime.now(timezone.utc),
                    "err": str(exc)[:500],
                    "id": run_id,
                },
            )
            raise

    return await get_run(session, run_id)


async def get_run(session: AsyncSession, run_id: UUID) -> RunResponse:
    result = await session.execute(
        text(
            """
            SELECT sr.*, sc.code AS scenario_code
            FROM simulation_runs sr
            JOIN simulation_scenarios sc ON sc.scenario_id = sr.scenario_id
            WHERE sr.simulation_run_id = :id
            """
        ),
        {"id": run_id},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError("not_found", f"Simulation run {run_id} not found.", status_code=404)

    counts = await _artifact_counts(session, run_id)
    faults = await fault_service.list_faults(session, run_id)

    return RunResponse(
        simulation_run_id=row["simulation_run_id"],
        scenario_id=row["scenario_id"],
        scenario_code=ScenarioCode(row["scenario_code"]),
        seed=int(row["seed"]),
        config_snapshot=row["config_snapshot"],
        status=SimulationRunStatus(row["status"]),
        started_by_user_id=row["started_by_user_id"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
        error_summary=row["error_summary"],
        faults=faults,
        artifacts=counts,
    )


async def reset_run(session: AsyncSession, run_id: UUID) -> RunResponse:
    result = await session.execute(
        text(
            """
            SELECT sr.seed, sr.config_snapshot, sc.code AS scenario_code
            FROM simulation_runs sr
            JOIN simulation_scenarios sc ON sc.scenario_id = sr.scenario_id
            WHERE sr.simulation_run_id = :id
            """
        ),
        {"id": run_id},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError("not_found", f"Simulation run {run_id} not found.", status_code=404)

    async with transaction(session):
        reset_count = int(row["config_snapshot"].get("reset_count", 0)) + 1
        updated_config = dict(row["config_snapshot"])
        updated_config["reset_count"] = reset_count
        await session.execute(
            text(
                """
                UPDATE simulation_runs
                SET status = :status, completed_at = NULL, error_summary = NULL,
                    config_snapshot = CAST(:config AS jsonb)
                WHERE simulation_run_id = :id
                """
            ),
            {
                "status": SimulationRunStatus.RESET.value,
                "config": json.dumps(updated_config),
                "id": run_id,
            },
        )
        await session.execute(
            text("UPDATE simulation_runs SET status = :status WHERE simulation_run_id = :id"),
            {"status": SimulationRunStatus.RUNNING.value, "id": run_id},
        )
        await _execute_run(
            session,
            run_id=run_id,
            scenario_code=ScenarioCode(row["scenario_code"]),
            seed=int(row["seed"]),
            config=updated_config,
            outlet_id=UUID(row["config_snapshot"]["outlet_id"])
            if row["config_snapshot"].get("outlet_id")
            else None,
            batch_suffix=f"R{reset_count}",
        )
        await session.execute(
            text(
                """
                UPDATE simulation_runs
                SET status = :status, completed_at = :completed_at
                WHERE simulation_run_id = :id
                """
            ),
            {
                "status": SimulationRunStatus.COMPLETED.value,
                "completed_at": datetime.now(timezone.utc),
                "id": run_id,
            },
        )

    return await get_run(session, run_id)


async def _execute_run(
    session: AsyncSession,
    *,
    run_id: UUID,
    scenario_code: ScenarioCode,
    seed: int,
    config: dict[str, Any],
    outlet_id: UUID | None,
    batch_suffix: str | None = None,
) -> None:
    from app.services.constants import DEFAULT_OUTLET_ID

    effective_outlet = outlet_id or DEFAULT_OUTLET_ID
    generation = generate_dataset(
        scenario_code=scenario_code,
        seed=seed,
        config=config,
        outlet_id=effective_outlet,
    )
    faults = await load_active_faults(session, run_id)
    batches = apply_faults_to_batches(generation.batches, faults, rng_seed=seed)
    suffix = batch_suffix or str(run_id)
    for batch in batches:
        batch.source_batch_ref = f"{batch.source_batch_ref}-RUN-{suffix}"
    await ingest_generated_batches(
        session,
        simulation_run_id=run_id,
        outlet_id=effective_outlet,
        batches=batches,
    )


async def _artifact_counts(session: AsyncSession, run_id: UUID) -> RunArtifactCounts:
    batch_result = await session.execute(
        text(
            """
            SELECT
              count(*) AS batches,
              coalesce(sum(received_event_count + rejected_event_count), 0) AS events
            FROM ingestion_batches WHERE simulation_run_id = :run_id
            """
        ),
        {"run_id": run_id},
    )
    batch_row = batch_result.mappings().one()
    ledger = await count_ledger_rows(session, run_id)
    return RunArtifactCounts(
        ingestion_batches=batch_row["batches"],
        ingestion_events=batch_row["events"],
        transactions=ledger["transactions"],
        cash_snapshots=ledger["cash_snapshots"],
        provider_snapshots=ledger["provider_snapshots"],
    )
