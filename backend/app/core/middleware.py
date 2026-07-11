"""HTTP middleware for request correlation and structured access logs."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.request_context import request_id_var

logger = logging.getLogger("app.request")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get("X-Request-ID")
        request_id = incoming or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        logger.info(
            "request_started",
            extra={"request_id": request_id, "method": request.method, "path": request.url.path},
        )
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise
        else:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)
