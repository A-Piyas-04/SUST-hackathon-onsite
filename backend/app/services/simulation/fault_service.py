"""Fault injection service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import FaultType, ProviderCode
from app.contracts.v1.simulation import CreateFaultRequest, FaultSummary, PatchFaultRequest
from app.core.errors import AppError
from app.services.constants import PROVIDER_IDS


async def create_fault(
    session: AsyncSession,
    run_id: UUID,
    request: CreateFaultRequest,
    *,
    actor_user_id: UUID | None = None,
) -> FaultSummary:
    run = await session.execute(
        text("SELECT simulation_run_id FROM simulation_runs WHERE simulation_run_id = :id"),
        {"id": run_id},
    )
    if run.first() is None:
        raise AppError("not_found", f"Simulation run {run_id} not found.", status_code=404)

    provider_id = request.provider_id
    if provider_id is None and "target_provider" in request.parameters:
        provider_id = PROVIDER_IDS.get(ProviderCode(str(request.parameters["target_provider"])))

    params = dict(request.parameters)
    if actor_user_id:
        params["actor_user_id"] = str(actor_user_id)

    fault_id = uuid4()
    scheduled = request.scheduled_at or datetime.now(timezone.utc)
    await session.execute(
        text(
            """
            INSERT INTO fault_injections (
              fault_injection_id, simulation_run_id, outlet_id, provider_id,
              fault_type, parameters, scheduled_at, is_enabled
            ) VALUES (
              :id, :run_id, :outlet_id, :provider_id, :fault_type,
              CAST(:parameters AS jsonb), :scheduled_at, true
            )
            """
        ),
        {
            "id": fault_id,
            "run_id": run_id,
            "outlet_id": request.outlet_id,
            "provider_id": provider_id,
            "fault_type": request.fault_type.value,
            "parameters": json.dumps(params),
            "scheduled_at": scheduled,
        },
    )
    return FaultSummary(
        fault_injection_id=fault_id,
        fault_type=request.fault_type,
        outlet_id=request.outlet_id,
        provider_id=provider_id,
        parameters=params,
        is_enabled=True,
        scheduled_at=scheduled,
    )


async def patch_fault(
    session: AsyncSession,
    run_id: UUID,
    fault_id: UUID,
    request: PatchFaultRequest,
) -> FaultSummary:
    result = await session.execute(
        text(
            """
            UPDATE fault_injections
            SET is_enabled = :enabled,
                ended_at = CASE WHEN :enabled THEN NULL ELSE now() END
            WHERE fault_injection_id = :fault_id AND simulation_run_id = :run_id
            RETURNING fault_injection_id, fault_type, outlet_id, provider_id,
                      parameters, is_enabled, scheduled_at, applied_at, ended_at
            """
        ),
        {"enabled": request.is_enabled, "fault_id": fault_id, "run_id": run_id},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError("not_found", f"Fault {fault_id} not found for run {run_id}.", status_code=404)
    return _row_to_fault(row)


async def list_faults(session: AsyncSession, run_id: UUID) -> list[FaultSummary]:
    result = await session.execute(
        text(
            """
            SELECT fault_injection_id, fault_type, outlet_id, provider_id,
                   parameters, is_enabled, scheduled_at, applied_at, ended_at
            FROM fault_injections WHERE simulation_run_id = :run_id
            ORDER BY scheduled_at
            """
        ),
        {"run_id": run_id},
    )
    return [_row_to_fault(r) for r in result.mappings().all()]


def _row_to_fault(row: Any) -> FaultSummary:
    return FaultSummary(
        fault_injection_id=row["fault_injection_id"],
        fault_type=FaultType(row["fault_type"]),
        outlet_id=row["outlet_id"],
        provider_id=row["provider_id"],
        parameters=row["parameters"] or {},
        is_enabled=row["is_enabled"],
        scheduled_at=row["scheduled_at"],
        applied_at=row.get("applied_at"),
        ended_at=row.get("ended_at"),
    )
