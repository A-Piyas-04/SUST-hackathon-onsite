"""Append-only ledger writer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.inputs import (
    NormalizedCashBalanceInput,
    NormalizedProviderBalanceInput,
    NormalizedTransactionInput,
)
from app.services.constants import PROVIDER_IDS


async def write_transaction(
    session: AsyncSession,
    *,
    ingestion_event_id: UUID,
    simulation_run_id: UUID,
    data: NormalizedTransactionInput,
) -> UUID | None:
    existing = await session.execute(
        text(
            """
            SELECT transaction_id FROM transactions
            WHERE provider_id = :provider_id AND synthetic_transaction_ref = :ref
            """
        ),
        {"provider_id": PROVIDER_IDS[data.provider_code], "ref": data.synthetic_transaction_ref},
    )
    row = existing.first()
    if row:
        return row[0]

    txn_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO transactions (
              transaction_id, ingestion_event_id, simulation_run_id,
              outlet_provider_account_id, provider_id, outlet_id,
              synthetic_transaction_ref, synthetic_party_ref,
              transaction_type, status, amount, currency_code,
              occurred_at, received_at
            ) VALUES (
              :transaction_id, :ingestion_event_id, :simulation_run_id,
              :account_id, :provider_id, :outlet_id,
              :ref, :party, :txn_type, :status, :amount, :currency,
              :occurred_at, :received_at
            )
            """
        ),
        {
            "transaction_id": txn_id,
            "ingestion_event_id": ingestion_event_id,
            "simulation_run_id": simulation_run_id,
            "account_id": data.outlet_provider_account_id,
            "provider_id": PROVIDER_IDS[data.provider_code],
            "outlet_id": data.outlet_id,
            "ref": data.synthetic_transaction_ref,
            "party": data.synthetic_party_ref,
            "txn_type": data.transaction_type.value,
            "status": data.status.value,
            "amount": data.amount,
            "currency": data.currency_code,
            "occurred_at": data.occurred_at,
            "received_at": data.received_at,
        },
    )
    return txn_id


async def write_cash_snapshot(
    session: AsyncSession,
    *,
    ingestion_event_id: UUID,
    simulation_run_id: UUID,
    data: NormalizedCashBalanceInput,
) -> UUID:
    snap_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO cash_balance_snapshots (
              cash_balance_snapshot_id, ingestion_event_id, simulation_run_id,
              outlet_id, balance, currency_code, observed_at, received_at, source_kind
            ) VALUES (
              :id, :event_id, :run_id, :outlet_id, :balance, :currency,
              :observed_at, :received_at, :source_kind
            )
            """
        ),
        {
            "id": snap_id,
            "event_id": ingestion_event_id,
            "run_id": simulation_run_id,
            "outlet_id": data.outlet_id,
            "balance": data.balance,
            "currency": data.currency_code,
            "observed_at": data.observed_at,
            "received_at": data.received_at,
            "source_kind": data.source_kind,
        },
    )
    return snap_id


async def write_provider_snapshot(
    session: AsyncSession,
    *,
    ingestion_event_id: UUID,
    simulation_run_id: UUID,
    data: NormalizedProviderBalanceInput,
) -> UUID:
    snap_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO provider_balance_snapshots (
              provider_balance_snapshot_id, ingestion_event_id, simulation_run_id,
              outlet_provider_account_id, provider_id, outlet_id,
              balance, currency_code, observed_at, received_at, source_kind
            ) VALUES (
              :id, :event_id, :run_id, :account_id, :provider_id, :outlet_id,
              :balance, :currency, :observed_at, :received_at, :source_kind
            )
            """
        ),
        {
            "id": snap_id,
            "event_id": ingestion_event_id,
            "run_id": simulation_run_id,
            "account_id": data.outlet_provider_account_id,
            "provider_id": PROVIDER_IDS[data.provider_code],
            "outlet_id": data.outlet_id,
            "balance": data.balance,
            "currency": data.currency_code,
            "observed_at": data.observed_at,
            "received_at": data.received_at,
            "source_kind": data.source_kind,
        },
    )
    return snap_id


async def count_ledger_rows(session: AsyncSession, run_id: UUID) -> dict[str, int]:
    result = await session.execute(
        text(
            """
            SELECT
              (SELECT count(*) FROM transactions WHERE simulation_run_id = :run_id) AS txns,
              (SELECT count(*) FROM cash_balance_snapshots WHERE simulation_run_id = :run_id) AS cash,
              (SELECT count(*) FROM provider_balance_snapshots WHERE simulation_run_id = :run_id) AS prov
            """
        ),
        {"run_id": run_id},
    )
    row = result.mappings().one()
    return {"transactions": row["txns"], "cash_snapshots": row["cash"], "provider_snapshots": row["prov"]}
