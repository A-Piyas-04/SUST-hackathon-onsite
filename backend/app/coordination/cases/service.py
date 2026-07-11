"""Case service interfaces (master Section 9.16).

Owner: Member 2. The legal-transition decision core is the pure
`state_machine.py`; this service will, in Phase 4, wrap it with persistence,
optimistic concurrency, scope checks, idempotency, and same-transaction audit.
No production implementation exists in Phase 1.
"""
from __future__ import annotations

from typing import Any, Protocol

from app.coordination.cases.contracts import (
    AcknowledgeRequest,
    AssignmentRequest,
    EscalateRequest,
    NoteRequest,
    ResolveRequest,
    ReviewRequest,
)
from app.coordination.shared.references import CallerScope
from app.coordination.shared.service import NotImplementedServiceError


class CaseService(Protocol):
    def list_cases(self, caller: CallerScope, filters: dict[str, Any]) -> list[dict[str, Any]]: ...

    def get_case(self, caller: CallerScope, case_id: str) -> dict[str, Any]: ...

    def get_timeline(self, caller: CallerScope, case_id: str) -> list[dict[str, Any]]: ...

    def assign(self, caller: CallerScope, case_id: str, req: AssignmentRequest, idem: str) -> dict[str, Any]: ...

    def acknowledge(self, caller: CallerScope, case_id: str, req: AcknowledgeRequest, idem: str) -> dict[str, Any]: ...

    def escalate(self, caller: CallerScope, case_id: str, req: EscalateRequest, idem: str) -> dict[str, Any]: ...

    def resolve(self, caller: CallerScope, case_id: str, req: ResolveRequest, idem: str) -> dict[str, Any]: ...

    def add_note(self, caller: CallerScope, case_id: str, req: NoteRequest, idem: str) -> dict[str, Any]: ...

    def review(self, caller: CallerScope, case_id: str, req: ReviewRequest, idem: str) -> dict[str, Any]: ...


class ScaffoldCaseService:
    """Phase-1 placeholder; no persistence, no state transitions."""

    def _nope(self, what: str):
        raise NotImplementedServiceError(f"{what} is implemented in Phase 4")

    def list_cases(self, caller: CallerScope, filters: dict[str, Any]):
        self._nope("list_cases")

    def get_case(self, caller: CallerScope, case_id: str):
        self._nope("get_case")

    def get_timeline(self, caller: CallerScope, case_id: str):
        self._nope("get_timeline")

    def assign(self, caller, case_id, req, idem):
        self._nope("assign")

    def acknowledge(self, caller, case_id, req, idem):
        self._nope("acknowledge")

    def escalate(self, caller, case_id, req, idem):
        self._nope("escalate")

    def resolve(self, caller, case_id, req, idem):
        self._nope("resolve")

    def add_note(self, caller, case_id, req, idem):
        self._nope("add_note")

    def review(self, caller, case_id, req, idem):
        self._nope("review")
