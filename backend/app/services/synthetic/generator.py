"""Deterministic seeded event generator for one outlet + three providers."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.contracts.v1.enums import FeedEventType, ProviderCode, ScenarioCode, TransactionStatus, TransactionType
from app.services.constants import ACCOUNT_IDS, DEFAULT_OUTLET_ID, PROVIDER_IDS
from app.services.synthetic.clock import batch_time, event_time


@dataclass
class GeneratedEvent:
    event_type: FeedEventType
    provider_code: ProviderCode | None
    source_event_ref: str
    source_observed_at: datetime
    payload: dict[str, Any]


@dataclass
class GeneratedBatch:
    provider_code: ProviderCode
    source_batch_ref: str
    source_generated_at: datetime
    events: list[GeneratedEvent] = field(default_factory=list)
    is_cash_batch: bool = False


@dataclass
class GenerationResult:
    outlet_id: UUID
    batches: list[GeneratedBatch]
    semantic_fingerprint: list[dict[str, Any]]


def _amount(rng: random.Random, base: float, spread: float = 0.2) -> str:
    value = base * (1 + rng.uniform(-spread, spread))
    return f"{value:.2f}"


def _q2(value: Decimal) -> Decimal:
    """Quantize money to 2 decimal places (feeds reject >2dp as malformed)."""
    return value.quantize(Decimal("0.01"))


def _party_ref(rng: random.Random, provider: ProviderCode, idx: int) -> str:
    return f"PARTY-{provider.value.upper()}-{idx:04d}"


def generate_dataset(
    *,
    scenario_code: ScenarioCode,
    seed: int,
    config: dict[str, Any],
    outlet_id: UUID = DEFAULT_OUTLET_ID,
) -> GenerationResult:
    rng = random.Random(seed)
    txn_count = int(config.get("transaction_count", 12))
    batches: list[GeneratedBatch] = []
    fingerprint: list[dict[str, Any]] = []

    # Initial balances
    cash_balance = Decimal(config.get("initial_cash", "85000.00"))
    provider_balances: dict[ProviderCode, Decimal] = {
        ProviderCode.BKASH: Decimal(config.get("initial_bkash", "42000.00")),
        ProviderCode.NAGAD: Decimal(config.get("initial_nagad", "38000.00")),
        ProviderCode.ROCKET: Decimal(config.get("initial_rocket", "31000.00")),
    }

    event_idx = 0
    batch_idx = 0

    # Cash balance batch (carrier provider bkash for batch metadata)
    cash_batch = GeneratedBatch(
        provider_code=ProviderCode.BKASH,
        source_batch_ref=f"CASH-{seed}-B0",
        source_generated_at=batch_time(batch_idx),
        is_cash_batch=True,
    )
    obs = event_time(event_idx)
    cash_batch.events.append(
        GeneratedEvent(
            event_type=FeedEventType.CASH_BALANCE,
            provider_code=None,
            source_event_ref=f"CASH-SNAP-{seed}-0",
            source_observed_at=obs,
            payload={
                "outlet_id": str(outlet_id),
                "balance": str(_q2(cash_balance)),
                "currency": "BDT",
                "observed_at": obs.isoformat(),
            },
        )
    )
    fingerprint.append({"type": "cash_balance", "balance": str(_q2(cash_balance)), "observed_at": obs.isoformat()})
    batches.append(cash_batch)
    batch_idx += 1
    event_idx += 1

    target_provider = ProviderCode(config.get("target_provider", "bkash"))
    cluster_amount = Decimal(config.get("cluster_amount", "1000.00"))
    cluster_provider = ProviderCode(config.get("cluster_provider", "bkash"))
    cluster_count = int(config.get("cluster_count", 6))
    cluster_step_minutes = int(config.get("cluster_step_minutes", 2))
    # Scenarios B and C both rely on a near-identical-amount cluster. Scenario C
    # additionally injects a conflicting balance snapshot so data quality degrades
    # and the (still-detected) cluster is safely suppressed rather than alerted.
    scenarios_with_cluster = {ScenarioCode.SCENARIO_B, ScenarioCode.SCENARIO_C}
    cluster_anchor = event_time(2)

    for provider in (ProviderCode.BKASH, ProviderCode.NAGAD, ProviderCode.ROCKET):
        batch = GeneratedBatch(
            provider_code=provider,
            source_batch_ref=f"{provider.value.upper()}-{seed}-B{batch_idx}",
            source_generated_at=batch_time(batch_idx),
        )
        batch_idx += 1
        is_cluster_provider = (
            scenario_code in scenarios_with_cluster and provider == cluster_provider
        )

        # Opening provider balance snapshot
        bal_obs = event_time(event_idx)
        batch.events.append(
            GeneratedEvent(
                event_type=FeedEventType.PROVIDER_BALANCE,
                provider_code=provider,
                source_event_ref=f"{provider.value.upper()}-BAL-{seed}-0",
                source_observed_at=bal_obs,
                payload={
                    "account_ref": f"ACCT-O1-{provider.value.upper()}",
                    "balance": str(provider_balances[provider]),
                    "currency": "BDT",
                    "observed_at": bal_obs.isoformat(),
                },
            )
        )
        fingerprint.append(
            {
                "type": "provider_balance",
                "provider": provider.value,
                "balance": str(provider_balances[provider]),
                "observed_at": bal_obs.isoformat(),
            }
        )
        event_idx += 1

        # Transactions per provider
        per_provider_txns = max(2, txn_count // 3)
        if is_cluster_provider:
            per_provider_txns = max(per_provider_txns, cluster_count)
        for t in range(per_provider_txns):
            txn_obs = event_time(event_idx)
            event_idx += 1

            # Directional balance effect (double-entry, 1:1):
            #   cash_out — the agent pays physical cash to a customer who sent
            #     e-money to the agent's provider account: shared cash DECREASES,
            #     provider e-money INCREASES.
            #   cash_in  — the agent takes physical cash from a customer and sends
            #     e-money back to the customer's wallet: shared cash INCREASES,
            #     provider e-money DECREASES.
            if is_cluster_provider and t < cluster_count:
                # Tight, near-identical cluster within one detection window, from a
                # small pool of synthetic parties.
                amount = cluster_amount
                txn_type = TransactionType.CASH_OUT
                txn_obs = cluster_anchor + timedelta(minutes=t * cluster_step_minutes)
                cash_balance = max(Decimal("0"), cash_balance - amount)
                provider_balances[provider] += amount
            elif scenario_code == ScenarioCode.SCENARIO_A and provider == target_provider:
                # Concentrated cash-out demand drains shared physical cash while
                # this provider's e-money rises — the hidden pressure Scenario A
                # demonstrates (the combined view still looks healthy).
                amount = Decimal(_amount(rng, 2500, 0.1))
                txn_type = TransactionType.CASH_OUT
                cash_balance = max(Decimal("0"), cash_balance - amount)
                provider_balances[provider] += amount
            else:
                # Ordinary alternating retail flow on non-target providers. Under
                # the corrected direction cash-out RAISES provider e-money, so the
                # cash-out leg is the larger, leading one to keep these providers'
                # e-money healthy — only the designated provider (Scenario A) or
                # the amount cluster (Scenario B/C) is meant to be under pressure.
                # The shared cash drawer still nets outflow, matching cash-out
                # demand.
                if t % 2 == 0:
                    amount = Decimal(_amount(rng, 1500))
                    txn_type = TransactionType.CASH_OUT
                    cash_balance = max(Decimal("0"), cash_balance - amount)
                    provider_balances[provider] += amount
                else:
                    amount = Decimal(_amount(rng, 800))
                    txn_type = TransactionType.CASH_IN
                    cash_balance += amount
                    provider_balances[provider] = max(
                        Decimal("0"), provider_balances[provider] - amount
                    )

            ref = f"TXN-{provider.value.upper()}-{seed}-{t:03d}"
            if is_cluster_provider and t < cluster_count:
                # Small pool of parties makes the "few accounts, repeated amounts"
                # pattern explicit while keeping distinct-party evidence meaningful.
                party = _party_ref(rng, provider, t % 2)
            else:
                party = _party_ref(rng, provider, t)
            batch.events.append(
                GeneratedEvent(
                    event_type=FeedEventType.TRANSACTION,
                    provider_code=provider,
                    source_event_ref=ref,
                    source_observed_at=txn_obs,
                    payload={
                        "txn_ref": ref,
                        "party_ref": party,
                        "account_ref": f"ACCT-O1-{provider.value.upper()}",
                        "txn_type": txn_type.value,
                        "status": TransactionStatus.COMPLETED.value,
                        "amount": str(amount),
                        "currency": "BDT",
                        "occurred_at": txn_obs.isoformat(),
                    },
                )
            )
            fingerprint.append(
                {
                    "type": "transaction",
                    "ref": ref,
                    "provider": provider.value,
                    "amount": str(amount),
                    "occurred_at": txn_obs.isoformat(),
                }
            )

        # Closing balance snapshot
        close_obs = event_time(event_idx)
        event_idx += 1
        batch.events.append(
            GeneratedEvent(
                event_type=FeedEventType.PROVIDER_BALANCE,
                provider_code=provider,
                source_event_ref=f"{provider.value.upper()}-BAL-{seed}-1",
                source_observed_at=close_obs,
                payload={
                    "account_ref": f"ACCT-O1-{provider.value.upper()}",
                    "balance": str(provider_balances[provider]),
                    "currency": "BDT",
                    "observed_at": close_obs.isoformat(),
                },
            )
        )
        fingerprint.append(
            {
                "type": "provider_balance",
                "provider": provider.value,
                "balance": str(provider_balances[provider]),
                "observed_at": close_obs.isoformat(),
            }
        )

        # Scenario C: inject a conflicting closing snapshot at the same observed
        # time with a different balance so data quality is classified conflicting.
        if scenario_code == ScenarioCode.SCENARIO_C and is_cluster_provider:
            conflict_balance = provider_balances[provider] + Decimal("5000.00")
            batch.events.append(
                GeneratedEvent(
                    event_type=FeedEventType.PROVIDER_BALANCE,
                    provider_code=provider,
                    source_event_ref=f"{provider.value.upper()}-BAL-{seed}-1C",
                    source_observed_at=close_obs,
                    payload={
                        "account_ref": f"ACCT-O1-{provider.value.upper()}",
                        "balance": str(conflict_balance),
                        "currency": "BDT",
                        "observed_at": close_obs.isoformat(),
                    },
                )
            )
            fingerprint.append(
                {
                    "type": "provider_balance",
                    "provider": provider.value,
                    "balance": str(conflict_balance),
                    "observed_at": close_obs.isoformat(),
                }
            )
        batches.append(batch)

    # Final cash snapshot
    final_obs = event_time(event_idx)
    cash_final = GeneratedBatch(
        provider_code=ProviderCode.BKASH,
        source_batch_ref=f"CASH-{seed}-B{batch_idx}",
        source_generated_at=batch_time(batch_idx),
        is_cash_batch=True,
    )
    cash_final.events.append(
        GeneratedEvent(
            event_type=FeedEventType.CASH_BALANCE,
            provider_code=None,
            source_event_ref=f"CASH-SNAP-{seed}-1",
            source_observed_at=final_obs,
            payload={
                "outlet_id": str(outlet_id),
                "balance": str(_q2(cash_balance)),
                "currency": "BDT",
                "observed_at": final_obs.isoformat(),
            },
        )
    )
    fingerprint.append({"type": "cash_balance", "balance": str(_q2(cash_balance)), "observed_at": final_obs.isoformat()})
    batches.append(cash_final)

    return GenerationResult(outlet_id=outlet_id, batches=batches, semantic_fingerprint=fingerprint)
