"""Apply active fault injections to generated or manual payloads."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.contracts.v1.enums import FaultType, ProviderCode
from app.services.constants import PROVIDER_IDS
from app.services.synthetic.generator import GeneratedBatch, GeneratedEvent


@dataclass
class ActiveFault:
    fault_injection_id: UUID
    fault_type: str
    outlet_id: UUID
    provider_id: UUID | None
    parameters: dict[str, Any]
    is_enabled: bool


def _provider_for_fault(fault: ActiveFault) -> ProviderCode | None:
    target = fault.parameters.get("target_provider")
    if target:
        return ProviderCode(str(target))
    if fault.provider_id:
        for code, pid in PROVIDER_IDS.items():
            if pid == fault.provider_id:
                return code
    return None


def apply_faults_to_batches(
    batches: list[GeneratedBatch],
    faults: list[ActiveFault],
    *,
    rng_seed: int,
) -> list[GeneratedBatch]:
    result: list[GeneratedBatch] = []
    skip_counts: dict[ProviderCode, int] = {}

    for batch in batches:
        provider = batch.provider_code
        skip = skip_counts.get(provider, 0)

        for fault in faults:
            if not fault.is_enabled:
                continue
            fp = _provider_for_fault(fault)
            if fp and fp != provider and not batch.is_cash_batch:
                continue
            if fault.fault_type == FaultType.MISSING_FEED.value and fp == provider:
                skip_counts[provider] = skip + int(fault.parameters.get("skip_batches", 1))
                skip = skip_counts[provider]

        if skip > 0 and not batch.is_cash_batch:
            skip_counts[provider] = skip - 1
            continue

        events: list[GeneratedEvent] = []
        for event in batch.events:
            mutated = copy.deepcopy(event)
            extras: list[GeneratedEvent] = []
            for fault in faults:
                if not fault.is_enabled:
                    continue
                mutated, extra = _apply_event_fault(mutated, batch, fault, rng_seed)
                extras.extend(extra)
            events.append(mutated)
            events.extend(extras)
        result.append(
            GeneratedBatch(
                provider_code=batch.provider_code,
                source_batch_ref=batch.source_batch_ref,
                source_generated_at=batch.source_generated_at,
                events=events,
                is_cash_batch=batch.is_cash_batch,
            )
        )
    return result


def _apply_event_fault(
    event: GeneratedEvent,
    batch: GeneratedBatch,
    fault: ActiveFault,
    rng_seed: int,
) -> tuple[GeneratedEvent, list[GeneratedEvent]]:
    fp = _provider_for_fault(fault)
    if fp and event.provider_code and event.provider_code != fp:
        return event, []
    if batch.is_cash_batch and fault.fault_type != FaultType.DELAY.value:
        return event, []

    if fault.fault_type == FaultType.DELAY.value:
        delay = int(fault.parameters.get("delay_seconds", 300))
        event.source_observed_at = event.source_observed_at + timedelta(seconds=delay)
        return event, []

    if fault.fault_type == FaultType.MISSING_FIELD.value:
        omit = fault.parameters.get("omit_field", "amount")
        payload = copy.deepcopy(event.payload)
        key_map = {
            "amount": ["trx_amount", "amount", "value"],
            "balance": ["balance", "wallet_balance", "availableBalance", "current_value", "physical_cash"],
        }
        for key in key_map.get(omit, [omit]):
            payload.pop(key, None)
        event.payload = payload
        return event, []

    if fault.fault_type == FaultType.MALFORMED_PAYLOAD.value:
        rate = float(fault.parameters.get("rate", 1.0))
        if (hash(event.source_event_ref) + rng_seed) % 100 < int(rate * 100):
            event.payload = {"__corrupt__": True, "raw": "not-json{"}
        return event, []

    if fault.fault_type == FaultType.CONFLICTING_BALANCE.value:
        # Conflict the closing observation only. Earlier per-transaction
        # snapshots remain trusted, so the dashboard can show a meaningful
        # last-known balance while still marking the feed as conflicting.
        if event.event_type.value == "provider_balance" and event.source_event_ref.endswith("-1"):
            delta = Decimal(str(fault.parameters.get("conflict_delta", "500.00")))
            conflict = copy.deepcopy(event)
            conflict.source_event_ref = event.source_event_ref + "-CONFLICT"
            payload = copy.deepcopy(event.payload)
            for key in ("balance", "wallet_balance", "availableBalance", "current_value"):
                if key in payload:
                    payload[key] = str(Decimal(str(payload[key])) + delta)
            conflict.payload = payload
            return event, [conflict]
        return event, []

    return event, []


def corrupt_payload_for_test(payload: dict[str, Any]) -> dict[str, Any]:
    return {"invalid": json.dumps(payload) + "{"}
