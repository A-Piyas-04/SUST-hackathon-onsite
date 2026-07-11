"""FastAPI glue shared by Member 2 route scaffolds.

Owner: Member 2. This is the ONLY shared module that imports FastAPI. It turns
an `ApiError` into the frozen safe error body and provides the honest
`not_implemented` response used by every Phase-1 route scaffold.
"""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.coordination.shared.errors import ApiError, new_request_id
from app.coordination.shared.service import feature_not_ready


def request_id_from(request: Request | None) -> str:
    """Reuse an inbound X-Request-Id if present; otherwise mint one."""
    if request is not None:
        header = request.headers.get("X-Request-Id")
        if header:
            return header
    return new_request_id()


def error_response(err: ApiError) -> JSONResponse:
    return JSONResponse(status_code=err.http_status, content=err.to_response())


def not_implemented(feature: str, request: Request | None = None) -> JSONResponse:
    """Honest 501 with the standard error shape — never a fake 200."""
    return error_response(feature_not_ready(feature, request_id=request_id_from(request)))
