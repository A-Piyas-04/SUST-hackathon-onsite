"""Scenario catalog loaded from simulation_scenarios."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import ScenarioCode
from app.core.errors import AppError


async def get_scenario_by_code(session: AsyncSession, code: ScenarioCode) -> dict[str, Any]:
    result = await session.execute(
        text(
            """
            SELECT scenario_id, code, name, description, default_seed, default_config,
                   validation_split, is_active
            FROM simulation_scenarios
            WHERE code = :code AND is_active
            """
        ),
        {"code": code.value},
    )
    row = result.mappings().first()
    if row is None:
        raise AppError("not_found", f"Scenario '{code.value}' not found.", status_code=404)
    return dict(row)


async def list_scenarios(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(
        text(
            """
            SELECT scenario_id, code, name, description, default_seed, default_config,
                   validation_split, is_active
            FROM simulation_scenarios
            WHERE is_active
            ORDER BY code
            """
        )
    )
    return [dict(r) for r in result.mappings().all()]


def merge_config(default_config: dict[str, Any], overrides: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(default_config)
    if overrides:
        merged.update(overrides)
    return merged


async def resolve_run_params(
    session: AsyncSession,
    scenario_code: ScenarioCode,
    seed: int | None,
    config_overrides: dict[str, Any] | None,
) -> tuple[UUID, int, dict[str, Any]]:
    scenario = await get_scenario_by_code(session, scenario_code)
    effective_seed = seed if seed is not None else int(scenario["default_seed"])
    config = merge_config(scenario["default_config"], config_overrides)
    return scenario["scenario_id"], effective_seed, config
