"""In-app notification queue and read-state (docs/schema.md §10.10).

Notifications are queued when a case is opened, reassigned, or escalated, and can
be listed and marked read by the recipient. Read-state persists on the row.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.coordination import (
    NotificationListResponse,
    NotificationOutput,
)
from app.core.auth import UserContext
from app.core.authz import SafeNotFoundError, can_access_scope


async def queue_notification(
    session: AsyncSession,
    *,
    case_id: UUID,
    recipient_role: str,
    recipient_user_id: UUID | None,
    payload: dict[str, Any],
) -> UUID:
    notification_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO notifications (
              notification_id, case_id, recipient_user_id, recipient_role,
              channel, status, payload
            ) VALUES (
              :id, :case_id, :recipient_user_id, :recipient_role,
              'in_app', 'queued', CAST(:payload AS jsonb)
            )
            """
        ),
        {
            "id": notification_id,
            "case_id": case_id,
            "recipient_user_id": recipient_user_id,
            "recipient_role": recipient_role,
            "payload": json.dumps(payload),
        },
    )
    return notification_id


def _to_output(row) -> NotificationOutput:
    return NotificationOutput(
        notification_id=row["notification_id"],
        case_id=row["case_id"],
        recipient_user_id=row["recipient_user_id"],
        recipient_role=row["recipient_role"],
        channel=row["channel"],
        status=row["status"],
        payload=row["payload"] or {},
        queued_at=row["queued_at"],
        delivered_at=row["delivered_at"],
        read_at=row["read_at"],
    )


async def list_notifications(
    session: AsyncSession, user: UserContext
) -> NotificationListResponse:
    """Notifications addressed to the user directly, or role-routed to a case the
    user can access under provider boundaries."""
    result = await session.execute(
        text(
            """
            SELECT n.*, c.outlet_id AS case_outlet_id, c.provider_id AS case_provider_id
            FROM notifications n
            JOIN cases c ON c.case_id = n.case_id
            ORDER BY n.queued_at DESC
            """
        )
    )
    roles = {r.value for r in user.roles}
    out: list[NotificationOutput] = []
    for row in result.mappings().all():
        if row["recipient_user_id"] == user.user_id:
            out.append(_to_output(row))
            continue
        if row["recipient_role"] in roles and await can_access_scope(
            session,
            user,
            outlet_id=row["case_outlet_id"],
            provider_id=row["case_provider_id"],
        ):
            out.append(_to_output(row))
    return NotificationListResponse(
        notifications=out, generated_at=datetime.now(timezone.utc)
    )


async def mark_read(
    session: AsyncSession, user: UserContext, notification_id: UUID
) -> NotificationOutput:
    result = await session.execute(
        text(
            """
            SELECT n.*, c.outlet_id AS case_outlet_id, c.provider_id AS case_provider_id
            FROM notifications n
            JOIN cases c ON c.case_id = n.case_id
            WHERE n.notification_id = :id
            """
        ),
        {"id": notification_id},
    )
    row = result.mappings().first()
    if row is None:
        raise SafeNotFoundError("Notification")

    recipient_ok = row["recipient_user_id"] == user.user_id
    roles = {r.value for r in user.roles}
    role_ok = row["recipient_role"] in roles and await can_access_scope(
        session, user, outlet_id=row["case_outlet_id"], provider_id=row["case_provider_id"]
    )
    if not (recipient_ok or role_ok):
        raise SafeNotFoundError("Notification")

    now = datetime.now(timezone.utc)
    await session.execute(
        text(
            """
            UPDATE notifications
            SET status = 'read',
                read_at = :now,
                delivered_at = COALESCE(delivered_at, :now)
            WHERE notification_id = :id
            """
        ),
        {"id": notification_id, "now": now},
    )
    updated = await session.execute(
        text("SELECT * FROM notifications WHERE notification_id = :id"),
        {"id": notification_id},
    )
    return _to_output(updated.mappings().one())
