"""Role/scope authorization policy tests (member-2 plan 7.1).

The runtime middleware is Phase 2; these prove the decision core now, including
the hard invariant that a missing provider scope is never a wildcard.
"""
from __future__ import annotations

from app.coordination.auth.policies import (
    ROLE_SCOPE_MATRIX,
    AccessDecision,
    ResourceScope,
    ScopeDimension,
    evaluate_read,
    has_minimum_scope,
    required_scopes,
)
from app.coordination.shared.enums import AppRole
from app.coordination.shared.references import CallerScope

# Resources
BKASH_OUTLET1 = ResourceScope(provider_id="prov_bkash", outlet_id="outlet_001", area_id="area_market")
NAGAD_OUTLET1 = ResourceScope(provider_id="prov_nagad", outlet_id="outlet_001", area_id="area_market")
SHARED_OUTLET1 = ResourceScope(provider_id=None, outlet_id="outlet_001", area_id="area_market")


def caller(role, *, providers=(), areas=(), outlets=(), active=True, user="u"):
    return CallerScope(
        user_id=user, roles=frozenset({role}),
        provider_ids=frozenset(providers), area_ids=frozenset(areas),
        outlet_ids=frozenset(outlets), is_active=active,
    )


def test_matrix_has_all_seven_roles():
    assert set(ROLE_SCOPE_MATRIX.keys()) == {r.value for r in AppRole}


def test_agent_can_read_own_outlet():
    c = caller(AppRole.AGENT, outlets=["outlet_001"])
    assert evaluate_read(c, BKASH_OUTLET1).allowed


def test_agent_cannot_read_other_outlet():
    c = caller(AppRole.AGENT, outlets=["outlet_002"])
    assert not evaluate_read(c, BKASH_OUTLET1).allowed


def test_provider_ops_reads_own_provider():
    c = caller(AppRole.PROVIDER_OPS, providers=["prov_bkash"])
    assert evaluate_read(c, BKASH_OUTLET1).allowed


def test_provider_ops_cannot_read_other_provider():
    c = caller(AppRole.PROVIDER_OPS, providers=["prov_bkash"])
    assert not evaluate_read(c, NAGAD_OUTLET1).allowed


def test_missing_provider_scope_is_not_wildcard():
    # provider_ops with NO provider scope must reach nothing, not everything.
    c = caller(AppRole.PROVIDER_OPS, providers=[])
    assert not evaluate_read(c, BKASH_OUTLET1).allowed
    assert not evaluate_read(c, NAGAD_OUTLET1).allowed
    assert not evaluate_read(c, SHARED_OUTLET1).allowed


def test_field_officer_correct_provider_and_area():
    c = caller(AppRole.FIELD_OFFICER, providers=["prov_bkash"], areas=["area_market"])
    assert evaluate_read(c, BKASH_OUTLET1).allowed


def test_field_officer_wrong_provider_denied():
    c = caller(AppRole.FIELD_OFFICER, providers=["prov_bkash"], areas=["area_market"])
    assert not evaluate_read(c, NAGAD_OUTLET1).allowed


def test_risk_analyst_own_provider():
    c = caller(AppRole.RISK_ANALYST, providers=["prov_bkash"])
    assert evaluate_read(c, BKASH_OUTLET1).allowed


def test_management_without_explicit_scope_no_raw_evidence():
    c = caller(AppRole.MANAGEMENT)  # aggregate, no explicit provider scope
    assert not evaluate_read(c, BKASH_OUTLET1).allowed


def test_management_with_explicit_provider_scope_allowed():
    c = caller(AppRole.MANAGEMENT, providers=["prov_bkash"])
    d = evaluate_read(c, BKASH_OUTLET1)
    assert d.allowed and d.reason == "management_explicit_provider_scope"


def test_admin_is_not_operational_shortcut():
    c = caller(AppRole.ADMIN, providers=["prov_bkash"])
    assert not evaluate_read(c, BKASH_OUTLET1).allowed


def test_inactive_user_denied():
    c = caller(AppRole.PROVIDER_OPS, providers=["prov_bkash"], active=False)
    d = evaluate_read(c, BKASH_OUTLET1)
    assert not d.allowed and d.reason == "inactive_user"


def test_has_minimum_scope():
    assert not has_minimum_scope(caller(AppRole.PROVIDER_OPS, providers=[]), AppRole.PROVIDER_OPS)
    assert has_minimum_scope(caller(AppRole.PROVIDER_OPS, providers=["prov_bkash"]), AppRole.PROVIDER_OPS)
    assert not has_minimum_scope(caller(AppRole.AGENT, outlets=[]), AppRole.AGENT)


def test_required_scopes_frozen():
    assert required_scopes(AppRole.AGENT) == frozenset({ScopeDimension.OUTLET})
    assert required_scopes(AppRole.FIELD_OFFICER) == frozenset({ScopeDimension.PROVIDER, ScopeDimension.AREA})
    assert required_scopes(AppRole.PROVIDER_OPS) == frozenset({ScopeDimension.PROVIDER})


def test_management_and_admin_are_read_only():
    assert ROLE_SCOPE_MATRIX[AppRole.MANAGEMENT].read_only
    assert ROLE_SCOPE_MATRIX[AppRole.ADMIN].read_only


def test_no_role_grants_raw_cross_provider_by_default():
    for policy in ROLE_SCOPE_MATRIX.values():
        assert policy.can_view_raw_cross_provider is False
