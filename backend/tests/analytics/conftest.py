from datetime import datetime, timezone

import pytest

from backend.analytics.fixtures.synthetic_generator_stub import (
    make_quality_assessment,
    make_transaction,
)

BASE_TIME = datetime(2026, 7, 11, 8, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def base_time() -> datetime:
    return BASE_TIME


@pytest.fixture
def fresh_quality():
    def _build(*, provider_code="bkash", outlet_id="outlet-1"):
        return make_quality_assessment(
            outlet_id=outlet_id,
            provider_code=provider_code,
            status="fresh",
            confidence_modifier=1.0,
            sample_count=10,
            assessed_at=BASE_TIME,
        )

    return _build


@pytest.fixture
def degraded_quality():
    def _build(*, provider_code="bkash", outlet_id="outlet-1"):
        return make_quality_assessment(
            outlet_id=outlet_id,
            provider_code=provider_code,
            status="stale",
            confidence_modifier=0.3,
            sample_count=2,
            assessed_at=BASE_TIME,
        )

    return _build


@pytest.fixture
def txn_factory():
    return make_transaction
