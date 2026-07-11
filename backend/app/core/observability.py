"""In-process request/error counters for the /metrics observability endpoint.

Deliberately lightweight (no external Prometheus dependency): a thread-safe
counter registry incremented by ``RequestIdMiddleware``. Values are per-process
and reset on restart — surfaced only as live operational context, never mixed
with the persisted, release-tagged validation metrics.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

_lock = threading.Lock()
_request_count = 0
_error_count = 0


def record_request(status_code: int) -> None:
    global _request_count, _error_count
    with _lock:
        _request_count += 1
        if status_code >= 500:
            _error_count += 1


def record_error() -> None:
    """Count an unhandled exception (response never produced)."""
    global _request_count, _error_count
    with _lock:
        _request_count += 1
        _error_count += 1


@dataclass(frozen=True)
class ProcessCounters:
    request_count: int
    error_count: int


def snapshot() -> ProcessCounters:
    with _lock:
        return ProcessCounters(request_count=_request_count, error_count=_error_count)


def reset() -> None:
    """Test-only helper to reset counters between cases."""
    global _request_count, _error_count
    with _lock:
        _request_count = 0
        _error_count = 0
