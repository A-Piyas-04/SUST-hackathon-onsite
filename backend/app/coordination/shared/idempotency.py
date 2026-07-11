"""Idempotency-Key request policy (member-2 plan Section 6.3; master Section 9.8).

Owner: Member 2. Pure-stdlib policy + validator. Durable idempotency STORAGE
(returning the original logical result for a repeated key) is a later phase;
Phase 1 freezes the *contract*: key syntax, which endpoints require it, the
request fingerprint, and the safe error codes for the two conflict cases.

Frozen decisions:
  * Header name: `Idempotency-Key`.
  * Syntax: 8..200 chars, printable ASCII excluding control chars and spaces.
    A UUID is the recommended form but any opaque token in range is accepted.
  * Scope of a key: (endpoint method+path template, authenticated user). The
    same key replayed by a different user is a *different* logical key.
  * Fingerprint: a stable hash of the canonicalised request body. Same key +
    same fingerprint  -> return the original result (no new side effects).
    Same key + different fingerprint -> 409 IDEMPOTENCY_KEY_CONFLICT.
  * Concurrent duplicates: the second in-flight request with the same key must
    not create a second case/transition/note/assignment/notification/audit
    event; it waits for or reuses the first result. (Enforced in later phases
    via a unique key store; contract asserted here.)
  * Retention: keys are retained for the demo session window (>= 24h assumed);
    beyond retention a replay may be treated as a fresh request.

Every mutating POST in the Member 2 surface requires the header. GET/PATCH-me
do not. `IDEMPOTENT_ENDPOINTS` is the frozen list consumed by tests and, later,
middleware.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.coordination.shared.errors import ApiError, ErrorCode, new_request_id

IDEMPOTENCY_HEADER = "Idempotency-Key"

MIN_KEY_LENGTH = 8
MAX_KEY_LENGTH = 200
_KEY_PATTERN = re.compile(r"^[\x21-\x7e]{%d,%d}$" % (MIN_KEY_LENGTH, MAX_KEY_LENGTH))

#: Frozen list of Member 2 endpoints that MUST accept/require an Idempotency-Key.
#: (method, path-template). Path params use the same snake_case names as the
#: registered FastAPI routes so tests and middleware agree exactly.
IDEMPOTENT_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("POST", "/api/v1/alerts/{alert_id}/cases"),
    ("POST", "/api/v1/cases/{case_id}/assignments"),
    ("POST", "/api/v1/cases/{case_id}/acknowledge"),
    ("POST", "/api/v1/cases/{case_id}/escalate"),
    ("POST", "/api/v1/cases/{case_id}/resolve"),
    ("POST", "/api/v1/cases/{case_id}/notes"),
    ("POST", "/api/v1/cases/{case_id}/review"),
    ("POST", "/api/v1/notifications/{notification_id}/read"),
)

#: Mutating POSTs that are intentionally NOT idempotency-gated in Phase 1.
#: demo-login mints a fresh session by design and is safe to repeat.
NON_IDEMPOTENT_POSTS: tuple[tuple[str, str], ...] = (
    ("POST", "/api/v1/auth/demo-login"),
)


def requires_idempotency_key(method: str, path_template: str) -> bool:
    return (method.upper(), path_template) in IDEMPOTENT_ENDPOINTS


def is_valid_key(key: str | None) -> bool:
    return bool(key) and bool(_KEY_PATTERN.match(key))  # type: ignore[arg-type]


def fingerprint(body: Any) -> str:
    """Stable fingerprint of a request body for same-key/same-request checks.

    Canonicalises via sorted-key JSON so field ordering does not matter.
    """
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_idempotency_header(
    method: str,
    path_template: str,
    key: str | None,
    *,
    request_id: str | None = None,
) -> None:
    """Validate the header for a request. Raises ApiError on violation.

    Returns None when the request is acceptable (either the endpoint does not
    require a key, or a syntactically valid key was supplied).
    """
    request_id = request_id or new_request_id()
    if not requires_idempotency_key(method, path_template):
        return
    if key is None:
        raise ApiError(
            code=ErrorCode.IDEMPOTENCY_KEY_REQUIRED,
            message=f"{IDEMPOTENCY_HEADER} header is required for this operation.",
            request_id=request_id,
            details={"required": IDEMPOTENCY_HEADER},
        )
    if not is_valid_key(key):
        raise ApiError(
            code=ErrorCode.IDEMPOTENCY_KEY_INVALID,
            message=(
                f"{IDEMPOTENCY_HEADER} must be {MIN_KEY_LENGTH}-{MAX_KEY_LENGTH} "
                "printable, non-space characters."
            ),
            request_id=request_id,
            details={"field": IDEMPOTENCY_HEADER},
        )
