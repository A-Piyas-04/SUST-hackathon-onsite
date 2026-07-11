"""Safe API error policy (schema.md Section 16, member-2 plan Section 6.3).

Owner: Member 2. Pure-stdlib so the policy is testable without FastAPI.

Every error rendered by a Member 2 endpoint uses exactly one shape:

    { "error": { "code", "message", "request_id", "details" } }

Invariants enforced/verified here:
  * `request_id` is always present (correlation ID).
  * A forbidden cross-provider lookup and a genuinely missing record produce the
    *identical* external shape — both use `NOT_FOUND` / HTTP 404 with the same
    message and empty details. Existence is never revealed via a different code,
    message, status, or detail field.
  * `details` carries only safe, non-confidential data. `redact_details` and
    the CI-style leak scan guard against tokens, another provider's IDs, and raw
    evidence leaking into a client-visible error.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """Stable, client-safe error codes. None of these reveal record existence
    beyond the deliberately-identical NOT_FOUND used for missing *and*
    forbidden-cross-provider lookups."""

    # Auth / identity
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    INACTIVE_USER = "INACTIVE_USER"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"

    # Authorization — NOTE: FORBIDDEN is only for actions on a resource the
    # caller may *see* but not perform (e.g. wrong role for a transition). A
    # cross-provider record the caller may not even know exists must use
    # NOT_FOUND, never FORBIDDEN, so existence is not disclosed.
    FORBIDDEN = "FORBIDDEN"

    # Existence — the single shape for "missing OR forbidden-cross-provider".
    NOT_FOUND = "NOT_FOUND"

    # Request validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_LOCALE = "INVALID_LOCALE"

    # Idempotency / concurrency
    IDEMPOTENCY_KEY_REQUIRED = "IDEMPOTENCY_KEY_REQUIRED"
    IDEMPOTENCY_KEY_INVALID = "IDEMPOTENCY_KEY_INVALID"
    IDEMPOTENCY_KEY_CONFLICT = "IDEMPOTENCY_KEY_CONFLICT"
    VERSION_REQUIRED = "VERSION_REQUIRED"
    VERSION_CONFLICT = "VERSION_CONFLICT"

    # Workflow
    ILLEGAL_TRANSITION = "ILLEGAL_TRANSITION"
    MISSING_TRANSITION_DATA = "MISSING_TRANSITION_DATA"
    UNSAFE_CONTENT = "UNSAFE_CONTENT"

    # Candidate ingestion (internal surface; see candidate.RejectionCode for the
    # fine-grained, non-client-facing reasons).
    CANDIDATE_REJECTED = "CANDIDATE_REJECTED"

    # Not implemented in this phase.
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


#: HTTP status codes that go with each error code. The mapping is intentionally
#: coarse; the point is that NOT_FOUND is always 404 whether the record is
#: missing or cross-provider-forbidden.
HTTP_STATUS: dict[str, int] = {
    ErrorCode.INVALID_CREDENTIALS: 401,
    ErrorCode.INACTIVE_USER: 401,
    ErrorCode.UNAUTHENTICATED: 401,
    ErrorCode.TOKEN_EXPIRED: 401,
    ErrorCode.TOKEN_INVALID: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.INVALID_LOCALE: 422,
    ErrorCode.IDEMPOTENCY_KEY_REQUIRED: 400,
    ErrorCode.IDEMPOTENCY_KEY_INVALID: 400,
    ErrorCode.IDEMPOTENCY_KEY_CONFLICT: 409,
    ErrorCode.VERSION_REQUIRED: 428,
    ErrorCode.VERSION_CONFLICT: 409,
    ErrorCode.ILLEGAL_TRANSITION: 409,
    ErrorCode.MISSING_TRANSITION_DATA: 422,
    ErrorCode.UNSAFE_CONTENT: 422,
    ErrorCode.CANDIDATE_REJECTED: 422,
    ErrorCode.NOT_IMPLEMENTED: 501,
}

#: The exact, frozen public shape for a missing OR forbidden-cross-provider
#: resource. Both paths MUST render this so existence cannot be inferred.
SAFE_NOT_FOUND_MESSAGE = "The requested resource was not found."


def new_request_id() -> str:
    """Generate a correlation/request ID. Opaque; contains no scope data."""
    return f"req_{uuid.uuid4().hex}"


# Patterns that must never appear in client-visible error details. This is a
# defensive leak scan, not a substitute for building safe details in the first
# place.
_LEAK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE)),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+")),
    ("password_field", re.compile(r"\b(password|passwd|pwd|secret|api[_-]?key|private[_-]?key)\b", re.IGNORECASE)),
    ("pin_otp", re.compile(r"\b(pin|otp)\b\s*[:=]", re.IGNORECASE)),
)

#: Detail keys that are explicitly allowed to appear in a client-visible error.
#: Anything else is dropped by `redact_details` to avoid accidental leakage.
_SAFE_DETAIL_KEYS: frozenset[str] = frozenset(
    {
        "field",
        "fields",
        "reason",
        "expected_version",
        "supported_versions",
        "allowed_transitions",
        "required",
        "locale",
        "supported_locales",
        "retry_after_seconds",
    }
)


def scan_for_leaks(text: str) -> list[str]:
    """Return the names of any leak patterns found in `text`. Empty == safe."""
    return [name for name, pattern in _LEAK_PATTERNS if pattern.search(text)]


def redact_details(details: dict[str, Any] | None) -> dict[str, Any]:
    """Drop any non-allowlisted key and any value that trips the leak scan.

    Used as a last line of defence when constructing a client error from data
    that may include unsafe fragments.
    """
    if not details:
        return {}
    safe: dict[str, Any] = {}
    for key, value in details.items():
        if key not in _SAFE_DETAIL_KEYS:
            continue
        if scan_for_leaks(str(value)):
            continue
        safe[key] = value
    return safe


@dataclass(frozen=True)
class ApiError(Exception):
    """A safe, client-renderable error. Carries the HTTP status separately so
    the route layer can map it, while `to_response()` produces the frozen body.
    """

    code: ErrorCode
    message: str
    request_id: str = field(default_factory=new_request_id)
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:  # noqa: D401
        # Enforce the leak-scan / allowlist at construction time.
        object.__setattr__(self, "details", redact_details(self.details))

    @property
    def http_status(self) -> int:
        return HTTP_STATUS.get(self.code, 400)

    def to_response(self) -> dict[str, Any]:
        return {
            "error": {
                "code": str(self.code),
                "message": self.message,
                "request_id": self.request_id,
                "details": self.details,
            }
        }


def not_found(request_id: str | None = None) -> ApiError:
    """The single safe response for BOTH a missing record and a forbidden
    cross-provider lookup. Callers must never branch to FORBIDDEN/403 for the
    cross-provider case — that would disclose existence."""
    return ApiError(
        code=ErrorCode.NOT_FOUND,
        message=SAFE_NOT_FOUND_MESSAGE,
        request_id=request_id or new_request_id(),
        details={},
    )


def validate_error_shape(body: dict[str, Any]) -> None:
    """Assert `body` matches the frozen error contract. Raises ValueError.

    Used by tests and can be used as a defensive guard around any error
    serialised by the Member 2 surface.
    """
    if set(body.keys()) != {"error"}:
        raise ValueError(f"error body must have exactly one top-level 'error' key, got {sorted(body.keys())}")
    err = body["error"]
    required = {"code", "message", "request_id", "details"}
    missing = required - set(err.keys())
    if missing:
        raise ValueError(f"error object missing required keys: {sorted(missing)}")
    extra = set(err.keys()) - required
    if extra:
        raise ValueError(f"error object has unexpected keys: {sorted(extra)}")
    if not isinstance(err["request_id"], str) or not err["request_id"]:
        raise ValueError("request_id must be a non-empty string")
    if not isinstance(err["details"], dict):
        raise ValueError("details must be an object")
    blob = f"{err['code']} {err['message']} {err['details']}"
    leaks = scan_for_leaks(blob)
    if leaks:
        raise ValueError(f"error body leaks confidential data: {leaks}")
