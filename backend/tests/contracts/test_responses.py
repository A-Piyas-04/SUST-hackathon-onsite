from app.contracts.v1.anomaly import AnomalyFlagOutput
from app.contracts.v1.enums import ReserveType
from app.contracts.v1.liquidity import LiquidityProjectionOutput
from app.contracts.v1.responses import AlertResponse, CaseResponse, DashboardResponse
from app.contracts.v1.validation import ValidationMetricPayload
from tests.contracts.conftest import load_fixture


def test_liquidity_projection_positive():
    projection = LiquidityProjectionOutput.model_validate(load_fixture("liquidity_projection.json"))
    assert projection.reserve_type == ReserveType.SHARED_CASH
    assert projection.provider_id is None
    assert projection.outlet_provider_account_id is None


def test_anomaly_flag_positive():
    AnomalyFlagOutput.model_validate(load_fixture("anomaly_flag.json"))


def test_dashboard_response_positive():
    DashboardResponse.model_validate(load_fixture("dashboard_response.json"))
    dumped = DashboardResponse.model_validate(
        load_fixture("dashboard_response.json")
    ).model_dump()
    assert "total_balance" not in dumped


def test_validation_metric_positive():
    ValidationMetricPayload.model_validate(load_fixture("validation_metric.json"))


def test_alert_response_positive():
    AlertResponse.model_validate(load_fixture("alert_response.json"))


def test_case_response_positive():
    CaseResponse.model_validate(load_fixture("case_response.json"))
