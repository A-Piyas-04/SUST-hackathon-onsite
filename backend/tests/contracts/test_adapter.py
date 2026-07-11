from uuid import UUID

from app.contracts.v1.alert_candidate import AlertCandidate
from app.contracts.v1.envelope import ResultEnvelope
from app.services.alert_candidate_adapter import envelope_to_alert_candidate
from tests.contracts.conftest import load_fixture

OUTLET1 = UUID("0b000000-0000-0000-0000-000000000001")
BKASH = UUID("11111111-1111-1111-1111-111111111111")


def test_liquidity_envelope_produces_alert_candidate():
    envelope = ResultEnvelope.model_validate(load_fixture("result_envelope_liquidity.json"))
    candidate = envelope_to_alert_candidate(envelope, outlet_id=OUTLET1)
    assert candidate is not None
    AlertCandidate.model_validate(candidate.model_dump(mode="json"))
    assert candidate.alert_type.value == "liquidity"
    assert candidate.is_alertable is True
    assert candidate.provider_id == BKASH


def test_anomaly_envelope_produces_alert_candidate():
    envelope = ResultEnvelope.model_validate(load_fixture("result_envelope_anomaly.json"))
    candidate = envelope_to_alert_candidate(envelope, outlet_id=OUTLET1)
    assert candidate is not None
    assert candidate.alert_type.value == "anomaly"
    assert candidate.plausible_benign_explanation


def test_non_actionable_envelope_returns_none():
    envelope = ResultEnvelope.model_validate(
        load_fixture("result_envelope_non_actionable.json", positive=False)
    )
    assert envelope_to_alert_candidate(envelope, outlet_id=OUTLET1) is None
