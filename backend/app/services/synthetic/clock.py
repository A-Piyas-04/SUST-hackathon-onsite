"""Deterministic simulation clock."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.constants import BASE_TIMESTAMP_ISO

_BASE = datetime.fromisoformat(BASE_TIMESTAMP_ISO)


def event_time(index: int, *, minute_step: int = 5) -> datetime:
    """Return a deterministic UTC timestamp for the given event index."""
    return _BASE + timedelta(minutes=index * minute_step)


def batch_time(batch_index: int, *, minute_step: int = 15) -> datetime:
    return _BASE + timedelta(minutes=batch_index * minute_step)
