"""Role / scope authorization policy (member-2 plan Section 7.1; schema.md 6.6, 15).

Owner: Member 2. Pure-stdlib, versioned, fully testable now. Runtime middleware
that attaches an authorized scope to a request is Phase 2; this module is the
*decision core* it will call, so the provider-boundary rules are frozen and
proven before any endpoint exists.

Hard invariants encoded here:
  * A missing provider scope is NEVER a wildcard. Empty reach == access to
    nothing, not everything.
  * `management` is read-only by default and does NOT receive raw
    cross-provider evidence unless a provider is explicitly in its scope.
  * `admin` is demo/setup only and is NOT an operational shortcut: it is not
    granted operational provider-confidential access by this policy.
  * Cross-provider denial is expressed as a boolean decision; the *service*
    turns a denied confidential-resource read into the same safe 404 as a
    missing record so existence is never disclosed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.coordination.shared.enums import AppRole
from app.coordination.shared.references import CallerScope

ROLE_SCOPE_MATRIX_VERSION = "v1"


class ScopeDimension(StrEnum):
    PROVIDER = "provider"
    AREA = "area"
    OUTLET = "outlet"


@dataclass(frozen=True)
class RoleScopePolicy:
    role: AppRole
    #: Scope dimensions a user of this role MUST have to be operational.
    required_scopes: frozenset[ScopeDimension]
    #: Read-only roles cannot perform workflow transitions.
    read_only: bool
    #: Whether the role may see another provider's confidential (raw) evidence
    #: *by virtue of the role*. Only ever true when the provider is explicitly
    #: within the caller's scope — never a blanket cross-provider grant.
    can_view_raw_cross_provider: bool
    description: str


#: The frozen role/scope matrix. Versioned so Member 1/3 can pin against it.
ROLE_SCOPE_MATRIX: dict[str, RoleScopePolicy] = {
    AppRole.AGENT: RoleScopePolicy(
        role=AppRole.AGENT,
        required_scopes=frozenset({ScopeDimension.OUTLET}),
        read_only=False,  # may act only when assigned/allowed on own-outlet case
        can_view_raw_cross_provider=False,
        description="Own-outlet combined alert/case view; actions only when assigned/allowed.",
    ),
    AppRole.FIELD_OFFICER: RoleScopePolicy(
        role=AppRole.FIELD_OFFICER,
        required_scopes=frozenset({ScopeDimension.PROVIDER, ScopeDimension.AREA}),
        read_only=False,
        can_view_raw_cross_provider=False,
        description="Assigned provider/area cases.",
    ),
    AppRole.AREA_MANAGER: RoleScopePolicy(
        role=AppRole.AREA_MANAGER,
        required_scopes=frozenset({ScopeDimension.PROVIDER, ScopeDimension.AREA}),
        read_only=False,
        can_view_raw_cross_provider=False,
        description="Provider/area queue and authorized escalation.",
    ),
    AppRole.PROVIDER_OPS: RoleScopePolicy(
        role=AppRole.PROVIDER_OPS,
        required_scopes=frozenset({ScopeDimension.PROVIDER}),
        read_only=False,
        can_view_raw_cross_provider=False,
        description="Own-provider alerts/cases only.",
    ),
    AppRole.RISK_ANALYST: RoleScopePolicy(
        role=AppRole.RISK_ANALYST,
        required_scopes=frozenset({ScopeDimension.PROVIDER}),
        read_only=False,
        can_view_raw_cross_provider=False,
        description="Escalated own-provider cases/reviews.",
    ),
    AppRole.MANAGEMENT: RoleScopePolicy(
        role=AppRole.MANAGEMENT,
        required_scopes=frozenset(),  # aggregate/read scope granted explicitly
        read_only=True,
        can_view_raw_cross_provider=False,
        description="Read-only aggregate; no raw cross-provider evidence unless explicitly scoped.",
    ),
    AppRole.ADMIN: RoleScopePolicy(
        role=AppRole.ADMIN,
        required_scopes=frozenset(),
        read_only=True,
        can_view_raw_cross_provider=False,
        description="Demo/setup only; never an operational shortcut.",
    ),
}


@dataclass(frozen=True)
class ResourceScope:
    """The provider/outlet/area scope of a confidential workflow resource
    (alert, case, note, notification, audit event, evidence reference)."""

    provider_id: str | None
    outlet_id: str | None = None
    area_id: str | None = None

    @property
    def is_shared_cash(self) -> bool:
        return self.provider_id is None


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    #: Machine-readable reason for tests/audit. Never surfaced raw to clients.
    reason: str
    matched_role: str | None = None


def required_scopes(role: AppRole | str) -> frozenset[ScopeDimension]:
    policy = ROLE_SCOPE_MATRIX.get(str(role))  # StrEnum compares equal to value
    if policy is None:
        return frozenset()
    return policy.required_scopes


def has_minimum_scope(caller: CallerScope, role: AppRole | str) -> bool:
    """True iff the caller satisfies the minimum scope dimensions for `role`."""
    needed = required_scopes(role)
    if ScopeDimension.PROVIDER in needed and not caller.provider_ids:
        return False
    if ScopeDimension.AREA in needed and not caller.area_ids:
        return False
    if ScopeDimension.OUTLET in needed and not caller.outlet_ids:
        return False
    return True


def _role_allows_read(role: str, caller: CallerScope, resource: ResourceScope) -> AccessDecision | None:
    """Per-role read decision. Returns an ALLOW decision or None (this role does
    not grant it); denials are aggregated by the caller of this helper."""
    if role == AppRole.AGENT:
        if resource.outlet_id and resource.outlet_id in caller.outlet_ids:
            return AccessDecision(True, "agent_own_outlet", role)
        return None
    if role in (AppRole.PROVIDER_OPS, AppRole.RISK_ANALYST):
        if resource.is_shared_cash:
            # Shared-cash confidential rows need outlet/area reach, never a
            # provider wildcard.
            if resource.outlet_id and resource.outlet_id in caller.outlet_ids:
                return AccessDecision(True, "provider_role_shared_cash_outlet", role)
            if resource.area_id and resource.area_id in caller.area_ids:
                return AccessDecision(True, "provider_role_shared_cash_area", role)
            return None
        if resource.provider_id and resource.provider_id in caller.provider_ids:
            return AccessDecision(True, "provider_role_own_provider", role)
        return None
    if role in (AppRole.FIELD_OFFICER, AppRole.AREA_MANAGER):
        provider_ok = bool(resource.provider_id and resource.provider_id in caller.provider_ids)
        area_ok = bool(resource.area_id and resource.area_id in caller.area_ids)
        if resource.is_shared_cash:
            if area_ok:
                return AccessDecision(True, "area_role_shared_cash_area", role)
            return None
        if provider_ok and area_ok:
            return AccessDecision(True, "area_role_provider_area", role)
        return None
    if role == AppRole.MANAGEMENT:
        # Read-only aggregate. Raw provider-confidential access ONLY if the
        # provider is explicitly in scope — never a blanket cross-provider grant.
        if resource.provider_id and resource.provider_id in caller.provider_ids:
            return AccessDecision(True, "management_explicit_provider_scope", role)
        return None
    if role == AppRole.ADMIN:
        # Demo/setup only; not an operational shortcut. No confidential grant.
        return None
    return None


def evaluate_read(caller: CallerScope, resource: ResourceScope) -> AccessDecision:
    """Decide whether `caller` may read a confidential resource with `resource`
    scope. Union across the caller's roles; deny by default.

    NOTE: a False decision on a cross-provider resource must be mapped by the
    service to the SAME safe 404 as a missing record.
    """
    if not caller.is_active:
        return AccessDecision(False, "inactive_user")
    if not caller.roles:
        return AccessDecision(False, "no_roles")
    for role in caller.roles:
        decision = _role_allows_read(role, caller, resource)
        if decision is not None and decision.allowed:
            return decision
    return AccessDecision(False, "out_of_scope")


def can_perform_transition(caller: CallerScope, resource: ResourceScope) -> AccessDecision:
    """Whether the caller may drive a case transition on `resource`.

    Requires read access AND at least one non-read-only role. Fine-grained
    owner/assignee checks are layered on top by the case service in Phase 4.
    """
    read = evaluate_read(caller, resource)
    if not read.allowed:
        return read
    for role in caller.roles:
        policy = ROLE_SCOPE_MATRIX.get(role)
        if policy and not policy.read_only:
            return AccessDecision(True, "actor_role_may_transition", role)
    return AccessDecision(False, "read_only_role")
