"""Request-scoped async database sessions."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import get_engine

_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Session factory is not initialized.")
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session
