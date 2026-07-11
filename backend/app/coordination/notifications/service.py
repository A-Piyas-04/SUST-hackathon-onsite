"""Notification service interface (master Section 9.16).

Owner: Member 2. In-app notifications only in the MVP. Runtime is Phase 4.
Payloads must carry only safe, provider-scoped summaries (no cross-provider
confidential data) — enforced when implemented.
"""
from __future__ import annotations

from typing import Any, Protocol

from app.coordination.shared.references import CallerScope
from app.coordination.shared.service import NotImplementedServiceError


class NotificationService(Protocol):
    def list_notifications(self, caller: CallerScope, filters: dict[str, Any]) -> list[dict[str, Any]]: ...

    def mark_read(self, caller: CallerScope, notification_id: str, idem: str) -> dict[str, Any]: ...


class ScaffoldNotificationService:
    def list_notifications(self, caller: CallerScope, filters: dict[str, Any]):
        raise NotImplementedServiceError("list_notifications is implemented in Phase 4")

    def mark_read(self, caller: CallerScope, notification_id: str, idem: str):
        raise NotImplementedServiceError("mark_read is implemented in Phase 4")
