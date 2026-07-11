"""Case route scaffolds (schema.md 16.5).

Owner: Member 2. Explicit action endpoints only — NO generic `PATCH status`.
Runtime is Phase 4; every handler returns an honest 501. Audit reads live here
too (GET /{caseId}/audit-events) alongside the case timeline.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.coordination.cases.contracts import (
    AcknowledgeRequest,
    AssignmentRequest,
    EscalateRequest,
    NoteRequest,
    ResolveRequest,
    ReviewRequest,
)
from app.coordination.shared.http import not_implemented

cases_router = APIRouter(prefix="/api/v1/cases", tags=["coordination:cases"])


@cases_router.get("")
async def list_cases(request: Request):
    return not_implemented("Case list", request)


@cases_router.get("/{case_id}")
async def get_case(request: Request, case_id: str):
    return not_implemented("Case detail", request)


@cases_router.get("/{case_id}/timeline")
async def get_case_timeline(request: Request, case_id: str):
    return not_implemented("Case timeline", request)


@cases_router.get("/{case_id}/audit-events")
async def get_case_audit_events(request: Request, case_id: str):
    return not_implemented("Case audit events", request)


@cases_router.post("/{case_id}/assignments")
async def assign_case(request: Request, case_id: str, body: AssignmentRequest):
    return not_implemented("Case assignment", request)


@cases_router.post("/{case_id}/acknowledge")
async def acknowledge_case(request: Request, case_id: str, body: AcknowledgeRequest):
    return not_implemented("Case acknowledge", request)


@cases_router.post("/{case_id}/escalate")
async def escalate_case(request: Request, case_id: str, body: EscalateRequest):
    return not_implemented("Case escalate", request)


@cases_router.post("/{case_id}/resolve")
async def resolve_case(request: Request, case_id: str, body: ResolveRequest):
    return not_implemented("Case resolve", request)


@cases_router.post("/{case_id}/notes")
async def add_case_note(request: Request, case_id: str, body: NoteRequest):
    return not_implemented("Case note", request)


@cases_router.post("/{case_id}/review")
async def review_case(request: Request, case_id: str, body: ReviewRequest):
    return not_implemented("Case review", request)
