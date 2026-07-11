"""Centralized authorization policy for Phase 5 provider boundaries.

The application connects with a privileged database role, so this module is the
authoritative application-layer gate; PostgreSQL RLS (migration 006) reinforces
the same rules on Supabase. The scope logic mirrors ``app.has_provider_scope`` /
``app.has_outlet_scope`` exactly (docs/schema.md §13.16, §15):

  * a provider scope grants provider-confidential access only for that provider
    (area-limited when the scope names an area); a NULL provider scope is NEVER a
    wildcard;
  * an outlet (agent) scope grants combined access at that outlet;
  * shared-cash/outlet access also follows an area scope or a provider scope that
    actually holds an account at that outlet.

Confidential lookups return the SAME safe not-found result whether the id is
missing or merely forbidden, so existence is never leaked (guardrail 7).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import AppRole
from app.core.auth import UserContext
from app.core.errors import AppError


class ForbiddenError(AppError):
    """Explicit 403 for authenticated callers lacking action permission."""

    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__("forbidden", message, status_code=403)


class SafeNotFoundError(AppError):
    """Uniform 404 for missing OR forbidden confidential resources."""

    def __init__(self, resource: str = "Resource") -> None:
        super().__init__("not_found", f"{resource} not found.", status_code=404)


class ConcurrencyConflictError(AppError):
    def __init__(self, message: str = "The record was modified by another request.") -> None:
        super().__init__("version_conflict", message, status_code=409)


class IllegalTransitionError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("illegal_transition", message, status_code=409)


# --------------------------------------------------------------------------- #
# Scope resolution helpers (single small query each; SECURITY DEFINER analogue)
# --------------------------------------------------------------------------- #
async def _outlet_area(session: AsyncSession, outlet_id: UUID) -> UUID | None:
    result = await session.execute(
        text("SELECT area_id FROM outlets WHERE outlet_id = :id"),
        {"id": outlet_id},
    )
    row = result.first()
    return row[0] if row else None


async def _outlet_has_provider_account(
    session: AsyncSession, outlet_id: UUID, provider_id: UUID
) -> bool:
    result = await session.execute(
        text(
            """
            SELECT 1 FROM outlet_provider_accounts
            WHERE outlet_id = :outlet AND provider_id = :provider AND is_active
            LIMIT 1
            """
        ),
        {"outlet": outlet_id, "provider": provider_id},
    )
    return result.first() is not None


def _is_admin(user: UserContext) -> bool:
    return AppRole.ADMIN in user.roles


def _is_management(user: UserContext) -> bool:
    return AppRole.MANAGEMENT in user.roles


def require_admin(user: UserContext) -> None:
    if not _is_admin(user):
        raise ForbiddenError("Demo setup actions require an admin identity.")


def require_admin_or_management(user: UserContext) -> None:
    """Evidence/observability reads are limited to admin and management roles."""
    if not (_is_admin(user) or _is_management(user)):
        raise ForbiddenError("Validation and metrics evidence require an admin or management role.")


async def require_outlet_access(
    session: AsyncSession, user: UserContext, *, outlet_id: UUID
) -> None:
    if not await has_outlet_scope(session, user, outlet_id=outlet_id):
        raise SafeNotFoundError("Outlet")


async def require_provider_access(
    session: AsyncSession,
    user: UserContext,
    *,
    provider_id: UUID,
    outlet_id: UUID,
) -> None:
    if not await can_access_scope(
        session, user, outlet_id=outlet_id, provider_id=provider_id
    ):
        raise SafeNotFoundError("Resource")


async def has_provider_scope(
    session: AsyncSession,
    user: UserContext,
    *,
    provider_id: UUID,
    outlet_id: UUID,
) -> bool:
    """Mirror of ``app.has_provider_scope(provider, outlet)``."""
    if _is_admin(user):
        return True
    outlet_area = await _outlet_area(session, outlet_id)
    for s in user.scopes:
        if (
            s.provider_id is not None
            and s.provider_id == provider_id
            and (s.area_id is None or s.area_id == outlet_area)
        ):
            return True
        if s.outlet_id is not None and s.outlet_id == outlet_id:
            return True
    return False


async def has_outlet_scope(
    session: AsyncSession, user: UserContext, *, outlet_id: UUID
) -> bool:
    """Mirror of ``app.has_outlet_scope(outlet)`` (shared-cash / outlet access)."""
    if _is_admin(user) or _is_management(user):
        return True
    outlet_area = await _outlet_area(session, outlet_id)
    for s in user.scopes:
        if s.outlet_id is not None and s.outlet_id == outlet_id:
            return True
        if s.area_id is not None and outlet_area is not None and s.area_id == outlet_area:
            return True
        if s.provider_id is not None and await _outlet_has_provider_account(
            session, outlet_id, s.provider_id
        ):
            return True
    return False


async def can_access_scope(
    session: AsyncSession,
    user: UserContext,
    *,
    outlet_id: UUID,
    provider_id: UUID | None,
) -> bool:
    """Provider-confidential when provider_id is set; shared-cash otherwise."""
    if provider_id is None:
        return await has_outlet_scope(session, user, outlet_id=outlet_id)
    if _is_management(user):
        return False
    return await has_provider_scope(
        session, user, provider_id=provider_id, outlet_id=outlet_id
    )


async def authorized_outlet_ids(
    session: AsyncSession, user: UserContext
) -> list[UUID] | None:
    """Return authorized outlet ids, or ``None`` when the caller may list all outlets."""
    if _is_admin(user) or _is_management(user):
        return None

    authorized: set[UUID] = set()
    for scope in user.scopes:
        if scope.outlet_id is not None:
            authorized.add(scope.outlet_id)
        if scope.area_id is not None:
            result = await session.execute(
                text("SELECT outlet_id FROM outlets WHERE area_id = :area_id"),
                {"area_id": scope.area_id},
            )
            authorized.update(row[0] for row in result.all())
        if scope.provider_id is not None:
            result = await session.execute(
                text(
                    """
                    SELECT outlet_id FROM outlet_provider_accounts
                    WHERE provider_id = :provider_id AND is_active
                    """
                ),
                {"provider_id": scope.provider_id},
            )
            authorized.update(row[0] for row in result.all())

    return sorted(authorized)


async def authorized_provider_ids(
    session: AsyncSession, user: UserContext, *, outlet_id: UUID | None = None
) -> list[UUID] | None:
    """Return authorized provider ids, or ``None`` when all providers are visible."""
    if _is_admin(user):
        return None
    if _is_management(user):
        return None

    authorized: set[UUID] = set()
    for scope in user.scopes:
        if scope.outlet_id is not None:
            if outlet_id is not None and scope.outlet_id != outlet_id:
                continue
            result = await session.execute(
                text(
                    """
                    SELECT provider_id FROM outlet_provider_accounts
                    WHERE outlet_id = :outlet_id AND is_active
                    """
                ),
                {"outlet_id": scope.outlet_id if outlet_id is None else outlet_id},
            )
            authorized.update(row[0] for row in result.all())
        elif scope.provider_id is not None:
            if outlet_id is not None and not await _outlet_has_provider_account(
                session, outlet_id, scope.provider_id
            ):
                continue
            authorized.add(scope.provider_id)

    return sorted(authorized)


async def provider_can_read_transactions(
    session: AsyncSession, user: UserContext, *, outlet_id: UUID
) -> bool:
    """Management receives aggregate dashboard access but not raw provider transactions."""
    if _is_management(user):
        return False
    if _is_admin(user):
        return True
    if AppRole.AGENT in user.roles:
        return await has_outlet_scope(session, user, outlet_id=outlet_id)
    provider_ids = await authorized_provider_ids(session, user, outlet_id=outlet_id)
    return bool(provider_ids)
