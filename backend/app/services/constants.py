"""Shared provider/outlet identity constants for Phase 3 services."""

from __future__ import annotations

from uuid import UUID

from app.contracts.v1.enums import ProviderCode
from app.core.auth import BKASH, NAGAD, OUTLET1, ROCKET

# Outlet-provider accounts for OUTLET1 (reference_seed.sql)
ACCOUNT_BKASH = UUID("e1000000-0000-0000-0000-000000000001")
ACCOUNT_NAGAD = UUID("e2000000-0000-0000-0000-000000000001")
ACCOUNT_ROCKET = UUID("e3000000-0000-0000-0000-000000000001")

PROVIDER_IDS: dict[ProviderCode, UUID] = {
    ProviderCode.BKASH: BKASH,
    ProviderCode.NAGAD: NAGAD,
    ProviderCode.ROCKET: ROCKET,
}

ACCOUNT_IDS: dict[ProviderCode, UUID] = {
    ProviderCode.BKASH: ACCOUNT_BKASH,
    ProviderCode.NAGAD: ACCOUNT_NAGAD,
    ProviderCode.ROCKET: ACCOUNT_ROCKET,
}

DEFAULT_OUTLET_ID = OUTLET1

BASE_TIMESTAMP_ISO = "2026-07-11T06:00:00+00:00"

INTERIM_PROJECTION = {
    "shortage_at": None,
    "confidence_score": "0",
    "confidence_level": "unavailable",
}
