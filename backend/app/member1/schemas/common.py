"""Shared response primitives used across every Member 1 schema/router.

Owner: Member 1. Encodes the API-wide conventions from docs/schema.md
Section 16: money as decimal strings (never floats), timestamptz/UTC/ISO 8601,
cursor+limit pagination, and the uniform error envelope.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ApiModel(BaseModel):
    """Base model: camelCase-free, explicit field names matching schema.md exactly."""

    model_config = ConfigDict(populate_by_name=True)


class Money(ApiModel):
    """Wrapper is intentionally NOT used for scalar amounts — money fields on
    response models are plain `Decimal` typed and serialized as decimal
    strings via `MoneyDecimal` below. This class documents the convention.
    """


def _serialize_money(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


class MoneyMixin(BaseModel):
    """Mixin adding a `@field_serializer` that renders every `Decimal` field
    as a plain decimal string (never scientific notation, never a float)."""

    @field_serializer("*", when_used="json")
    def _serialize_decimals(self, value: Any) -> Any:  # noqa: ANN401
        if isinstance(value, Decimal):
            return _serialize_money(value)
        return value


class ErrorDetail(ApiModel):
    code: str
    message: str
    request_id: str
    details: dict[str, Any] | None = None


class ErrorEnvelope(ApiModel):
    """Uniform error shape (schema.md Section 16): unauthorized cross-provider
    lookups return this with a 404 code, identical to a genuinely missing
    record, so existence is never leaked."""

    error: ErrorDetail


T = TypeVar("T")


class CursorPage(ApiModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = Field(default=None, description="Opaque cursor for the next page; null when there are no more results.")
    limit: int


class TimeRangeQuery(ApiModel):
    """`from`/`to` time filter convention. `from_` avoids shadowing the
    Python keyword; the wire field name is `from`."""

    from_: datetime | None = Field(default=None, alias="from")
    to: datetime | None = None


UtcDatetime = datetime
