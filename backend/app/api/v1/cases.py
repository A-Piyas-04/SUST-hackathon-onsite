"""Phase 5 case lifecycle routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.coordination import (
    AcknowledgeRequest,
    AssignmentRequest,
    AuditEventsResponse,
    CaseListResponse,
    CaseOutput,
    CaseTimelineResponse,
    EscalateRequest,
    NoteOutput,
    NoteRequest,
    OpenCaseRequest,
    ResolveRequest,
    ReviewOutput,
    ReviewRequest,
)
from app.core.auth import UserContext, require_authenticated
from app.db.session import get_db_session
from app.services.coordination import cases as cases_service

router = APIRouter(prefix="/api/v1", tags=["cases"])


@router.post("/alerts/{alert_id}/cases", response_model=CaseOutput)
async def open_case(
    alert_id: UUID,
    request: OpenCaseRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    case, created = await cases_service.open_case(session, user, alert_id, request)
    response.status_code = 201 if created else 200
    return case


@router.get("/cases", response_model=CaseListResponse)
async def list_cases(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
    status: str | None = None,
):
    return await cases_service.list_cases(session, user, status=status)


@router.get("/cases/{case_id}", response_model=CaseOutput)
async def get_case(
    case_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await cases_service.get_case(session, user, case_id)


@router.get("/cases/{case_id}/timeline", response_model=CaseTimelineResponse)
async def get_timeline(
    case_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await cases_service.get_timeline(session, user, case_id)


@router.get("/cases/{case_id}/audit-events", response_model=AuditEventsResponse)
async def get_audit_events(
    case_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await cases_service.get_audit_events(session, user, case_id)


@router.post("/cases/{case_id}/assignments", response_model=CaseOutput)
async def assign_case(
    case_id: UUID,
    request: AssignmentRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await cases_service.assign(session, user, case_id, request)


@router.post("/cases/{case_id}/acknowledge", response_model=CaseOutput)
async def acknowledge_case(
    case_id: UUID,
    request: AcknowledgeRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await cases_service.acknowledge(session, user, case_id, request)


@router.post("/cases/{case_id}/escalate", response_model=CaseOutput)
async def escalate_case(
    case_id: UUID,
    request: EscalateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await cases_service.escalate(session, user, case_id, request)


@router.post("/cases/{case_id}/resolve", response_model=CaseOutput)
async def resolve_case(
    case_id: UUID,
    request: ResolveRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await cases_service.resolve(session, user, case_id, request)


@router.post("/cases/{case_id}/notes", response_model=NoteOutput, status_code=201)
async def add_note(
    case_id: UUID,
    request: NoteRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await cases_service.add_note(session, user, case_id, request)


@router.post("/cases/{case_id}/review", response_model=ReviewOutput, status_code=201)
async def review_case(
    case_id: UUID,
    request: ReviewRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await cases_service.add_review(session, user, case_id, request)
