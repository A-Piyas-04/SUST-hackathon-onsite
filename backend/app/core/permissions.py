"""UI and API permission strings derived from demo role assignments.

The backend remains authoritative: routes enforce scope and role-action rules
in ``authz.py``; this module exposes a stable permission vocabulary for
``GET /api/v1/me`` and frontend gating.
"""

from __future__ import annotations

from enum import StrEnum

from app.contracts.v1.enums import AppRole
from app.core.auth import UserContext


class CaseAction(StrEnum):
    OPEN = "open"
    ASSIGN = "assign"
    ACKNOWLEDGE = "acknowledge"
    ESCALATE = "escalate"
    RESOLVE = "resolve"
    NOTE = "note"
    REVIEW = "review"


_OPS_ROLES = frozenset(
    {AppRole.FIELD_OFFICER, AppRole.AREA_MANAGER, AppRole.PROVIDER_OPS}
)
_PARTICIPANT_ROLES = _OPS_ROLES | frozenset({AppRole.AGENT, AppRole.RISK_ANALYST})


def is_admin(user: UserContext) -> bool:
    return AppRole.ADMIN in user.roles


def is_management(user: UserContext) -> bool:
    return AppRole.MANAGEMENT in user.roles


def permissions_for_user(user: UserContext) -> tuple[str, ...]:
    roles = set(user.roles)
    perms: set[str] = {"tab:notifications"}

    if AppRole.ADMIN in roles:
        perms.update(
            {
                "tab:dashboard",
                "tab:liquidity",
                "tab:anomalies",
                "tab:scenarios",
                "tab:alerts",
                "tab:cases",
                "tab:validation",
                "outlet:switch",
                "simulation:manage",
                "ingestion:manage",
                "analytics:run",
                "alerts:publish",
                "case:open",
                "case:assign",
                "case:acknowledge",
                "case:escalate",
                "case:resolve",
                "case:note",
                "case:review",
            }
        )
        return tuple(sorted(perms))

    if AppRole.MANAGEMENT in roles:
        perms.update(
            {
                "tab:dashboard",
                "tab:liquidity",
                "tab:alerts",
                "tab:cases",
                "tab:validation",
                "outlet:switch",
            }
        )
        return tuple(sorted(perms))

    if AppRole.AGENT in roles:
        perms.update(
            {
                "tab:dashboard",
                "tab:liquidity",
                "tab:anomalies",
                "tab:alerts",
                "tab:cases",
                "case:note",
            }
        )
        return tuple(sorted(perms))

    if roles & _OPS_ROLES:
        perms.update(
            {
                "tab:dashboard",
                "tab:liquidity",
                "tab:anomalies",
                "tab:alerts",
                "tab:cases",
                "outlet:switch",
                "case:open",
                "case:assign",
                "case:acknowledge",
                "case:escalate",
                "case:resolve",
                "case:note",
            }
        )
        return tuple(sorted(perms))

    if AppRole.RISK_ANALYST in roles:
        perms.update(
            {
                "tab:dashboard",
                "tab:liquidity",
                "tab:anomalies",
                "tab:alerts",
                "tab:cases",
                "outlet:switch",
                "case:open",
                "case:note",
                "case:review",
            }
        )
        return tuple(sorted(perms))

    return tuple(sorted(perms))


def require_role_action(user: UserContext, action: CaseAction) -> None:
    """Raise ``ForbiddenError`` when the caller's role may not perform ``action``."""
    from app.core.authz import ForbiddenError

    roles = set(user.roles)
    if AppRole.ADMIN in roles:
        return

    if action is CaseAction.REVIEW:
        if AppRole.RISK_ANALYST not in roles:
            raise ForbiddenError("Only a risk analyst may record a case review.")
        return

    if action in {
        CaseAction.ASSIGN,
        CaseAction.ACKNOWLEDGE,
        CaseAction.ESCALATE,
        CaseAction.RESOLVE,
    }:
        if not roles & _OPS_ROLES:
            raise ForbiddenError("Your role cannot perform this case action.")
        return

    if action is CaseAction.OPEN:
        if not roles & (_OPS_ROLES | {AppRole.RISK_ANALYST}):
            raise ForbiddenError("Your role cannot open a case from an alert.")
        return

    if action is CaseAction.NOTE:
        if AppRole.MANAGEMENT in roles and not roles & _PARTICIPANT_ROLES:
            raise ForbiddenError("Your role cannot add case notes.")
        if not roles & _PARTICIPANT_ROLES:
            raise ForbiddenError("Your role cannot add case notes.")
        return

    raise ForbiddenError("Your role cannot perform this case action.")
