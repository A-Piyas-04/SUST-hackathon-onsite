"""Database readiness checks for /health."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CRITICAL_TABLES = ("providers", "outlets", "schema_migrations")


@dataclass(frozen=True)
class DatabaseHealth:
    connected: bool
    schema_ok: bool
    migration_count: int
    error: str | None = None

    @property
    def ready(self) -> bool:
        return self.connected and self.schema_ok and self.migration_count > 0


async def check_database_ready(session: AsyncSession) -> DatabaseHealth:
    try:
        await session.execute(text("SELECT 1"))
        migration_count = int(
            (await session.execute(text("SELECT COUNT(*) FROM schema_migrations"))).scalar_one()
        )
        missing = []
        for table in CRITICAL_TABLES:
            exists = (
                await session.execute(
                    text(
                        "SELECT EXISTS ("
                        "  SELECT 1 FROM information_schema.tables "
                        "  WHERE table_schema = 'public' AND table_name = :table_name"
                        ")"
                    ),
                    {"table_name": table},
                )
            ).scalar_one()
            if not exists:
                missing.append(table)
        if missing:
            return DatabaseHealth(
                connected=True,
                schema_ok=False,
                migration_count=migration_count,
                error=f"Missing tables: {', '.join(missing)}",
            )
        return DatabaseHealth(
            connected=True,
            schema_ok=True,
            migration_count=migration_count,
        )
    except Exception as exc:  # noqa: BLE001 — health endpoint must not leak internals
        return DatabaseHealth(
            connected=False,
            schema_ok=False,
            migration_count=0,
            error=type(exc).__name__,
        )
