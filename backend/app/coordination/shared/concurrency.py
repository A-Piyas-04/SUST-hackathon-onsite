"""Optimistic-concurrency / version policy for case mutations.

Owner: Member 2. Pure-stdlib policy + validator. Database-level optimistic
locking is a later phase; Phase 1 freezes the contract.

Frozen decisions (member-2 plan Section 6.3; schema.md `cases.version`):
  * A case carries an integer `version`, default 1, incremented by exactly 1 on
    every successful mutation (transition, assignment, note, review).
  * A case mutation MUST supply the expected version, via either the request
    body field `version` or the `If-Match` header. If both are supplied they
    must agree; disagreement is a client error.
  * If the supplied version != the current version, the write is rejected with
    409 VERSION_CONFLICT and NOTHING changes (no state, no audit, no
    notification). The client must re-read and retry.
  * `If-Match` values may be quoted ETags (`"3"`); quotes are stripped.

This module decides accept/reject and the resulting error; the actual
compare-and-swap against the DB row belongs to the case service in Phase 4.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.coordination.shared.errors import ApiError, ErrorCode, new_request_id

IF_MATCH_HEADER = "If-Match"


@dataclass(frozen=True)
class VersionCheck:
    """Outcome of reconciling the caller's expected version."""

    expected_version: int


def _parse_if_match(if_match: str | None) -> int | None:
    if if_match is None:
        return None
    token = if_match.strip().strip('"')
    if token in ("*", ""):
        return None
    try:
        return int(token)
    except ValueError:
        return None


def resolve_expected_version(
    *,
    body_version: int | None,
    if_match: str | None,
    request_id: str | None = None,
) -> VersionCheck:
    """Determine the caller's expected version from body + header.

    Rules: at least one source required; if both present they must agree.
    Raises ApiError(VERSION_REQUIRED / VALIDATION_ERROR) on violation.
    """
    request_id = request_id or new_request_id()
    header_version = _parse_if_match(if_match)

    if body_version is None and header_version is None:
        raise ApiError(
            code=ErrorCode.VERSION_REQUIRED,
            message="A current case version is required (body `version` or If-Match).",
            request_id=request_id,
            details={"required": "version"},
        )
    if (
        body_version is not None
        and header_version is not None
        and body_version != header_version
    ):
        raise ApiError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Body `version` and If-Match header disagree.",
            request_id=request_id,
            details={"field": "version"},
        )
    expected = body_version if body_version is not None else header_version
    assert expected is not None  # for type-checkers; guaranteed by checks above
    return VersionCheck(expected_version=expected)


def check_version(
    *,
    current_version: int,
    expected_version: int,
    request_id: str | None = None,
) -> None:
    """Compare-and-guard. Raises 409 VERSION_CONFLICT if stale; else returns.

    A stale write must be a pure no-op for the caller — this raises BEFORE any
    mutation, and the case service must not write state/audit on this path.
    """
    request_id = request_id or new_request_id()
    if expected_version != current_version:
        raise ApiError(
            code=ErrorCode.VERSION_CONFLICT,
            message="The case was modified by someone else. Re-read and retry.",
            request_id=request_id,
            details={"expected_version": current_version},
        )


def next_version(current_version: int) -> int:
    """Version increment semantics: +1 per successful mutation."""
    return current_version + 1
