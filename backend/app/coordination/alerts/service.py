"""Alert service interfaces (master Section 9.16).

Owner: Member 2. Query/consume interfaces as Protocols. The candidate-consumer
*validation* logic already exists as a pure function in `candidate.py`; the
service that PERSISTS an immutable alert from an accepted candidate is Phase 3.
"""
from __future__ import annotations

from typing import Any, Protocol

from app.coordination.alerts.candidate import AlertCandidate, CandidateValidationResult
from app.coordination.shared.references import CallerScope
from app.coordination.shared.service import NotImplementedServiceError


class AlertService(Protocol):
    def list_alerts(self, caller: CallerScope, filters: dict[str, Any]) -> list[dict[str, Any]]: ...

    def get_alert(self, caller: CallerScope, alert_id: str) -> dict[str, Any]: ...

    def get_explanations(self, caller: CallerScope, alert_id: str, locale: str | None) -> list[dict[str, Any]]: ...

    def consume_candidate(self, candidate: AlertCandidate) -> CandidateValidationResult: ...

    def open_case(self, caller: CallerScope, alert_id: str, idempotency_key: str) -> dict[str, Any]: ...


class ScaffoldAlertService:
    """Phase-1 placeholder; no persistence."""

    def list_alerts(self, caller: CallerScope, filters: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedServiceError("list_alerts is implemented in Phase 2/3")

    def get_alert(self, caller: CallerScope, alert_id: str) -> dict[str, Any]:
        raise NotImplementedServiceError("get_alert is implemented in Phase 3")

    def get_explanations(self, caller: CallerScope, alert_id: str, locale: str | None) -> list[dict[str, Any]]:
        raise NotImplementedServiceError("get_explanations is implemented in Phase 3")

    def consume_candidate(self, candidate: AlertCandidate) -> CandidateValidationResult:
        raise NotImplementedServiceError("candidate persistence is implemented in Phase 3")

    def open_case(self, caller: CallerScope, alert_id: str, idempotency_key: str) -> dict[str, Any]:
        raise NotImplementedServiceError("open_case is implemented in Phase 3")
