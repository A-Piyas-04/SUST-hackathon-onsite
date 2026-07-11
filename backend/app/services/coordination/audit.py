"""Atomic, append-only audit-event writes (docs/schema.md §10.12).

Every high-impact workflow mutation calls ``write_audit_event`` inside the same
transaction as the mutation, so an event is never missing and the history is
immutable and ordered. Actor/action/when/why/context are all captured.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserContext
from app.core.request_context import get_request_id


async def write_audit_event(
    session: AsyncSession,
    *,
    action: str,
    actor: UserContext | None,
    actor_type: str = "user",
    case_id: UUID | None = None,
    alert_id: UUID | None = None,
    provider_id: UUID | None = None,
    outlet_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    previous_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
) -> UUID:
    event_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO audit_events (
              audit_event_id, case_id, alert_id, provider_id, outlet_id,
              actor_user_id, actor_type, action, entity_type, entity_id,
              previous_values, new_values, request_id, occurred_at
            ) VALUES (
              :id, :case_id, :alert_id, :provider_id, :outlet_id,
              :actor_user_id, :actor_type, :action, :entity_type, :entity_id,
              CAST(:previous AS jsonb), CAST(:new AS jsonb), :request_id, :occurred_at
            )
            """
        ),
        {
            "id": event_id,
            "case_id": case_id,
            "alert_id": alert_id,
            "provider_id": provider_id,
            "outlet_id": outlet_id,
            "actor_user_id": actor.user_id if actor else None,
            "actor_type": actor_type,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "previous": json.dumps(previous_values) if previous_values is not None else None,
            "new": json.dumps(new_values) if new_values is not None else None,
            "request_id": get_request_id(),
            "occurred_at": datetime.now(timezone.utc),
        },
    )
    return event_id
