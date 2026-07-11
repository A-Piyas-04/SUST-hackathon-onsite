"""Normalize provider mock shapes into internal contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from app.contracts.v1.enums import FeedEventType, ProviderCode, TransactionStatus, TransactionType
from app.contracts.v1.inputs import (
    NormalizedCashBalanceInput,
    NormalizedProviderBalanceInput,
    NormalizedTransactionInput,
)
from app.services.constants import ACCOUNT_IDS, DEFAULT_OUTLET_ID


class NormalizationError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)


def _parse_dt(value: Any, field: str) -> datetime:
    if value is None:
        raise NormalizationError("missing_field", f"Missing required field: {field}")
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise NormalizationError("invalid_timestamp", f"Invalid timestamp in {field}") from exc


def _parse_decimal(value: Any, field: str) -> Decimal:
    if value is None:
        raise NormalizationError("missing_field", f"Missing required field: {field}")
    try:
        dec = Decimal(str(value))
        if dec < 0:
            raise NormalizationError("invalid_amount", f"Negative amount in {field}")
        return dec
    except (InvalidOperation, ValueError) as exc:
        raise NormalizationError("invalid_amount", f"Invalid amount in {field}") from exc


def normalize_event(
    *,
    provider_code: ProviderCode,
    event_type: FeedEventType,
    payload: dict[str, Any],
    outlet_id: UUID,
    received_at: datetime,
) -> NormalizedTransactionInput | NormalizedCashBalanceInput | NormalizedProviderBalanceInput | None:
    if event_type == FeedEventType.HEARTBEAT:
        return None

    if provider_code == ProviderCode.BKASH:
        return _normalize_bkash(provider_code, event_type, payload, outlet_id, received_at)
    if provider_code == ProviderCode.NAGAD:
        return _normalize_nagad(provider_code, event_type, payload, outlet_id, received_at)
    return _normalize_rocket(provider_code, event_type, payload, outlet_id, received_at)


def _normalize_bkash(
    provider_code: ProviderCode,
    event_type: FeedEventType,
    p: dict[str, Any],
    outlet_id: UUID,
    received_at: datetime,
) -> NormalizedTransactionInput | NormalizedCashBalanceInput | NormalizedProviderBalanceInput:
    if event_type == FeedEventType.TRANSACTION:
        return NormalizedTransactionInput(
            synthetic_transaction_ref=str(p["bkash_trx_id"]),
            synthetic_party_ref=str(p["customer_token"]),
            outlet_id=outlet_id,
            outlet_provider_account_id=ACCOUNT_IDS[provider_code],
            provider_code=provider_code,
            transaction_type=TransactionType(str(p["trx_category"])),
            status=TransactionStatus(str(p["trx_state"])),
            amount=_parse_decimal(p.get("trx_amount"), "trx_amount"),
            occurred_at=_parse_dt(p.get("event_time"), "event_time"),
            received_at=received_at,
        )
    if event_type == FeedEventType.PROVIDER_BALANCE:
        return NormalizedProviderBalanceInput(
            outlet_id=outlet_id,
            outlet_provider_account_id=ACCOUNT_IDS[provider_code],
            provider_code=provider_code,
            balance=_parse_decimal(p.get("wallet_balance"), "wallet_balance"),
            observed_at=_parse_dt(p.get("as_of"), "as_of"),
            received_at=received_at,
        )
    if event_type == FeedEventType.CASH_BALANCE:
        return NormalizedCashBalanceInput(
            outlet_id=UUID(str(p.get("outlet_code", outlet_id))),
            balance=_parse_decimal(p.get("physical_cash"), "physical_cash"),
            observed_at=_parse_dt(p.get("as_of"), "as_of"),
            received_at=received_at,
        )
    raise NormalizationError("unknown_event_type", f"Unsupported event type: {event_type}")


def _normalize_nagad(
    provider_code: ProviderCode,
    event_type: FeedEventType,
    p: dict[str, Any],
    outlet_id: UUID,
    received_at: datetime,
) -> NormalizedTransactionInput | NormalizedCashBalanceInput | NormalizedProviderBalanceInput:
    if event_type == FeedEventType.TRANSACTION:
        return NormalizedTransactionInput(
            synthetic_transaction_ref=str(p["referenceNo"]),
            synthetic_party_ref=str(p["senderId"]),
            outlet_id=outlet_id,
            outlet_provider_account_id=ACCOUNT_IDS[provider_code],
            provider_code=provider_code,
            transaction_type=TransactionType(str(p["type"])),
            status=TransactionStatus(str(p["status"])),
            amount=_parse_decimal(p.get("amount"), "amount"),
            occurred_at=_parse_dt(p.get("timestamp"), "timestamp"),
            received_at=received_at,
        )
    if event_type == FeedEventType.PROVIDER_BALANCE:
        return NormalizedProviderBalanceInput(
            outlet_id=outlet_id,
            outlet_provider_account_id=ACCOUNT_IDS[provider_code],
            provider_code=provider_code,
            balance=_parse_decimal(p.get("availableBalance"), "availableBalance"),
            observed_at=_parse_dt(p.get("balanceTime"), "balanceTime"),
            received_at=received_at,
        )
    if event_type == FeedEventType.CASH_BALANCE:
        return NormalizedCashBalanceInput(
            outlet_id=UUID(str(p.get("outletId", outlet_id))),
            balance=_parse_decimal(p.get("cashInHand"), "cashInHand"),
            observed_at=_parse_dt(p.get("balanceTime"), "balanceTime"),
            received_at=received_at,
        )
    raise NormalizationError("unknown_event_type", f"Unsupported event type: {event_type}")


def _normalize_rocket(
    provider_code: ProviderCode,
    event_type: FeedEventType,
    p: dict[str, Any],
    outlet_id: UUID,
    received_at: datetime,
) -> NormalizedTransactionInput | NormalizedCashBalanceInput | NormalizedProviderBalanceInput:
    if event_type == FeedEventType.TRANSACTION:
        return NormalizedTransactionInput(
            synthetic_transaction_ref=str(p["rocket_txn_ref"]),
            synthetic_party_ref=str(p["counterparty_ref"]),
            outlet_id=outlet_id,
            outlet_provider_account_id=ACCOUNT_IDS[provider_code],
            provider_code=provider_code,
            transaction_type=TransactionType(str(p["operation"])),
            status=TransactionStatus(str(p["completion_status"])),
            amount=_parse_decimal(p.get("value"), "value"),
            occurred_at=_parse_dt(p.get("when"), "when"),
            received_at=received_at,
        )
    if event_type == FeedEventType.PROVIDER_BALANCE:
        return NormalizedProviderBalanceInput(
            outlet_id=outlet_id,
            outlet_provider_account_id=ACCOUNT_IDS[provider_code],
            provider_code=provider_code,
            balance=_parse_decimal(p.get("current_value"), "current_value"),
            observed_at=_parse_dt(p.get("when"), "when"),
            received_at=received_at,
        )
    if event_type == FeedEventType.CASH_BALANCE:
        return NormalizedCashBalanceInput(
            outlet_id=UUID(str(p.get("outlet_uuid", outlet_id))),
            balance=_parse_decimal(p.get("drawer_value"), "drawer_value"),
            observed_at=_parse_dt(p.get("when"), "when"),
            received_at=received_at,
        )
    raise NormalizationError("unknown_event_type", f"Unsupported event type: {event_type}")
