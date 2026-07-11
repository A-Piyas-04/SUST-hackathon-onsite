"""Bootstrap deterministic demo data after reference seeds.

Docker and first-run setups need simulation runs, analytics, published alerts,
and at least one routed case before the coordination tabs show meaningful data.
Safe to re-run: reuses existing seeded runs and skips work that is already present.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text

from app.contracts.v1.coordination import OpenCaseRequest
from app.contracts.v1.enums import ScenarioCode
from app.contracts.v1.simulation import CreateRunRequest
from app.core.auth import ADMIN, BKASH, BKASH_OPS, OUTLET1, get_demo_user
from app.core.config import get_settings
from app.db.engine import create_engine, dispose_engine, set_engine
from app.db.session import get_session_factory, init_session_factory
from app.db.transaction import transaction
from app.services.analytics import runner as analytics_runner
from app.services.coordination import alerts as alerts_service
from app.services.coordination import cases as cases_service
from app.services.simulation import run_service

DEFAULT_OUTLET = OUTLET1


@dataclass(frozen=True)
class ScenarioBootstrap:
    scenario_code: ScenarioCode
    seed: int
    liquidity: bool = False
    anomaly: bool = False
    publish: bool = False


BOOTSTRAP_SCENARIOS: tuple[ScenarioBootstrap, ...] = (
    ScenarioBootstrap(ScenarioCode.NORMAL, 1001, liquidity=True),
    ScenarioBootstrap(ScenarioCode.SCENARIO_A, 2001, liquidity=True, publish=True),
    ScenarioBootstrap(ScenarioCode.SCENARIO_B, 2002, liquidity=True, anomaly=True, publish=True),
    ScenarioBootstrap(ScenarioCode.SCENARIO_C, 2003, liquidity=True, anomaly=True),
)


async def _with_session(coro):
    settings = get_settings()
    engine = create_engine(settings)
    set_engine(engine)
    init_session_factory()
    factory = get_session_factory()
    try:
        async with factory() as session:
            async with transaction(session):
                return await coro(session)
    finally:
        await dispose_engine()


async def _existing_run_id(session, *, scenario_code: ScenarioCode, seed: int) -> UUID | None:
    result = await session.execute(
        text(
            """
            SELECT sr.simulation_run_id
            FROM simulation_runs sr
            JOIN simulation_scenarios sc ON sc.scenario_id = sr.scenario_id
            WHERE sc.code = :code AND sr.seed = :seed
              AND EXISTS (
                SELECT 1 FROM transactions t
                WHERE t.simulation_run_id = sr.simulation_run_id
              )
            ORDER BY sr.started_at
            LIMIT 1
            """
        ),
        {"code": scenario_code.value, "seed": seed},
    )
    row = result.first()
    return row[0] if row else None


async def _has_liquidity_projections(session, *, simulation_run_id: UUID, outlet_id: UUID) -> bool:
    result = await session.execute(
        text(
            """
            SELECT 1
            FROM liquidity_projections lp
            JOIN analytics_runs ar ON ar.analytics_run_id = lp.analytics_run_id
            WHERE ar.simulation_run_id = :run_id AND lp.outlet_id = :outlet_id
            LIMIT 1
            """
        ),
        {"run_id": simulation_run_id, "outlet_id": outlet_id},
    )
    return result.first() is not None


async def _has_anomaly_flags(session, *, simulation_run_id: UUID, outlet_id: UUID) -> bool:
    result = await session.execute(
        text(
            """
            SELECT 1
            FROM anomaly_flags af
            JOIN analytics_runs ar ON ar.analytics_run_id = af.analytics_run_id
            WHERE ar.simulation_run_id = :run_id AND af.outlet_id = :outlet_id
            LIMIT 1
            """
        ),
        {"run_id": simulation_run_id, "outlet_id": outlet_id},
    )
    return result.first() is not None


async def _has_active_alerts(session, *, simulation_run_id: UUID) -> bool:
    result = await session.execute(
        text(
            """
            SELECT 1
            FROM alerts
            WHERE simulation_run_id = :run_id AND state = 'active'
            LIMIT 1
            """
        ),
        {"run_id": simulation_run_id},
    )
    return result.first() is not None


async def _ensure_run(
    *,
    scenario_code: ScenarioCode,
    seed: int,
    outlet_id: UUID,
) -> tuple[UUID, bool]:
    async def _lookup(session):
        return await _existing_run_id(session, scenario_code=scenario_code, seed=seed)

    run_id = await _with_session(_lookup)
    if run_id is not None:
        print(
            f"  {scenario_code.value} seed {seed}: run already present ({run_id})",
            flush=True,
        )
        return run_id, False

    async def _create(session):
        return await run_service.create_run(
            session,
            CreateRunRequest(
                scenario_code=scenario_code,
                seed=seed,
                outlet_id=outlet_id,
            ),
        )

    run = await _with_session(_create)
    print(
        f"  {scenario_code.value} seed {seed}: run created "
        f"({run.artifacts.transactions} txns)",
        flush=True,
    )
    return run.simulation_run_id, True


async def _apply_scenario(
  spec: ScenarioBootstrap,
  *,
  outlet_id: UUID,
) -> dict:
    run_id, created_run = await _ensure_run(
        scenario_code=spec.scenario_code,
        seed=spec.seed,
        outlet_id=outlet_id,
    )
    ran_liquidity = False
    ran_anomaly = False
    published_count = 0

    if spec.publish:

        async def _needs_publish(session):
            return not await _has_active_alerts(session, simulation_run_id=run_id)

        if await _with_session(_needs_publish):
            admin = get_demo_user(ADMIN)
            assert admin is not None

            async def _publish(session):
                return await alerts_service.publish_from_run(
                    session,
                    admin,
                    simulation_run_id=run_id,
                    outlet_id=outlet_id,
                )

            result = await _with_session(_publish)
            published_count = len(result.published)
            ran_liquidity = True
            ran_anomaly = spec.anomaly
            print(
                f"  {spec.scenario_code.value}: published {published_count} alert(s)",
                flush=True,
            )
        else:
            print(f"  {spec.scenario_code.value}: active alerts already present — skipped publish.", flush=True)
    else:
        if spec.liquidity:

            async def _needs_liquidity(session):
                return not await _has_liquidity_projections(
                    session, simulation_run_id=run_id, outlet_id=outlet_id
                )

            if await _with_session(_needs_liquidity):

                async def _liquidity(session):
                    return await analytics_runner.run_liquidity(
                        session,
                        simulation_run_id=run_id,
                        outlet_id=outlet_id,
                    )

                result = await _with_session(_liquidity)
                ran_liquidity = True
                print(
                    f"  {spec.scenario_code.value}: liquidity analytics "
                    f"({len(result.projections)} projections)",
                    flush=True,
                )

        if spec.anomaly:

            async def _needs_anomaly(session):
                return not await _has_anomaly_flags(
                    session, simulation_run_id=run_id, outlet_id=outlet_id
                )

            if await _with_session(_needs_anomaly):

                async def _anomaly(session):
                    return await analytics_runner.run_anomalies(
                        session,
                        simulation_run_id=run_id,
                        outlet_id=outlet_id,
                    )

                result = await _with_session(_anomaly)
                ran_anomaly = True
                print(
                    f"  {spec.scenario_code.value}: anomaly analytics "
                    f"({len(result.flags)} flag(s), {result.suppressed_count} suppressed)",
                    flush=True,
                )

    return {
        "scenario_code": spec.scenario_code.value,
        "seed": spec.seed,
        "simulation_run_id": str(run_id),
        "created_run": created_run,
        "ran_liquidity": ran_liquidity,
        "ran_anomaly": ran_anomaly,
        "published_alerts": published_count,
    }


async def _ensure_demo_case(*, outlet_id: UUID) -> bool:
    async def _has_case(session):
        result = await session.execute(text("SELECT 1 FROM cases LIMIT 1"))
        return result.first() is not None

    if await _with_session(_has_case):
        print("  demo case already present — skipped.", flush=True)
        return False

    async def _find_alert(session):
        result = await session.execute(
            text(
                """
                SELECT alert_id
                FROM alerts
                WHERE outlet_id = :outlet_id
                  AND provider_id = :provider_id
                  AND state = 'active'
                  AND alert_type IN ('anomaly', 'combined', 'liquidity')
                ORDER BY detected_at
                LIMIT 1
                """
            ),
            {"outlet_id": outlet_id, "provider_id": BKASH},
        )
        row = result.first()
        return row[0] if row else None

    alert_id = await _with_session(_find_alert)
    if alert_id is None:
        print("  no publishable alert found for demo case — skipped.", flush=True)
        return False

    ops = get_demo_user(BKASH_OPS)
    assert ops is not None

    async def _open(session):
        case, _created = await cases_service.open_case(
            session,
            ops,
            alert_id,
            OpenCaseRequest(),
        )
        return case

    case = await _with_session(_open)
    print(f"  demo case opened: {case.case_number} ({case.case_id})", flush=True)
    return True


async def bootstrap(*, outlet_id: UUID = DEFAULT_OUTLET) -> dict:
    scenario_results = []
    for spec in BOOTSTRAP_SCENARIOS:
        scenario_results.append(await _apply_scenario(spec, outlet_id=outlet_id))
    opened_case = await _ensure_demo_case(outlet_id=outlet_id)
    return {"scenarios": scenario_results, "opened_demo_case": opened_case}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap demo simulation + coordination data")
    parser.add_argument("--outlet-id", default=str(DEFAULT_OUTLET))
    args = parser.parse_args(argv)

    print("bootstrapping demo data ...", flush=True)
    asyncio.run(bootstrap(outlet_id=UUID(args.outlet_id)))
    print("  demo bootstrap complete.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
