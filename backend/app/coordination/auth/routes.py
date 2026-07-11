"""Auth/profile route scaffolds (schema.md 16.1).

Owner: Member 2. Routers register cleanly and preserve `/api/v1`. Runtime
behaviour is Phase 2; every handler returns an honest 501 with the standard
safe error body (never a fake 200). Member 1 composes these via
`app.coordination.router.get_member2_routers()` without editing this module.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.coordination.auth.contracts import (
    DemoLoginRequest,
    PreferencesPatchRequest,
)
from app.coordination.shared.http import not_implemented

auth_router = APIRouter(prefix="/api/v1/auth", tags=["coordination:auth"])
profile_router = APIRouter(prefix="/api/v1", tags=["coordination:profile"])


@auth_router.post("/demo-login")
async def demo_login(request: Request, body: DemoLoginRequest):
    return not_implemented("Demo login", request)


@profile_router.get("/me")
async def get_me(request: Request):
    return not_implemented("Current-user profile", request)


@profile_router.patch("/me/preferences")
async def patch_preferences(request: Request, body: PreferencesPatchRequest):
    return not_implemented("Preferences update", request)
