"""Contract tests: enums load, error shape, locale enum, candidate field
validation primitives (schema/version/type/severity/scope consistency)."""
from __future__ import annotations

import pytest

from app.coordination.shared import enums
from app.coordination.shared.enums import (
    SUPPORTED_CANDIDATE_VERSIONS,
    AlertType,
    AppRole,
    CaseStatus,
    LocaleCode,
    ReviewOutcome,
    Severity,
)
from app.coordination.shared.errors import (
    ErrorCode,
    new_request_id,
    not_found,
    validate_error_shape,
)


def test_all_coordination_enums_load():
    assert set(AppRole) == {
        AppRole.AGENT, AppRole.FIELD_OFFICER, AppRole.AREA_MANAGER,
        AppRole.PROVIDER_OPS, AppRole.RISK_ANALYST, AppRole.MANAGEMENT, AppRole.ADMIN,
    }
    assert set(CaseStatus) == {CaseStatus.OPEN, CaseStatus.ACKNOWLEDGED, CaseStatus.ESCALATED, CaseStatus.RESOLVED}
    assert set(LocaleCode) == {LocaleCode.EN, LocaleCode.BN, LocaleCode.BN_LATN}


def test_no_fraud_or_financial_enum_values():
    forbidden = {"fraud", "fraudster", "blocked", "frozen", "confirmed_fraud"}
    for enum_cls in (AppRole, CaseStatus, ReviewOutcome, AlertType, Severity):
        values = {e.value for e in enum_cls}
        assert not (values & forbidden), f"{enum_cls.__name__} exposes forbidden value"


def test_review_outcome_has_no_fraud_verdict():
    # A fraud verdict must be structurally impossible.
    assert "fraud" not in {v.value for v in ReviewOutcome}


def test_error_shape_is_valid_and_has_request_id():
    err = not_found()
    body = err.to_response()
    validate_error_shape(body)  # raises if invalid
    assert body["error"]["request_id"]
    assert body["error"]["code"] == ErrorCode.NOT_FOUND.value


def test_error_details_reject_leaks():
    from app.coordination.shared.errors import ApiError

    # An unsafe detail value is redacted rather than surfaced.
    err = ApiError(code=ErrorCode.VALIDATION_ERROR, message="bad", details={"reason": "Bearer eyJabc.def.ghi"})
    assert "Bearer" not in str(err.details)


def test_request_ids_unique():
    assert new_request_id() != new_request_id()


def test_candidate_version_set_frozen():
    assert "1" in SUPPORTED_CANDIDATE_VERSIONS
    assert "99" not in SUPPORTED_CANDIDATE_VERSIONS


def test_valid_alert_types_match_schema():
    from app.coordination.alerts.candidate import VALID_ALERT_TYPES

    assert VALID_ALERT_TYPES == {"liquidity", "anomaly", "combined", "data_quality"}


@pytest.mark.parametrize("severity", ["info", "low", "medium", "high", "critical"])
def test_severities_recognised(severity):
    from app.coordination.alerts.candidate import VALID_SEVERITIES

    assert severity in VALID_SEVERITIES


def test_shared_analytical_enums_reused_from_member1():
    # AlertType/Severity/ConfidenceLevel are re-exported, not duplicated.
    from app.shared import enums as m1

    assert enums.AlertType is m1.AlertType
    assert enums.Severity is m1.Severity
