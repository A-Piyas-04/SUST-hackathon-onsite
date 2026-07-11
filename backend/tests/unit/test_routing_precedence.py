"""Unit tests for coordination routing precedence (docs Phase 5).

resolve_routing only reads routing_rules through session.execute(), so a
stub session exercises the full precedence algorithm without a database:
provider+area > provider-only > area-only > default; ties break on lower
priority; severity must meet the rule minimum; NULL filters are wildcards.
"""

from __future__ import annotations

from uuid import uuid4

from app.services.coordination.routing import resolve_routing

PROVIDER = uuid4()
OTHER_PROVIDER = uuid4()
AREA = uuid4()


class _StubResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _StubSession:
    """Quacks like AsyncSession for resolve_routing's single SELECT."""

    def __init__(self, rows):
        self._rows = rows

    async def execute(self, *_args, **_kwargs):
        return _StubResult(self._rows)


def _rule(
    *,
    provider_id=None,
    area_id=None,
    alert_type=None,
    minimum_severity="info",
    target_role="field_officer",
    priority=100,
):
    return {
        "routing_rule_id": uuid4(),
        "provider_id": provider_id,
        "area_id": area_id,
        "alert_type": alert_type,
        "minimum_severity": minimum_severity,
        "target_role": target_role,
        "priority": priority,
    }


async def test_provider_and_area_rule_beats_provider_only():
    specific = _rule(provider_id=PROVIDER, area_id=AREA, target_role="area_manager")
    broader = _rule(provider_id=PROVIDER, target_role="provider_ops")
    decision = await resolve_routing(
        _StubSession([broader, specific]),
        provider_id=PROVIDER,
        outlet_area_id=AREA,
        alert_type="liquidity",
        severity="high",
    )
    assert decision.target_role == "area_manager"
    assert decision.routing_rule_id == specific["routing_rule_id"]


async def test_lower_priority_breaks_specificity_tie():
    loser = _rule(provider_id=PROVIDER, target_role="management", priority=50)
    winner = _rule(provider_id=PROVIDER, target_role="provider_ops", priority=10)
    decision = await resolve_routing(
        _StubSession([loser, winner]),
        provider_id=PROVIDER,
        outlet_area_id=None,
        alert_type="anomaly",
        severity="medium",
    )
    assert decision.target_role == "provider_ops"


async def test_rule_below_minimum_severity_is_skipped():
    strict = _rule(provider_id=PROVIDER, minimum_severity="critical", target_role="management")
    fallback = _rule(target_role="risk_analyst")
    decision = await resolve_routing(
        _StubSession([strict, fallback]),
        provider_id=PROVIDER,
        outlet_area_id=None,
        alert_type="anomaly",
        severity="low",
    )
    assert decision.target_role == "risk_analyst"


async def test_mismatched_provider_or_alert_type_is_skipped():
    other = _rule(provider_id=OTHER_PROVIDER, target_role="management")
    wrong_type = _rule(alert_type="data_quality", target_role="management")
    decision = await resolve_routing(
        _StubSession([other, wrong_type]),
        provider_id=PROVIDER,
        outlet_area_id=None,
        alert_type="liquidity",
        severity="high",
    )
    # Neither rule matches -> guaranteed default fallback.
    assert decision.routing_rule_id is None
    assert decision.target_role == "field_officer"


async def test_wildcard_rule_matches_any_provider_and_area():
    wildcard = _rule(target_role="risk_analyst", priority=200)
    decision = await resolve_routing(
        _StubSession([wildcard]),
        provider_id=PROVIDER,
        outlet_area_id=AREA,
        alert_type="combined",
        severity="info",
    )
    assert decision.target_role == "risk_analyst"
    assert decision.routing_rule_id == wildcard["routing_rule_id"]


async def test_unknown_severity_treated_as_lowest():
    needs_medium = _rule(minimum_severity="medium", target_role="management")
    decision = await resolve_routing(
        _StubSession([needs_medium]),
        provider_id=None,
        outlet_area_id=None,
        alert_type="liquidity",
        severity="not-a-severity",
    )
    # Unknown severity ranks as 0 -> below 'medium' -> default fallback.
    assert decision.target_role == "field_officer"
