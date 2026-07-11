"""Auth/profile service interfaces (master Section 9.16).

Owner: Member 2. Narrow Protocols so routes depend on an interface, not a
concrete implementation. No production implementation exists in Phase 1 —
`ScaffoldAuthService` raises to prove the seam without faking success.
"""
from __future__ import annotations

from typing import Protocol

from app.coordination.auth.contracts import (
    DemoLoginRequest,
    DemoLoginResponse,
    MeResponse,
    PreferencesPatchRequest,
)
from app.coordination.shared.service import NotImplementedServiceError


class AuthService(Protocol):
    def demo_login(self, request: DemoLoginRequest) -> DemoLoginResponse: ...

    def current_user(self, user_id: str) -> MeResponse: ...

    def update_preferences(self, user_id: str, request: PreferencesPatchRequest) -> MeResponse: ...


class ScaffoldAuthService:
    """Phase-1 placeholder. Every method raises; no persistence, no JWT."""

    def demo_login(self, request: DemoLoginRequest) -> DemoLoginResponse:
        raise NotImplementedServiceError("demo_login is implemented in Phase 2")

    def current_user(self, user_id: str) -> MeResponse:
        raise NotImplementedServiceError("current_user is implemented in Phase 2")

    def update_preferences(self, user_id: str, request: PreferencesPatchRequest) -> MeResponse:
        raise NotImplementedServiceError("update_preferences is implemented in Phase 2")
