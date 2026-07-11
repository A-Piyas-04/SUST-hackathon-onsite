"""AlertCandidate consumer tests: valid fixtures accepted, invalid fixtures
rejected with the expected stable rejection codes."""
from __future__ import annotations

import pytest

from app.coordination.alerts.candidate import (
    AlertCandidate,
    RejectionCode,
    validate_candidate,
)


def test_all_valid_candidates_accepted(valid_candidates, lookup):
    for name, data in valid_candidates.items():
        candidate = AlertCandidate.from_dict(data)
        result = validate_candidate(candidate, lookup)
        assert result.accepted, f"{name} should be accepted; got {result.codes}"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "liquidity_candidate", "anomaly_candidate", "combined_candidate",
        "data_quality_candidate", "shared_cash_candidate",
        "provider_scoped_candidate", "advisory_no_case_candidate",
    ],
)
def test_named_valid_candidate_accepted(fixture_name, valid_candidates, lookup):
    candidate = AlertCandidate.from_dict(valid_candidates[fixture_name])
    assert validate_candidate(candidate, lookup).accepted


def test_all_invalid_candidates_rejected_with_expected_codes(invalid_candidates, lookup):
    for name, data in invalid_candidates.items():
        expected = set(data.get("_expected_rejections", []))
        candidate = AlertCandidate.from_dict(data)
        result = validate_candidate(candidate, lookup)
        assert not result.accepted, f"{name} should be rejected"
        got = set(result.codes)
        missing = expected - got
        assert not missing, f"{name}: expected rejection codes {missing} not in {got}"


def test_suppressed_anomaly_cannot_become_anomaly_alert(invalid_candidates, lookup):
    candidate = AlertCandidate.from_dict(invalid_candidates["suppressed_anomaly"])
    result = validate_candidate(candidate, lookup)
    assert RejectionCode.SUPPRESSED_ANOMALY.value in result.codes


def test_missing_benign_context_rejected(invalid_candidates, lookup):
    candidate = AlertCandidate.from_dict(invalid_candidates["missing_benign"])
    result = validate_candidate(candidate, lookup)
    assert RejectionCode.MISSING_BENIGN_CONTEXT.value in result.codes


def test_unsafe_next_step_rejected(invalid_candidates, lookup):
    candidate = AlertCandidate.from_dict(invalid_candidates["unsafe_recommendation"])
    result = validate_candidate(candidate, lookup)
    assert RejectionCode.UNSAFE_RECOMMENDED_ACTION.value in result.codes


def test_fraud_wording_rejected(invalid_candidates, lookup):
    candidate = AlertCandidate.from_dict(invalid_candidates["unsafe_wording"])
    result = validate_candidate(candidate, lookup)
    assert RejectionCode.UNSAFE_STRUCTURED_VARIABLE.value in result.codes


def test_cross_provider_source_mismatch_rejected(invalid_candidates, lookup):
    candidate = AlertCandidate.from_dict(invalid_candidates["provider_mismatch"])
    result = validate_candidate(candidate, lookup)
    assert RejectionCode.PROVIDER_SCOPE_MISMATCH.value in result.codes


def test_unsupported_version_rejected(invalid_candidates, lookup):
    candidate = AlertCandidate.from_dict(invalid_candidates["unsupported_version"])
    result = validate_candidate(candidate, lookup)
    assert RejectionCode.UNSUPPORTED_CANDIDATE_VERSION.value in result.codes


def test_missing_source_rejected(invalid_candidates, lookup):
    candidate = AlertCandidate.from_dict(invalid_candidates["missing_source"])
    result = validate_candidate(candidate, lookup)
    assert RejectionCode.MISSING_SOURCE_RESULTS.value in result.codes


def test_validator_does_not_recompute_confidence(valid_candidates, lookup):
    # Member 2 must never derive/override confidence — the validator only reads
    # structured variables. Injecting an override key is rejected.
    data = dict(valid_candidates["liquidity_candidate"])
    data["structured_variables"] = dict(data["structured_variables"])
    data["structured_variables"]["confidence_override"] = 0.99
    candidate = AlertCandidate.from_dict(data)
    result = validate_candidate(candidate, lookup)
    assert RejectionCode.CONFIDENCE_OVERRIDE_ATTEMPT.value in result.codes
