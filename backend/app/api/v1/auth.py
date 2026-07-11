"""Phase 5 authentication and principal-context routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.coordination import (
    DemoLoginRequest,
    DemoLoginResponse,
    PreferencesUpdate,
    PrincipalResponse,
    ScopeOut,
)
from app.core.auth import (
    UserContext,
    demo_token_for,
    require_authenticated,
    resolve_demo_user,
)
from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
from app.db.session import get_db_session
from app.db.transaction import transaction

router = APIRouter(prefix="/api/v1", tags=["auth"])


async def _principal(session: AsyncSession, user: UserContext) -> PrincipalResponse:
    locale = (
        await session.execute(
            text("SELECT preferred_locale FROM app_users WHERE user_id = :id"),
            {"id": user.user_id},
        )
    ).scalar()
    return PrincipalResponse(
        user_id=user.user_id,
        display_name=user.display_name,
        preferred_locale=locale or user.preferred_locale,
        roles=[r for r in user.roles],
        scopes=[
            ScopeOut(
                role=s.role,
                provider_id=s.provider_id,
                area_id=s.area_id,
                outlet_id=s.outlet_id,
            )
            for s in user.scopes
        ],
    )


@router.post("/auth/demo-login", response_model=DemoLoginResponse)
async def demo_login(
    request: DemoLoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    if not settings.demo_auth_enabled:
        raise UnauthorizedError("Demo authentication is disabled.")
    user = resolve_demo_user(
        user_key=request.user_key,
        role=request.role.value if request.role else None,
        provider=request.provider,
    )
    principal = await _principal(session, user)
    return DemoLoginResponse(token=demo_token_for(user.user_id), user=principal)


@router.get("/me", response_model=PrincipalResponse)
async def get_me(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    return await _principal(session, user)


@router.patch("/me/preferences", response_model=PrincipalResponse)
async def update_preferences(
    request: PreferencesUpdate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserContext, Depends(require_authenticated)],
):
    async with transaction(session):
        await session.execute(
            text(
                "UPDATE app_users SET preferred_locale = :locale WHERE user_id = :id"
            ),
            {"locale": request.preferred_locale.value, "id": user.user_id},
        )
    return await _principal(session, user)
