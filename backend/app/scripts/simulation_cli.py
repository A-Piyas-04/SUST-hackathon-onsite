"""CLI for simulation run/reset/fault operations."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from uuid import UUID

from app.core.auth import OUTLET1
from app.core.config import get_settings
from app.db.engine import create_engine, dispose_engine, set_engine
from app.db.session import get_session_factory, init_session_factory
from app.contracts.v1.enums import FaultType, ScenarioCode
from app.contracts.v1.simulation import CreateFaultRequest, CreateRunRequest, PatchFaultRequest
from app.db.transaction import transaction
from app.services.simulation import fault_service, run_service


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


async def cmd_run(args: argparse.Namespace) -> None:
    request = CreateRunRequest(
        scenario_code=ScenarioCode(args.scenario),
        seed=args.seed,
        outlet_id=UUID(args.outlet_id) if args.outlet_id else OUTLET1,
    )

    async def _run(session):
        return await run_service.create_run(session, request)

    result = await _with_session(_run)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


async def cmd_status(args: argparse.Namespace) -> None:
    run_id = UUID(args.run_id)

    async def _status(session):
        return await run_service.get_run(session, run_id)

    result = await _with_session(_status)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


async def cmd_reset(args: argparse.Namespace) -> None:
    run_id = UUID(args.run_id)

    async def _reset(session):
        return await run_service.reset_run(session, run_id)

    result = await _with_session(_reset)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


async def cmd_fault_add(args: argparse.Namespace) -> None:
    run_id = UUID(args.run_id)
    params: dict = {}
    if args.provider:
        params["target_provider"] = args.provider
    if args.delta:
        params["conflict_delta"] = args.delta
    if args.delay:
        params["delay_seconds"] = args.delay

    request = CreateFaultRequest(
        fault_type=FaultType(args.type),
        outlet_id=UUID(args.outlet_id) if args.outlet_id else OUTLET1,
        parameters=params,
    )

    async def _add(session):
        return await fault_service.create_fault(session, run_id, request)

    result = await _with_session(_add)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


async def cmd_fault_toggle(args: argparse.Namespace) -> None:
    run_id = UUID(args.run_id)
    fault_id = UUID(args.fault_id)
    request = PatchFaultRequest(is_enabled=args.enabled.lower() == "true")

    async def _toggle(session):
        return await fault_service.patch_fault(session, run_id, fault_id, request)

    result = await _with_session(_toggle)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3 simulation CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Start a simulation run")
    run_p.add_argument("--scenario", default="normal")
    run_p.add_argument("--seed", type=int, default=None)
    run_p.add_argument("--outlet-id", default=None)

    status_p = sub.add_parser("status", help="Get run status")
    status_p.add_argument("--run-id", required=True)

    reset_p = sub.add_parser("reset", help="Reset and re-run")
    reset_p.add_argument("--run-id", required=True)

    fault_p = sub.add_parser("fault", help="Fault operations")
    fault_sub = fault_p.add_subparsers(dest="fault_cmd", required=True)

    add_p = fault_sub.add_parser("add", help="Add fault")
    add_p.add_argument("--run-id", required=True)
    add_p.add_argument("--type", required=True)
    add_p.add_argument("--provider", default=None)
    add_p.add_argument("--delta", default=None)
    add_p.add_argument("--delay", type=int, default=None)
    add_p.add_argument("--outlet-id", default=None)

    toggle_p = fault_sub.add_parser("toggle", help="Toggle fault")
    toggle_p.add_argument("--run-id", required=True)
    toggle_p.add_argument("--fault-id", required=True)
    toggle_p.add_argument("--enabled", required=True, choices=["true", "false"])

    args = parser.parse_args(argv)

    if args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "status":
        asyncio.run(cmd_status(args))
    elif args.command == "reset":
        asyncio.run(cmd_reset(args))
    elif args.command == "fault":
        if args.fault_cmd == "add":
            asyncio.run(cmd_fault_add(args))
        else:
            asyncio.run(cmd_fault_toggle(args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
