"""Tiny raw-SQL query helpers shared by every Member 1 repository.

Owner: Member 1. Uses SQLAlchemy's async engine/session (app/core/db.py) with
parameterized `text()` queries rather than a full declarative ORM model per
table — a deliberate hackathon-speed trade-off given the schema is already
frozen in docs/schema.md; there is no risk of drifting from a second
model definition because there isn't one.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def fetch_all(session: AsyncSession, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    result = await session.execute(text(query), params or {})
    return [dict(row._mapping) for row in result]


async def fetch_one(session: AsyncSession, query: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    rows = await fetch_all(session, query, params)
    return rows[0] if rows else None


async def execute(session: AsyncSession, query: str, params: dict[str, Any] | None = None) -> None:
    await session.execute(text(query), params or {})
