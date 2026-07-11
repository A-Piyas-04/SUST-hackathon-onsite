"""Case action request contracts (schema.md 16.5; member-2 plan 7.2).

Owner: Member 2. Each workflow transition uses an EXPLICIT action endpoint with
transition-specific validation — there is no generic `PATCH status`. Mutating
bodies carry the expected `version` (optimistic concurrency); the
`Idempotency-Key` travels as a header, validated by `shared.idempotency`.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.coordination.shared.enums import AppRole, NoteType, ReviewOutcome


class _Versioned(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(..., ge=1, description="Expected current case version (optimistic lock).")


class AcknowledgeRequest(_Versioned):
    pass


class EscalateRequest(_Versioned):
    target_role: AppRole
    target_user_id: str | None = None
    reason: str = Field(..., min_length=1, max_length=2000)


class ResolveRequest(_Versioned):
    resolution_summary: str = Field(..., min_length=1, max_length=4000)


class AssignmentRequest(_Versioned):
    assigned_to_role: AppRole
    assigned_to_user_id: str | None = None
    comment: str | None = Field(default=None, max_length=2000)


class NoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note_text: str = Field(..., min_length=1, max_length=4000)
    note_type: NoteType = NoteType.GENERAL


class ReviewRequest(BaseModel):
    """Review outcome is advisory and NEVER a fraud verdict — enforced by the
    `ReviewOutcome` enum (no fraud value exists)."""

    model_config = ConfigDict(extra="forbid")
    disposition: ReviewOutcome
    was_false_positive: bool | None = None
    review_summary: str = Field(..., min_length=1, max_length=4000)
