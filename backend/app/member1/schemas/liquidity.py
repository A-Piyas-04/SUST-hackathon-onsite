from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.member1.schemas.common import ApiModel


class LiquidityProjectionOut(ApiModel):
    liquidity_projection_id: UUID
    analytics_run_id: UUID
    outlet_id: UUID
    reserve_type: str
    outlet_provider_account_id: UUID | None = None
    provider_id: UUID | None = None
    as_of_at: datetime
    current_balance: str
    burn_rate_per_hour: str
    projected_shortage_at: datetime | None = None
    lower_bound_at: datetime | None = None
    upper_bound_at: datetime | None = None
    confidence_score: float
    confidence_level: str
    sample_count: int
    is_actionable: bool
    non_actionable_reason: str | None = None
