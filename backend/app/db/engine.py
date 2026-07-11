"""Async SQLAlchemy engine lifecycle."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings
from app.db.dsn import get_sync_dsn, to_async_dsn

_engine: AsyncEngine | None = None


def create_engine(settings: Settings) -> AsyncEngine:
    del settings  # reserved for future pool tuning
    async_dsn = to_async_dsn(get_sync_dsn())
    return create_async_engine(async_dsn, pool_pre_ping=True)


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database engine is not initialized.")
    return _engine


def set_engine(engine: AsyncEngine) -> None:
    global _engine
    _engine = engine


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
