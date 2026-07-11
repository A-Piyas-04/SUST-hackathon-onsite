import pytest
from pydantic import ValidationError

from app.contracts.v1.envelope import ResultEnvelope
from app.contracts.v1.quality import QualityAssessmentInput
from tests.contracts.conftest import load_fixture


def test_quality_assessment_positive():
    QualityAssessmentInput.model_validate(load_fixture("quality_assessment.json"))


def test_quality_assessment_bad_modifier():
    with pytest.raises(ValidationError):
        QualityAssessmentInput.model_validate(
            load_fixture("quality_assessment_bad_modifier.json", positive=False)
        )


def test_result_envelope_liquidity_positive():
    ResultEnvelope.model_validate(load_fixture("result_envelope_liquidity.json"))


def test_result_envelope_anomaly_positive():
    ResultEnvelope.model_validate(load_fixture("result_envelope_anomaly.json"))
