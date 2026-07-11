from __future__ import annotations

from uuid import UUID

from app.member1.schemas.common import ApiModel


class ProviderOut(ApiModel):
    provider_id: UUID
    code: str
    display_name: str
    display_color: str | None = None
    is_active: bool


class AreaOut(ApiModel):
    area_id: UUID
    parent_area_id: UUID | None = None
    code: str
    name: str
    level: str
    is_active: bool


class OutletOut(ApiModel):
    outlet_id: UUID
    synthetic_code: str
    display_name: str
    area_id: UUID | None = None
    currency_code: str
    is_active: bool
    active_provider_codes: list[str] = []
