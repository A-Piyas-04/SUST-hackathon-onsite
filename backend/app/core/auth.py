"""Authentication dependency interface — mock/demo provider for Phase 2."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.contracts.v1.enums import AppRole
from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError

_bearer = HTTPBearer(auto_error=False)

# Seeded demo identities (see backend/seeds/reference_seed.sql)
BKASH = UUID("11111111-1111-1111-1111-111111111111")
NAGAD = UUID("22222222-2222-2222-2222-222222222222")
ROCKET = UUID("33333333-3333-3333-3333-333333333333")
OUTLET1 = UUID("0b000000-0000-0000-0000-000000000001")
OUTLET2 = UUID("0b000000-0000-0000-0000-000000000002")
AREA_MARKET = UUID("a0000000-0000-0000-0000-000000000003")

AGENT1 = UUID("d0000000-0000-0000-0000-000000000a01")
AGENT2 = UUID("d0000000-0000-0000-0000-000000000a02")
BKASH_OPS = UUID("d0000000-0000-0000-0000-000000000b01")
NAGAD_OPS = UUID("d0000000-0000-0000-0000-000000000b02")
ROCKET_OPS = UUID("d0000000-0000-0000-0000-000000000b03")
AREA_MGR = UUID("d0000000-0000-0000-0000-000000000c01")
RISK_BK = UUID("d0000000-0000-0000-0000-000000000d01")
MGMT = UUID("d0000000-0000-0000-0000-000000000e01")
ADMIN = UUID("d0000000-0000-0000-0000-000000000f01")


@dataclass(frozen=True)
class AccessScope:
    role: AppRole
    provider_id: UUID | None = None
    area_id: UUID | None = None
    outlet_id: UUID | None = None


@dataclass(frozen=True)
class UserContext:
    user_id: UUID
    display_name: str
    preferred_locale: str
    scopes: tuple[AccessScope, ...]

    @property
    def roles(self) -> tuple[AppRole, ...]:
        return tuple({s.role for s in self.scopes})


_DEMO_USERS: dict[UUID, UserContext] = {
    AGENT1: UserContext(
        user_id=AGENT1,
        display_name="Demo Agent (Outlet 001)",
        preferred_locale="en",
        scopes=(AccessScope(role=AppRole.AGENT, outlet_id=OUTLET1),),
    ),
    AGENT2: UserContext(
        user_id=AGENT2,
        display_name="Demo Agent (Outlet 002)",
        preferred_locale="en",
        scopes=(AccessScope(role=AppRole.AGENT, outlet_id=OUTLET2),),
    ),
    BKASH_OPS: UserContext(
        user_id=BKASH_OPS,
        display_name="Demo bKash Ops",
        preferred_locale="en",
        scopes=(AccessScope(role=AppRole.PROVIDER_OPS, provider_id=BKASH),),
    ),
    NAGAD_OPS: UserContext(
        user_id=NAGAD_OPS,
        display_name="Demo Nagad Ops",
        preferred_locale="en",
        scopes=(AccessScope(role=AppRole.PROVIDER_OPS, provider_id=NAGAD),),
    ),
    ROCKET_OPS: UserContext(
        user_id=ROCKET_OPS,
        display_name="Demo Rocket Ops",
        preferred_locale="en",
        scopes=(AccessScope(role=AppRole.PROVIDER_OPS, provider_id=ROCKET),),
    ),
    AREA_MGR: UserContext(
        user_id=AREA_MGR,
        display_name="Demo Area Manager (bKash/Market)",
        preferred_locale="bn",
        scopes=(
            AccessScope(role=AppRole.AREA_MANAGER, provider_id=BKASH, area_id=AREA_MARKET),
        ),
    ),
    RISK_BK: UserContext(
        user_id=RISK_BK,
        display_name="Demo Risk Analyst (bKash)",
        preferred_locale="en",
        scopes=(AccessScope(role=AppRole.RISK_ANALYST, provider_id=BKASH),),
    ),
    MGMT: UserContext(
        user_id=MGMT,
        display_name="Demo Management",
        preferred_locale="en",
        scopes=(AccessScope(role=AppRole.MANAGEMENT),),
    ),
    ADMIN: UserContext(
        user_id=ADMIN,
        display_name="Demo Admin",
        preferred_locale="en",
        scopes=(AccessScope(role=AppRole.ADMIN),),
    ),
}


class AuthProvider(ABC):
    @abstractmethod
    async def resolve(self, token: str) -> UserContext:
        raise NotImplementedError


class MockAuthProvider(AuthProvider):
    """Demo tokens: ``Bearer demo:<user_uuid>``."""

    async def resolve(self, token: str) -> UserContext:
        if not token.startswith("demo:"):
            raise UnauthorizedError("Invalid demo token format. Use Bearer demo:<user_uuid>.")
        try:
            user_id = UUID(token.removeprefix("demo:"))
        except ValueError as exc:
            raise UnauthorizedError("Invalid demo user id.") from exc
        user = _DEMO_USERS.get(user_id)
        if user is None:
            raise UnauthorizedError("Unknown demo user.")
        return user


def get_auth_provider(settings: Settings | None = None) -> AuthProvider:
    settings = settings or get_settings()
    if not settings.demo_auth_enabled:
        raise UnauthorizedError("Demo authentication is disabled.")
    return MockAuthProvider()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError()
    provider = get_auth_provider(settings)
    return await provider.resolve(credentials.credentials)


require_authenticated = get_current_user
