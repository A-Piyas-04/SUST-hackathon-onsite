"""Provider-specific mock payload adapters."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.contracts.v1.enums import FeedEventType, ProviderCode


def to_provider_shape(provider: ProviderCode, event_type: FeedEventType, payload: dict[str, Any]) -> dict[str, Any]:
    """Wrap normalized-ish payload into provider-specific mock shapes."""
    if provider == ProviderCode.BKASH:
        return _bkash_shape(event_type, payload)
    if provider == ProviderCode.NAGAD:
        return _nagad_shape(event_type, payload)
    return _rocket_shape(event_type, payload)


def _bkash_shape(event_type: FeedEventType, p: dict[str, Any]) -> dict[str, Any]:
    if event_type == FeedEventType.TRANSACTION:
        return {
            "bkash_trx_id": p.get("txn_ref"),
            "customer_token": p.get("party_ref"),
            "merchant_account": p.get("account_ref"),
            "trx_category": p.get("txn_type"),
            "trx_state": p.get("status"),
            "trx_amount": p.get("amount"),
            "ccy": p.get("currency", "BDT"),
            "event_time": p.get("occurred_at"),
        }
    if event_type == FeedEventType.PROVIDER_BALANCE:
        return {
            "merchant_account": p.get("account_ref"),
            "wallet_balance": p.get("balance"),
            "ccy": p.get("currency", "BDT"),
            "as_of": p.get("observed_at"),
        }
    if event_type == FeedEventType.CASH_BALANCE:
        return {
            "outlet_code": p.get("outlet_id"),
            "physical_cash": p.get("balance"),
            "ccy": p.get("currency", "BDT"),
            "as_of": p.get("observed_at"),
        }
    return p


def _nagad_shape(event_type: FeedEventType, p: dict[str, Any]) -> dict[str, Any]:
    if event_type == FeedEventType.TRANSACTION:
        return {
            "referenceNo": p.get("txn_ref"),
            "senderId": p.get("party_ref"),
            "accountNo": p.get("account_ref"),
            "type": p.get("txn_type"),
            "status": p.get("status"),
            "amount": p.get("amount"),
            "currencyCode": p.get("currency", "BDT"),
            "timestamp": p.get("occurred_at"),
        }
    if event_type == FeedEventType.PROVIDER_BALANCE:
        return {
            "accountNo": p.get("account_ref"),
            "availableBalance": p.get("balance"),
            "currencyCode": p.get("currency", "BDT"),
            "balanceTime": p.get("observed_at"),
        }
    if event_type == FeedEventType.CASH_BALANCE:
        return {
            "outletId": p.get("outlet_id"),
            "cashInHand": p.get("balance"),
            "currencyCode": p.get("currency", "BDT"),
            "balanceTime": p.get("observed_at"),
        }
    return p


def _rocket_shape(event_type: FeedEventType, p: dict[str, Any]) -> dict[str, Any]:
    if event_type == FeedEventType.TRANSACTION:
        return {
            "rocket_txn_ref": p.get("txn_ref"),
            "counterparty_ref": p.get("party_ref"),
            "agent_account": p.get("account_ref"),
            "operation": p.get("txn_type"),
            "completion_status": p.get("status"),
            "value": p.get("amount"),
            "unit": p.get("currency", "BDT"),
            "when": p.get("occurred_at"),
        }
    if event_type == FeedEventType.PROVIDER_BALANCE:
        return {
            "agent_account": p.get("account_ref"),
            "current_value": p.get("balance"),
            "unit": p.get("currency", "BDT"),
            "when": p.get("observed_at"),
        }
    if event_type == FeedEventType.CASH_BALANCE:
        return {
            "outlet_uuid": p.get("outlet_id"),
            "drawer_value": p.get("balance"),
            "unit": p.get("currency", "BDT"),
            "when": p.get("observed_at"),
        }
    return p


def parse_received_at(payload: dict[str, Any], fallback: datetime) -> datetime:
    for key in ("event_time", "timestamp", "when", "as_of", "balanceTime"):
        if key in payload and payload[key]:
            return datetime.fromisoformat(str(payload[key]).replace("Z", "+00:00"))
    return fallback
