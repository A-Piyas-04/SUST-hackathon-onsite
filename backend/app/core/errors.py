"""Application error taxonomy and safe API error payloads."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_context import get_request_id


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotImplementedFeatureError(AppError):
    def __init__(self, message: str, *, phase: str = "3+") -> None:
        super().__init__(
            "not_implemented",
            message,
            status_code=501,
            details={"phase": phase},
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required.") -> None:
        super().__init__("unauthorized", message, status_code=401)


def error_payload(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": get_request_id(),
            "details": details or {},
        }
    }


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message, details=exc.details),
    )


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = {"fields": exc.errors()}
    return JSONResponse(
        status_code=422,
        content=error_payload("validation_error", "Request validation failed.", details=details),
    )


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload("http_error", str(exc.detail)),
    )


async def unhandled_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_payload(
            "internal_error",
            "An unexpected error occurred. Please try again later.",
        ),
    )
