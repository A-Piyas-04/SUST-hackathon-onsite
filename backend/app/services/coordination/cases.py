"""Case lifecycle: routing, legal transitions, optimistic concurrency, audit.

Guarantees (docs Phase 5 state rules):
  * explicit legal transition matrix (mirrors migration 004 DB trigger);
  * resolution preconditions (must be acknowledged/escalated first, with summary);
  * optimistic concurrency via the ``version`` column;
  * idempotency keys defend against duplicate mutations (migration 007);
  * every high-impact mutation writes an audit event atomically.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.coordination import (
    AcknowledgeRequest,
    AssignmentRequest,
    AuditEventOutput,
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
    SimilarCasesPanel,
    TimelineEvent,
)
from app.core.auth import UserContext
from app.core.authz import (
    ConcurrencyConflictError,
    IllegalTransitionError,
    SafeNotFoundError,
    can_access_scope,
)
from app.core.permissions import CaseAction, require_role_action
from app.db.transaction import transaction
from app.services.coordination import alerts as alerts_service
from app.services.coordination import audit, notifications, routing, similar_cases

# Legal case-status transitions (mirror of enforce_case_transition in 004).
_LEGAL_TRANSITIONS: set[tuple[str, str]] = {
    ("open", "acknowledged"),
    ("open", "escalated"),
    ("acknowledged", "escalated"),
    ("acknowledged", "resolved"),
    ("escalated", "resolved"),
}


# --------------------------------------------------------------------------- #
# Idempotency helpers (migration 007)
# --------------------------------------------------------------------------- #
async def _idem_lookup(
    session: AsyncSession, key: str | None, scope_key: str, action: str
) -> dict[str, Any] | None:
    if not key:
        return None
    result = await session.execute(
        text(
            """
            SELECT response_body FROM coordination_idempotency_keys
            WHERE idempotency_key = :k AND scope_key = :s AND action = :a
            """
        ),
        {"k": key, "s": scope_key, "a": action},
    )
    row = result.first()
    return row[0] if row else None


async def _idem_store(
    session: AsyncSession,
    key: str | None,
    scope_key: str,
    action: str,
    actor: UserContext,
    status: int,
    body: dict[str, Any],
) -> None:
    if not key:
        return
    await session.execute(
        text(
            """
            INSERT INTO coordination_idempotency_keys (
              idempotency_key, scope_key, action, actor_user_id,
              response_status, response_body
            ) VALUES (:k, :s, :a, :actor, :status, CAST(:body AS jsonb))
            ON CONFLICT ON CONSTRAINT pk_coordination_idempotency DO NOTHING
            """
        ),
        {
            "k": key,
            "s": scope_key,
            "a": action,
            "actor": actor.user_id,
            "status": status,
            "body": json.dumps(body),
        },
    )


# --------------------------------------------------------------------------- #
# Row mapping / loading
# --------------------------------------------------------------------------- #
def _to_output(row) -> CaseOutput:
    return CaseOutput(
        case_id=row["case_id"],
        case_number=row["case_number"],
        alert_id=row["alert_id"],
        outlet_id=row["outlet_id"],
        provider_id=row["provider_id"],
        routing_rule_id=row["routing_rule_id"],
        status=row["status"],
        current_owner_user_id=row["current_owner_user_id"],
        current_owner_role=row["current_owner_role"],
        recommended_next_step=row["recommended_next_step"],
        opened_at=row["opened_at"],
        acknowledged_at=row["acknowledged_at"],
        escalated_at=row["escalated_at"],
        resolved_at=row["resolved_at"],
        resolution_summary=row["resolution_summary"],
        version=row["version"],
        updated_at=row["updated_at"],
    )


async def _load_case(session: AsyncSession, case_id: UUID, *, for_update: bool = False):
    suffix = " FOR UPDATE" if for_update else ""
    result = await session.execute(
        text(f"SELECT * FROM cases WHERE case_id = :id{suffix}"), {"id": case_id}
    )
    return result.mappings().first()


async def _require_case(
    session: AsyncSession, user: UserContext, case_id: UUID, *, for_update: bool = False
):
    row = await _load_case(session, case_id, for_update=for_update)
    if row is None:
        raise SafeNotFoundError("Case")
    if not await can_access_scope(
        session, user, outlet_id=row["outlet_id"], provider_id=row["provider_id"]
    ):
        raise SafeNotFoundError("Case")
    return row


def _check_version(row, expected_version: int | None) -> None:
    if expected_version is not None and expected_version != row["version"]:
        raise ConcurrencyConflictError(
            f"Expected version {expected_version} but case is at version {row['version']}."
        )


def _check_transition(from_status: str, to_status: str) -> None:
    if (from_status, to_status) not in _LEGAL_TRANSITIONS:
        raise IllegalTransitionError(
            f"Cannot transition case from '{from_status}' to '{to_status}'."
        )


# --------------------------------------------------------------------------- #
# Open case
# --------------------------------------------------------------------------- #
async def open_case(
    session: AsyncSession, user: UserContext, alert_id: UUID, request: OpenCaseRequest
) -> tuple[CaseOutput, bool]:
    """Route and open a case from an alert. Idempotent: an alert has one case."""
    require_role_action(user, CaseAction.OPEN)
    async with transaction(session):
        alert = await alerts_service.require_alert(session, user, alert_id)

        existing = await session.execute(
            text("SELECT * FROM cases WHERE alert_id = :a"), {"a": alert_id}
        )
        existing_row = existing.mappings().first()
        if existing_row is not None:
            return _to_output(existing_row), False  # idempotent open

        outlet_area = (
            await session.execute(
                text("SELECT area_id FROM outlets WHERE outlet_id = :id"),
                {"id": alert["outlet_id"]},
            )
        ).scalar()
        decision = await routing.resolve_routing(
            session,
            provider_id=alert["provider_id"],
            outlet_area_id=outlet_area,
            alert_type=alert["alert_type"],
            severity=alert["severity"],
        )

        payload = alert["structured_payload"] or {}
        next_step = payload.get("recommended_next_step") or (
            "Review the analytical evidence and coordinate through the authorized process."
        )
        case_id = uuid4()
        case_number = f"CASE-{str(case_id)[:8].upper()}"
        await session.execute(
            text(
                """
                INSERT INTO cases (
                  case_id, case_number, alert_id, outlet_id, provider_id,
                  routing_rule_id, status, current_owner_user_id, current_owner_role,
                  recommended_next_step
                ) VALUES (
                  :id, :number, :alert_id, :outlet_id, :provider_id,
                  :rule_id, 'open', NULL, :owner_role, :next_step
                )
                """
            ),
            {
                "id": case_id,
                "number": case_number,
                "alert_id": alert_id,
                "outlet_id": alert["outlet_id"],
                "provider_id": alert["provider_id"],
                "rule_id": decision.routing_rule_id,
                "owner_role": decision.target_role,
                "next_step": next_step,
            },
        )
        await session.execute(
            text(
                """
                INSERT INTO case_status_history (
                  case_status_history_id, case_id, from_status, to_status,
                  changed_by_user_id, reason
                ) VALUES (gen_random_uuid(), :case_id, NULL, 'open', :user, :reason)
                """
            ),
            {"case_id": case_id, "user": user.user_id, "reason": "case opened from alert"},
        )
        await session.execute(
            text(
                """
                INSERT INTO case_assignments (
                  case_assignment_id, case_id, assigned_to_user_id, assigned_to_role,
                  assigned_by_user_id, reason, routing_rule_id, comment
                ) VALUES (
                  gen_random_uuid(), :case_id, NULL, :role, :by, 'initial_route',
                  :rule_id, :comment
                )
                """
            ),
            {
                "case_id": case_id,
                "role": decision.target_role,
                "by": user.user_id,
                "rule_id": decision.routing_rule_id,
                "comment": "initial routing",
            },
        )
        await notifications.queue_notification(
            session,
            case_id=case_id,
            recipient_role=decision.target_role,
            recipient_user_id=None,
            payload={
                "case_number": case_number,
                "event": "case_opened",
                "next_step": next_step,
            },
        )
        await audit.write_audit_event(
            session,
            action="case_opened",
            actor=user,
            actor_type="routing_engine",
            case_id=case_id,
            alert_id=alert_id,
            provider_id=alert["provider_id"],
            outlet_id=alert["outlet_id"],
            entity_type="case",
            entity_id=case_id,
            new_values={"status": "open", "owner_role": decision.target_role},
        )
        row = await _load_case(session, case_id)
        return _to_output(row), True


# --------------------------------------------------------------------------- #
# Status mutations
# --------------------------------------------------------------------------- #
async def _apply_status_change(
    session: AsyncSession,
    user: UserContext,
    case_id: UUID,
    *,
    to_status: str,
    expected_version: int | None,
    reason: str | None,
    extra_sets: str,
    extra_params: dict[str, Any],
    audit_action: str,
    notify_role: str | None = None,
) -> CaseOutput:
    row = await _require_case(session, user, case_id, for_update=True)
    _check_version(row, expected_version)
    _check_transition(row["status"], to_status)
    new_version = row["version"] + 1
    params = {
        "id": case_id,
        "to_status": to_status,
        "new_version": new_version,
        "cur_version": row["version"],
        **extra_params,
    }
    result = await session.execute(
        text(
            f"""
            UPDATE cases
            SET status = :to_status,
                version = :new_version,
                updated_at = now(){extra_sets}
            WHERE case_id = :id AND version = :cur_version
            """
        ),
        params,
    )
    if result.rowcount == 0:
        raise ConcurrencyConflictError()
    await session.execute(
        text(
            """
            INSERT INTO case_status_history (
              case_status_history_id, case_id, from_status, to_status,
              changed_by_user_id, reason
            ) VALUES (gen_random_uuid(), :case_id, :from_status, :to_status, :user, :reason)
            """
        ),
        {
            "case_id": case_id,
            "from_status": row["status"],
            "to_status": to_status,
            "user": user.user_id,
            "reason": reason,
        },
    )
    await audit.write_audit_event(
        session,
        action=audit_action,
        actor=user,
        case_id=case_id,
        alert_id=row["alert_id"],
        provider_id=row["provider_id"],
        outlet_id=row["outlet_id"],
        entity_type="case",
        entity_id=case_id,
        previous_values={"status": row["status"], "version": row["version"]},
        new_values={"status": to_status, "version": new_version},
    )
    if notify_role is not None:
        await notifications.queue_notification(
            session,
            case_id=case_id,
            recipient_role=notify_role,
            recipient_user_id=None,
            payload={"event": audit_action, "status": to_status},
        )
    updated = await _load_case(session, case_id)
    return _to_output(updated)


async def acknowledge(
    session: AsyncSession, user: UserContext, case_id: UUID, request: AcknowledgeRequest
) -> CaseOutput:
    require_role_action(user, CaseAction.ACKNOWLEDGE)
    scope_key = f"case:{case_id}"
    async with transaction(session):
        cached = await _idem_lookup(session, request.idempotency_key, scope_key, "acknowledge")
        if cached is not None:
            return CaseOutput.model_validate(cached)
        out = await _apply_status_change(
            session,
            user,
            case_id,
            to_status="acknowledged",
            expected_version=request.expected_version,
            reason=request.reason,
            extra_sets=", acknowledged_at = now()",
            extra_params={},
            audit_action="case_acknowledged",
        )
        await _idem_store(
            session, request.idempotency_key, scope_key, "acknowledge", user, 200,
            out.model_dump(mode="json"),
        )
        return out


async def escalate(
    session: AsyncSession, user: UserContext, case_id: UUID, request: EscalateRequest
) -> CaseOutput:
    require_role_action(user, CaseAction.ESCALATE)
    scope_key = f"case:{case_id}"
    async with transaction(session):
        cached = await _idem_lookup(session, request.idempotency_key, scope_key, "escalate")
        if cached is not None:
            return CaseOutput.model_validate(cached)
        target_role = (request.target_role.value if request.target_role else "risk_analyst")
        out = await _apply_status_change(
            session,
            user,
            case_id,
            to_status="escalated",
            expected_version=request.expected_version,
            reason=request.reason,
            extra_sets=", escalated_at = now(), current_owner_role = :owner_role, current_owner_user_id = NULL",
            extra_params={"owner_role": target_role},
            audit_action="case_escalated",
            notify_role=target_role,
        )
        # Record the escalation reassignment for the timeline.
        await session.execute(
            text(
                """
                INSERT INTO case_assignments (
                  case_assignment_id, case_id, assigned_to_user_id, assigned_to_role,
                  assigned_by_user_id, reason, comment
                ) VALUES (gen_random_uuid(), :case_id, NULL, :role, :by, 'escalation', :comment)
                """
            ),
            {"case_id": case_id, "role": target_role, "by": user.user_id, "comment": request.reason},
        )
        await _idem_store(
            session, request.idempotency_key, scope_key, "escalate", user, 200,
            out.model_dump(mode="json"),
        )
        return out


async def resolve(
    session: AsyncSession, user: UserContext, case_id: UUID, request: ResolveRequest
) -> CaseOutput:
    require_role_action(user, CaseAction.RESOLVE)
    scope_key = f"case:{case_id}"
    async with transaction(session):
        cached = await _idem_lookup(session, request.idempotency_key, scope_key, "resolve")
        if cached is not None:
            return CaseOutput.model_validate(cached)
        out = await _apply_status_change(
            session,
            user,
            case_id,
            to_status="resolved",
            expected_version=request.expected_version,
            reason=request.reason or "case resolved",
            extra_sets=", resolved_at = now(), resolution_summary = :summary",
            extra_params={"summary": request.resolution_summary},
            audit_action="case_resolved",
        )
        await _idem_store(
            session, request.idempotency_key, scope_key, "resolve", user, 200,
            out.model_dump(mode="json"),
        )
        try:
            await similar_cases.index_resolved_case(session, case_id)
        except Exception:
            pass
        return out


# --------------------------------------------------------------------------- #
# Assignment (does not change status)
# --------------------------------------------------------------------------- #
async def assign(
    session: AsyncSession, user: UserContext, case_id: UUID, request: AssignmentRequest
) -> CaseOutput:
    require_role_action(user, CaseAction.ASSIGN)
    scope_key = f"case:{case_id}"
    async with transaction(session):
        cached = await _idem_lookup(session, request.idempotency_key, scope_key, "assign")
        if cached is not None:
            return CaseOutput.model_validate(cached)
        row = await _require_case(session, user, case_id, for_update=True)
        _check_version(row, request.expected_version)
        new_version = row["version"] + 1
        result = await session.execute(
            text(
                """
                UPDATE cases
                SET current_owner_role = :role,
                    current_owner_user_id = :user_id,
                    version = :new_version,
                    updated_at = now()
                WHERE case_id = :id AND version = :cur_version
                """
            ),
            {
                "role": request.assigned_to_role.value,
                "user_id": request.assigned_to_user_id,
                "new_version": new_version,
                "cur_version": row["version"],
                "id": case_id,
            },
        )
        if result.rowcount == 0:
            raise ConcurrencyConflictError()
        await session.execute(
            text(
                """
                INSERT INTO case_assignments (
                  case_assignment_id, case_id, assigned_to_user_id, assigned_to_role,
                  assigned_by_user_id, reason, comment
                ) VALUES (gen_random_uuid(), :case_id, :to_user, :role, :by, :reason, :comment)
                """
            ),
            {
                "case_id": case_id,
                "to_user": request.assigned_to_user_id,
                "role": request.assigned_to_role.value,
                "by": user.user_id,
                "reason": request.assignment_reason.value,
                "comment": request.reason,
            },
        )
        await audit.write_audit_event(
            session,
            action="case_assigned",
            actor=user,
            case_id=case_id,
            alert_id=row["alert_id"],
            provider_id=row["provider_id"],
            outlet_id=row["outlet_id"],
            entity_type="case",
            entity_id=case_id,
            previous_values={"owner_role": row["current_owner_role"]},
            new_values={"owner_role": request.assigned_to_role.value},
        )
        await notifications.queue_notification(
            session,
            case_id=case_id,
            recipient_role=request.assigned_to_role.value,
            recipient_user_id=request.assigned_to_user_id,
            payload={"event": "case_assigned", "role": request.assigned_to_role.value},
        )
        out = _to_output(await _load_case(session, case_id))
        await _idem_store(
            session, request.idempotency_key, scope_key, "assign", user, 200,
            out.model_dump(mode="json"),
        )
        return out


# --------------------------------------------------------------------------- #
# Notes / reviews (append-only, no status change)
# --------------------------------------------------------------------------- #
async def add_note(
    session: AsyncSession, user: UserContext, case_id: UUID, request: NoteRequest
) -> NoteOutput:
    require_role_action(user, CaseAction.NOTE)
    scope_key = f"case:{case_id}"
    async with transaction(session):
        cached = await _idem_lookup(session, request.idempotency_key, scope_key, "note")
        if cached is not None:
            return NoteOutput.model_validate(cached)
        row = await _require_case(session, user, case_id, for_update=False)
        note_id = uuid4()
        await session.execute(
            text(
                """
                INSERT INTO case_notes (
                  case_note_id, case_id, author_user_id, note_text, note_type
                ) VALUES (:id, :case_id, :author, :text, :type)
                """
            ),
            {
                "id": note_id,
                "case_id": case_id,
                "author": user.user_id,
                "text": request.note_text,
                "type": request.note_type.value,
            },
        )
        await audit.write_audit_event(
            session,
            action="note_added",
            actor=user,
            case_id=case_id,
            alert_id=row["alert_id"],
            provider_id=row["provider_id"],
            outlet_id=row["outlet_id"],
            entity_type="case_note",
            entity_id=note_id,
            new_values={"note_type": request.note_type.value},
        )
        created = await session.execute(
            text("SELECT * FROM case_notes WHERE case_note_id = :id"), {"id": note_id}
        )
        r = created.mappings().one()
        out = NoteOutput(
            case_note_id=r["case_note_id"],
            case_id=r["case_id"],
            author_user_id=r["author_user_id"],
            note_text=r["note_text"],
            note_type=r["note_type"],
            created_at=r["created_at"],
        )
        await _idem_store(
            session, request.idempotency_key, scope_key, "note", user, 201,
            out.model_dump(mode="json"),
        )
        return out


async def add_review(
    session: AsyncSession, user: UserContext, case_id: UUID, request: ReviewRequest
) -> ReviewOutput:
    require_role_action(user, CaseAction.REVIEW)
    scope_key = f"case:{case_id}"
    async with transaction(session):
        cached = await _idem_lookup(session, request.idempotency_key, scope_key, "review")
        if cached is not None:
            return ReviewOutput.model_validate(cached)
        row = await _require_case(session, user, case_id, for_update=False)
        review_id = uuid4()
        await session.execute(
            text(
                """
                INSERT INTO case_reviews (
                  case_review_id, case_id, reviewed_by_user_id, disposition,
                  was_false_positive, review_summary
                ) VALUES (:id, :case_id, :by, :disposition, :fp, :summary)
                """
            ),
            {
                "id": review_id,
                "case_id": case_id,
                "by": user.user_id,
                "disposition": request.disposition.value,
                "fp": request.was_false_positive,
                "summary": request.review_summary,
            },
        )
        await audit.write_audit_event(
            session,
            action="case_reviewed",
            actor=user,
            case_id=case_id,
            alert_id=row["alert_id"],
            provider_id=row["provider_id"],
            outlet_id=row["outlet_id"],
            entity_type="case_review",
            entity_id=review_id,
            new_values={"disposition": request.disposition.value},
        )
        created = await session.execute(
            text("SELECT * FROM case_reviews WHERE case_review_id = :id"), {"id": review_id}
        )
        r = created.mappings().one()
        out = ReviewOutput(
            case_review_id=r["case_review_id"],
            case_id=r["case_id"],
            reviewed_by_user_id=r["reviewed_by_user_id"],
            disposition=r["disposition"],
            was_false_positive=r["was_false_positive"],
            review_summary=r["review_summary"],
            reviewed_at=r["reviewed_at"],
        )
        await _idem_store(
            session, request.idempotency_key, scope_key, "review", user, 201,
            out.model_dump(mode="json"),
        )
        return out


# --------------------------------------------------------------------------- #
# Reads
# --------------------------------------------------------------------------- #
async def get_case(session: AsyncSession, user: UserContext, case_id: UUID) -> CaseOutput:
    row = await _require_case(session, user, case_id)
    out = _to_output(row)
    try:
        out.similar_cases = await similar_cases.retrieve_similar_cases(
            session,
            case_id=row["case_id"],
            alert_id=row["alert_id"],
            provider_id=row["provider_id"],
        )
    except Exception:
        out.similar_cases = SimilarCasesPanel(status="unavailable", matches=[], message=None)
    return out


async def list_cases(
    session: AsyncSession, user: UserContext, *, status: str | None = None
) -> CaseListResponse:
    clauses = []
    params: dict[str, Any] = {}
    if status is not None:
        clauses.append("status = :status")
        params["status"] = status
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    result = await session.execute(
        text(f"SELECT * FROM cases{where} ORDER BY updated_at DESC"), params
    )
    cases: list[CaseOutput] = []
    for row in result.mappings().all():
        if await can_access_scope(
            session, user, outlet_id=row["outlet_id"], provider_id=row["provider_id"]
        ):
            cases.append(_to_output(row))
    return CaseListResponse(cases=cases, generated_at=datetime.now(timezone.utc))


async def get_timeline(
    session: AsyncSession, user: UserContext, case_id: UUID
) -> CaseTimelineResponse:
    await _require_case(session, user, case_id)
    result = await session.execute(
        text(
            """
            SELECT event_at, event_type, event_id, actor_user_id, detail
            FROM v_case_timeline
            WHERE case_id = :id
            ORDER BY event_at, event_type, event_id
            """
        ),
        {"id": case_id},
    )
    events = [
        TimelineEvent(
            event_at=r["event_at"],
            event_type=r["event_type"],
            event_id=r["event_id"],
            actor_user_id=r["actor_user_id"],
            detail=r["detail"] or {},
        )
        for r in result.mappings().all()
    ]
    return CaseTimelineResponse(
        case_id=case_id, events=events, generated_at=datetime.now(timezone.utc)
    )


async def get_audit_events(
    session: AsyncSession, user: UserContext, case_id: UUID
) -> AuditEventsResponse:
    await _require_case(session, user, case_id)
    result = await session.execute(
        text(
            """
            SELECT * FROM audit_events
            WHERE case_id = :id
            ORDER BY occurred_at, audit_event_id
            """
        ),
        {"id": case_id},
    )
    events = [
        AuditEventOutput(
            audit_event_id=r["audit_event_id"],
            case_id=r["case_id"],
            alert_id=r["alert_id"],
            provider_id=r["provider_id"],
            outlet_id=r["outlet_id"],
            actor_user_id=r["actor_user_id"],
            actor_type=r["actor_type"],
            action=r["action"],
            entity_type=r["entity_type"],
            entity_id=r["entity_id"],
            previous_values=r["previous_values"],
            new_values=r["new_values"],
            request_id=r["request_id"],
            occurred_at=r["occurred_at"],
        )
        for r in result.mappings().all()
    ]
    return AuditEventsResponse(
        case_id=case_id, events=events, generated_at=datetime.now(timezone.utc)
    )
