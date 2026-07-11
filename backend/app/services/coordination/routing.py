"""Alert-to-owner routing resolution (docs Phase 5 routing precedence).

Precedence: provider + area -> provider fallback -> area fallback -> default
fallback. A rule matches when its provider/area/alert_type filters are either a
wildcard (NULL) or an exact match, and the alert severity meets the rule minimum.
Among matches, the most specific rule wins; ties break on ``priority`` (lower
wins), matching the seeded ``routing_rules`` table.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class RoutingDecision:
    routing_rule_id: UUID | None
    target_role: str


async def resolve_routing(
    session: AsyncSession,
    *,
    provider_id: UUID | None,
    outlet_area_id: UUID | None,
    alert_type: str,
    severity: str,
) -> RoutingDecision:
    result = await session.execute(
        text(
            """
            SELECT routing_rule_id, provider_id, area_id, alert_type,
                   minimum_severity, target_role, priority
            FROM routing_rules
            WHERE is_active
            """
        )
    )
    rows = [dict(r) for r in result.mappings().all()]
    sev = _SEVERITY_ORDER.get(severity, 0)

    best: dict | None = None
    best_key: tuple[int, int] | None = None
    for r in rows:
        if r["provider_id"] is not None and r["provider_id"] != provider_id:
            continue
        if r["area_id"] is not None and r["area_id"] != outlet_area_id:
            continue
        if r["alert_type"] is not None and r["alert_type"] != alert_type:
            continue
        if sev < _SEVERITY_ORDER.get(r["minimum_severity"], 0):
            continue
        specificity = (2 if r["provider_id"] is not None else 0) + (
            1 if r["area_id"] is not None else 0
        )
        # Higher specificity wins; lower priority breaks ties.
        key = (specificity, -int(r["priority"]))
        if best_key is None or key > best_key:
            best_key = key
            best = r

    if best is None:
        # Guaranteed fallback so a case always has an owner role.
        return RoutingDecision(routing_rule_id=None, target_role="field_officer")
    return RoutingDecision(
        routing_rule_id=best["routing_rule_id"], target_role=best["target_role"]
    )
