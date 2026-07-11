"""Service-layer scaffolding helpers (master Section 9.15-9.16).

Owner: Member 2. Runtime behaviour for Member 2's workflow is intentionally NOT
implemented in Phase 1. Rather than return a misleading `200 OK`, every
unimplemented action raises `ApiError(NOT_IMPLEMENTED)` (HTTP 501) with the
standard safe error body. Service *interfaces* are defined per module as
Protocols so they can be mocked in tests and implemented in later phases.

This module is pure-stdlib; only the `*/routes.py` layer imports FastAPI.
"""
from __future__ import annotations

from app.coordination.shared.errors import ApiError, ErrorCode, new_request_id


def feature_not_ready(feature: str, *, request_id: str | None = None) -> ApiError:
    """Return (do not raise) a NOT_IMPLEMENTED ApiError for an unbuilt feature."""
    return ApiError(
        code=ErrorCode.NOT_IMPLEMENTED,
        message=f"{feature} is not implemented in this phase (P1-M2 scaffolding).",
        request_id=request_id or new_request_id(),
        details={},
    )


class NotImplementedServiceError(NotImplementedError):
    """Raised by scaffolded service methods that have no Phase-1 implementation."""
