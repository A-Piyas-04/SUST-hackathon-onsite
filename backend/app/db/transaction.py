"""Explicit transaction helper with rollback safety."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    if session.in_transaction():
        async with session.begin_nested():
            yield session
    else:
        async with session.begin():
            yield session
