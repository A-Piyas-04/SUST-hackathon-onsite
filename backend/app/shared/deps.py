"""Shared FastAPI dependencies.

Owner: Member 1 for this stub only. `get_current_user_stub` is an explicit
passthrough with NO real authentication/authorization/RBAC logic — Member 2
owns the real implementation (JWT verification, role/provider/area scope
resolution) and will replace this dependency in place once ready, without
routers needing to change their signature.
"""
from __future__ import annotations

from typing import TypedDict


class CurrentUserStub(TypedDict):
    user_id: str
    role: str


def get_current_user_stub() -> CurrentUserStub:
    """# TODO(owner=Member2): replace with real JWT auth + RBAC scope
    resolution. Returns a fixed admin-like stub so every Member 1 route is
    callable during Phase 1 without a real token."""
    return {"user_id": "00000000-0000-0000-0000-000000000000", "role": "admin_service_stub"}
