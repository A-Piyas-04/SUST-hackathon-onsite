"""Shared contract primitives: money, timestamps, confidence, evidence."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

BANNED_WORDS = re.compile(
    r"\b(fraud|fraudster|blocked|frozen|accuse|accusation)\b", re.IGNORECASE
)


def _serialize_decimal(value: Decimal) -> str:
    return format(value, "f")


MoneyDecimal = Annotated[
    Decimal,
    Field(ge=0, decimal_places=2, max_digits=20),
    PlainSerializer(_serialize_decimal, return_type=str, when_used="json"),
]


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware (UTC).")
    return value.astimezone(timezone.utc)


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Confidence(ContractModel):
    score: Annotated[Decimal, Field(ge=0, le=1, decimal_places=4, max_digits=6)]
    level: str
    feed_status: str | None = None


class EvidenceItem(ContractModel):
    evidence_type: str | None = None
    signal_code: str | None = None
    label: str
    value: Any = None
    numeric_value: float | Decimal | None = None
    unit: str | None = None
    direction: str | None = None
    display_order: int | None = None


def validate_safe_language(text: str, field_name: str) -> str:
    if BANNED_WORDS.search(text):
        raise ValueError(f"{field_name} must use safe advisory language only.")
    return text
