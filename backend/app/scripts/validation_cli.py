"""CLI for the Phase 7 held-out validation harness.

    python -m app.scripts.validation_cli run

Runs the held-out evaluation deterministically, persists a completed
``validation_runs`` row with ground-truth labels and metric results, and writes
evidence artifacts to ``docs/evidence/``. Re-running with the same seeds yields
identical analytics metric values.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from uuid import UUID

from app.core.config import get_settings
from app.db.engine import create_engine, dispose_engine, set_engine
from app.db.session import get_session_factory, init_session_factory
from app.db.transaction import transaction
from app.services.validation import evidence, reader
from app.services.validation.harness import run_validation


async def _run() -> dict:
    settings = get_settings()
    engine = create_engine(settings)
    set_engine(engine)
    init_session_factory()
    factory = get_session_factory()
    try:
        async with factory() as session:
            # Single outer transaction so every write commits atomically (the
            # harness's inner transaction() blocks become savepoints).
            async with transaction(session):
                summary = await run_validation(session)
                run_id = UUID(summary["validation_run_id"])
                payloads = await reader.list_validation_runs(
                    session, validation_run_id=run_id
                )
            if payloads:
                paths = evidence.write_all(payloads[0])
                summary["artifacts"] = [str(p) for p in paths]
            return summary
    finally:
        await dispose_engine()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 7 validation harness CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="Run held-out validation and write evidence artifacts")
    args = parser.parse_args(argv)

    if args.command == "run":
        summary = asyncio.run(_run())
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
