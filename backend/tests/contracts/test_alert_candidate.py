import pytest
from pydantic import ValidationError

from app.contracts.v1.alert_candidate import AlertCandidate
from tests.contracts.conftest import load_fixture


def test_alert_candidate_fixture_is_valid_without_case_fields():
    candidate = AlertCandidate.model_validate(load_fixture("alert_candidate.json"))
    dumped = candidate.model_dump()
    for forbidden in ("status", "current_owner_user_id", "version", "resolution_summary"):
        assert forbidden not in dumped


def test_alert_candidate_rejects_unsafe_language():
    with pytest.raises(ValidationError):
        AlertCandidate.model_validate(
            load_fixture("alert_candidate_unsafe_language.json", positive=False)
        )
