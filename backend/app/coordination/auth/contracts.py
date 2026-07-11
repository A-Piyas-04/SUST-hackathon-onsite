"""Auth/profile request & response contracts (schema.md 16.1; member-2 plan 9.7).

Owner: Member 2. Pydantic models back the OpenAPI surface Member 1 composes.
These are frozen contracts; runtime issuance/validation is Phase 2.

Security notes:
  * No password/PIN/OTP/token field is accepted or returned. `demo-login`
    selects a SEEDED synthetic identity by opaque selector only.
  * `/me` exposes explicit roles + provider/area/outlet scopes; a missing scope
    is never a wildcard.
  * `PATCH /me/preferences` accepts ONLY `preferred_locale`.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.coordination.shared.enums import AppRole, LocaleCode


class DemoLoginRequest(BaseModel):
    """Select a seeded demo identity. No credentials are transmitted."""

    model_config = ConfigDict(extra="forbid")
    demo_user_selector: str = Field(
        ..., min_length=1, max_length=100,
        description="Opaque selector for a seeded synthetic demo identity (e.g. 'agent_outlet_001').",
    )


class ScopeAssignment(BaseModel):
    role: AppRole
    provider_id: str | None = None
    area_id: str | None = None
    outlet_id: str | None = None


class SessionInfo(BaseModel):
    """Returned demo session/JWT metadata. The token itself is issued in Phase 2;
    the CONTRACT is frozen now. Never contains a password."""

    token_type: str = "bearer"
    access_token: str | None = Field(
        default=None, description="Demo JWT (issued in Phase 2; null in scaffolding)."
    )
    expires_at: str | None = Field(default=None, description="ISO-8601 UTC expiry.")


class DemoLoginResponse(BaseModel):
    user_id: str
    display_name: str
    is_active: bool
    preferred_locale: LocaleCode
    roles: list[AppRole]
    scopes: list[ScopeAssignment]
    session: SessionInfo


class MeResponse(BaseModel):
    """`GET /api/v1/me` — profile, roles, explicit scopes, locale."""

    user_id: str
    display_name: str
    is_active: bool
    preferred_locale: LocaleCode
    roles: list[AppRole]
    provider_scopes: list[str]
    area_scopes: list[str]
    outlet_scopes: list[str]
    restrictions: list[str] = Field(
        default_factory=list,
        description="Explicit restriction notes (e.g. 'management: aggregate read-only').",
    )


class PreferencesPatchRequest(BaseModel):
    """Only the preferred locale may be changed. Roles/scopes/activation are not
    client-mutable."""

    model_config = ConfigDict(extra="forbid")
    preferred_locale: LocaleCode
