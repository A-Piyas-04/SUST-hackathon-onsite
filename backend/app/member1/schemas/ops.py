from __future__ import annotations

from datetime import datetime

from app.member1.schemas.common import ApiModel
from app.member1.adapters.validation_payload import ValidationMetricPayload


class HealthResponse(ApiModel):
    status: str
    database: str
    env: str
    checked_at: datetime


class MetricsResponse(ApiModel):
    metrics: list[ValidationMetricPayload]
    generated_at: datetime


class ValidationResultsResponse(ApiModel):
    results: list[ValidationMetricPayload]
    generated_at: datetime
