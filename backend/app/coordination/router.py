"""Member 2 route composition entry point (master Checkpoint 5; member-2 plan
Phase 1 exit: "Member 1 can merge your route contract without editing your
module").

Owner: Member 2. Member 1 composes Member 2's surface with ONE of:

    from app.coordination.router import get_member2_routers, include_member2_routers

    include_member2_routers(app)                       # registers all routers
    # or, if finer control is wanted:
    for r in get_member2_routers():
        app.include_router(r)

All routers already carry the `/api/v1` prefix. No Member 2 internals need
editing to compose them. None of these modules import Member 1 repositories or
Member 3 formula implementations.
"""
from __future__ import annotations

from fastapi import APIRouter, FastAPI

from app.coordination.alerts.routes import alerts_router
from app.coordination.auth.routes import auth_router, profile_router
from app.coordination.cases.routes import cases_router
from app.coordination.notifications.routes import notifications_router


def get_member2_routers() -> list[APIRouter]:
    """Ordered list of all Member 2 routers. Audit reads are registered inside
    `cases_router` (GET /api/v1/cases/{caseId}/audit-events)."""
    return [
        auth_router,
        profile_router,
        alerts_router,
        cases_router,
        notifications_router,
    ]


def include_member2_routers(app: FastAPI) -> None:
    for router in get_member2_routers():
        app.include_router(router)
