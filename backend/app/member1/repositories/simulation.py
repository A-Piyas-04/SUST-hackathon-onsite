from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories.db import fetch_all, fetch_one


async def list_scenarios(session: AsyncSession) -> list[dict]:
    return await fetch_all(
        session,
        "SELECT scenario_id, code, name, description, default_seed, is_active FROM simulation_scenarios WHERE is_active ORDER BY code",
    )


async def get_scenario_by_code(session: AsyncSession, code: str) -> dict | None:
    return await fetch_one(
        session,
        "SELECT scenario_id, code, name, description, default_seed FROM simulation_scenarios WHERE code = :code",
        {"code": code},
    )


async def create_simulation_run(session: AsyncSession, *, scenario_id: UUID, seed: int, config: dict[str, Any]) -> dict:
    row = await fetch_one(
        session,
        """
        INSERT INTO simulation_runs (scenario_id, seed, config_snapshot, status, started_at)
        VALUES (:scenario_id, :seed, :config, 'running', now())
        RETURNING simulation_run_id, scenario_id, seed, status, started_at, completed_at, error_summary
        """,
        {"scenario_id": str(scenario_id), "seed": seed, "config": json.dumps(config)},
    )
    assert row is not None
    return row


async def get_simulation_run(session: AsyncSession, run_id: UUID) -> dict | None:
    return await fetch_one(
        session,
        "SELECT simulation_run_id, scenario_id, seed, status, started_at, completed_at, error_summary FROM simulation_runs WHERE simulation_run_id = :run_id",
        {"run_id": str(run_id)},
    )


async def mark_simulation_run_reset(session: AsyncSession, run_id: UUID) -> dict | None:
    return await fetch_one(
        session,
        """
        UPDATE simulation_runs SET status = 'reset', completed_at = now()
        WHERE simulation_run_id = :run_id
        RETURNING simulation_run_id, scenario_id, seed, status, started_at, completed_at, error_summary
        """,
        {"run_id": str(run_id)},
    )


async def create_fault_injection(
    session: AsyncSession,
    *,
    simulation_run_id: UUID,
    outlet_id: UUID,
    provider_id: UUID | None,
    fault_type: str,
    parameters: dict[str, Any],
    scheduled_at: datetime,
) -> dict:
    row = await fetch_one(
        session,
        """
        INSERT INTO fault_injections (simulation_run_id, outlet_id, provider_id, fault_type, parameters, scheduled_at)
        VALUES (:simulation_run_id, :outlet_id, :provider_id, :fault_type, :parameters, :scheduled_at)
        RETURNING fault_injection_id, simulation_run_id, outlet_id, provider_id, fault_type, parameters,
                  scheduled_at, applied_at, ended_at, is_enabled
        """,
        {
            "simulation_run_id": str(simulation_run_id),
            "outlet_id": str(outlet_id),
            "provider_id": str(provider_id) if provider_id else None,
            "fault_type": fault_type,
            "parameters": json.dumps(parameters),
            "scheduled_at": scheduled_at,
        },
    )
    assert row is not None
    return row


async def set_fault_injection_enabled(session: AsyncSession, fault_injection_id: UUID, is_enabled: bool) -> dict | None:
    return await fetch_one(
        session,
        """
        UPDATE fault_injections SET is_enabled = :is_enabled
        WHERE fault_injection_id = :fault_injection_id
        RETURNING fault_injection_id, simulation_run_id, outlet_id, provider_id, fault_type, parameters,
                  scheduled_at, applied_at, ended_at, is_enabled
        """,
        {"fault_injection_id": str(fault_injection_id), "is_enabled": is_enabled},
    )
