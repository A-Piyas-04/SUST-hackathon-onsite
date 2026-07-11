"""Uniform error envelope (schema.md Section 16):
`{"error": {"code","message","request_id","details"}}`. Unauthorized
cross-provider lookups must return the same 404 shape as a genuinely missing
record — routers achieve that simply by raising a plain 404 either way.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or str(uuid.uuid4())


def _error_body(*, code: str, message: str, request_id: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "request_id": request_id, "details": details}}


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        code, message, details = detail.get("code", "http_error"), detail.get("message", ""), detail.get("details")
    else:
        code, message, details = "http_error", str(detail), None
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(code=code, message=message, request_id=get_request_id(request), details=details),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=_error_body(
            code="validation_error",
            message="Request validation failed",
            request_id=get_request_id(request),
            details={"errors": exc.errors()},
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    return JSONResponse(
        status_code=500,
        content=_error_body(code="internal_error", message="An unexpected error occurred", request_id=get_request_id(request)),
    )
