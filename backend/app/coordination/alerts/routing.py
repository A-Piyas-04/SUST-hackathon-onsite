"""Routing variables + initial routing decision table (member-2 plan Sections
6.5/9.14; schema.md 10.5) and active-alert deduplication rules (schema.md 10.1,
master Section 10.3).

Owner: Member 2. Pure-stdlib. The full routing *engine* (persistence, live rule
rows, case creation) is Phase 3; Phase 1 freezes the input variables, the
resolution order, and a default decision table.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.coordination.shared.enums import AlertType, AppRole, Severity

# Routing input variables Member 2 needs to resolve a recipient/owner + next step.
ROUTING_VARIABLES: tuple[str, ...] = (
    "alert_type",
    "provider_id",
    "area_id",
    "outlet_id",
    "severity",
    "requires_case",
    "suggested_recipient_role",
    "suggested_owner_role",
    "recommended_next_step_code",
    "escalation_eligible",
    "data_quality_advisory",
)

#: Severity ordering for `minimum_severity` comparisons.
_SEVERITY_ORDER: dict[str, int] = {
    Severity.INFO.value: 0,
    Severity.LOW.value: 1,
    Severity.MEDIUM.value: 2,
    Severity.HIGH.value: 3,
    Severity.CRITICAL.value: 4,
}


def severity_rank(severity: str) -> int:
    return _SEVERITY_ORDER.get(severity, -1)


@dataclass(frozen=True)
class RoutingRule:
    name: str
    provider_id: str | None  # None == fallback / shared cash
    area_id: str | None
    alert_type: str | None  # None == wildcard
    minimum_severity: str
    target_role: AppRole
    priority: int  # lower wins


@dataclass(frozen=True)
class RoutingInput:
    alert_type: str
    provider_id: str | None
    area_id: str | None
    severity: str
    requires_case: bool


@dataclass(frozen=True)
class RoutingDecision:
    matched: bool
    target_role: AppRole | None = None
    rule_name: str | None = None
    specificity: str | None = None  # provider_area | provider | area | fallback


# Default Phase-1 decision table. Rows are specificity-agnostic; resolution
# order (below) picks the most specific matching rule, then lowest priority.
DEFAULT_ROUTING_TABLE: tuple[RoutingRule, ...] = (
    RoutingRule("provider_area_high", provider_id="*", area_id="*", alert_type=None,
                minimum_severity=Severity.HIGH.value, target_role=AppRole.AREA_MANAGER, priority=10),
    RoutingRule("provider_high", provider_id="*", area_id=None, alert_type=None,
                minimum_severity=Severity.HIGH.value, target_role=AppRole.PROVIDER_OPS, priority=20),
    RoutingRule("provider_default", provider_id="*", area_id=None, alert_type=None,
                minimum_severity=Severity.MEDIUM.value, target_role=AppRole.PROVIDER_OPS, priority=30),
    RoutingRule("area_default", provider_id=None, area_id="*", alert_type=None,
                minimum_severity=Severity.MEDIUM.value, target_role=AppRole.FIELD_OFFICER, priority=40),
    RoutingRule("global_fallback", provider_id=None, area_id=None, alert_type=None,
                minimum_severity=Severity.INFO.value, target_role=AppRole.PROVIDER_OPS, priority=100),
)


def _rule_matches(rule: RoutingRule, inp: RoutingInput) -> tuple[bool, str]:
    """Return (matches, specificity). `*` means "requires this dimension set"."""
    if severity_rank(inp.severity) < severity_rank(rule.minimum_severity):
        return False, ""
    if rule.alert_type is not None and rule.alert_type != inp.alert_type:
        return False, ""
    needs_provider = rule.provider_id == "*"
    needs_area = rule.area_id == "*"
    if needs_provider and not inp.provider_id:
        return False, ""
    if needs_area and not inp.area_id:
        return False, ""
    if needs_provider and needs_area:
        return True, "provider_area"
    if needs_provider:
        return True, "provider"
    if needs_area:
        return True, "area"
    return True, "fallback"


_SPECIFICITY_ORDER = {"provider_area": 0, "provider": 1, "area": 2, "fallback": 3}


def resolve_route(
    inp: RoutingInput,
    table: tuple[RoutingRule, ...] = DEFAULT_ROUTING_TABLE,
) -> RoutingDecision:
    """Resolution order: exact provider+area -> provider -> area -> global
    fallback, then lowest priority wins a tie (schema.md 10.5)."""
    candidates: list[tuple[int, int, RoutingRule, str]] = []
    for rule in table:
        ok, specificity = _rule_matches(rule, inp)
        if ok:
            candidates.append((_SPECIFICITY_ORDER[specificity], rule.priority, rule, specificity))
    if not candidates:
        return RoutingDecision(matched=False)
    candidates.sort(key=lambda c: (c[0], c[1]))
    _, _, rule, specificity = candidates[0]
    return RoutingDecision(
        matched=True,
        target_role=rule.target_role,
        rule_name=rule.name,
        specificity=specificity,
    )


# --- Deduplication rules --------------------------------------------------

DEDUPLICATION_VARIABLES: tuple[str, ...] = (
    "outlet_id",
    "provider_id",  # null for shared cash
    "alert_type",
    "condition_window",  # e.g. rounded detection window
)


@dataclass(frozen=True)
class DeduplicationKey:
    """A stable key for active-alert deduplication. Two candidates producing the
    same key within the active window are duplicates; the newer one supersedes
    the older (schema.md unique-partial-index on state='active')."""

    outlet_id: str
    provider_id: str | None
    alert_type: str
    condition_window: str

    def as_string(self) -> str:
        provider = self.provider_id or "shared_cash"
        return f"{self.alert_type}:{provider}:{self.outlet_id}:{self.condition_window}"


def is_duplicate(existing_active_keys: set[str], candidate_key: str) -> bool:
    """Pure check: is this dedup key already active? (Concurrent-duplicate
    resolution and superseding are enforced by a unique index in Phase 3.)"""
    return candidate_key in existing_active_keys
