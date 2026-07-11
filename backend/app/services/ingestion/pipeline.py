"""Ingestion batch orchestration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import FeedEventType, NormalizationStatus, ProviderCode, RejectionCode
from app.contracts.v1.ingestion import (
    IngestBatchRequest,
    IngestBatchResponse,
    IngestEventInput,
    IngestEventSummary,
)
from app.contracts.v1.inputs import (
    NormalizedCashBalanceInput,
    NormalizedProviderBalanceInput,
    NormalizedTransactionInput,
)
from app.core.errors import AppError
from app.core.request_context import get_request_id
from app.services.constants import ACCOUNT_IDS, DEFAULT_OUTLET_ID, PROVIDER_IDS
from app.services.ingestion.adapters import to_provider_shape
from app.services.ingestion.fault_effects import ActiveFault
from app.services.ingestion.normalizer import NormalizationError, normalize_event
from app.services.ledger import writer as ledger_writer
from app.services.quality import foundation as quality_foundation
from app.services.synthetic.generator import GeneratedBatch, GeneratedEvent


async def ingest_batch(session: AsyncSession, request: IngestBatchRequest) -> IngestBatchResponse:
    provider_id = PROVIDER_IDS[request.provider_code]
    received_at = datetime.now(timezone.utc)
    trace = {"request_id": get_request_id()}

    existing = await session.execute(
        text(
            """
            SELECT ingestion_batch_id, normalization_status,
                   expected_event_count, received_event_count, rejected_event_count
            FROM ingestion_batches
            WHERE provider_id = :provider_id AND source_batch_ref = :ref
            """
        ),
        {"provider_id": provider_id, "ref": request.source_batch_ref},
    )
    existing_row = existing.mappings().first()
    if existing_row:
        events = await _load_batch_events(session, existing_row["ingestion_batch_id"])
        return IngestBatchResponse(
            ingestion_batch_id=existing_row["ingestion_batch_id"],
            simulation_run_id=request.simulation_run_id,
            outlet_id=request.outlet_id,
            provider_code=request.provider_code,
            source_batch_ref=request.source_batch_ref,
            expected_event_count=existing_row["expected_event_count"],
            received_event_count=existing_row["received_event_count"],
            rejected_event_count=existing_row["rejected_event_count"],
            normalization_status=NormalizationStatus(existing_row["normalization_status"]),
            events=events,
        )

    batch_id = uuid4()
    rejected = 0
    accepted = 0
    summaries: list[IngestEventSummary] = []

    await session.execute(
        text(
            """
            INSERT INTO ingestion_batches (
              ingestion_batch_id, simulation_run_id, outlet_id, provider_id,
              source_batch_ref, source_generated_at, received_at,
              expected_event_count, received_event_count, rejected_event_count,
              normalization_status
            ) VALUES (
              :id, :run_id, :outlet_id, :provider_id, :ref, :gen_at, :received_at,
              :expected, 0, 0, :status
            )
            """
        ),
        {
            "id": batch_id,
            "run_id": request.simulation_run_id,
            "outlet_id": request.outlet_id,
            "provider_id": provider_id,
            "ref": request.source_batch_ref,
            "gen_at": request.source_generated_at,
            "received_at": received_at,
            "expected": len(request.events),
            "status": NormalizationStatus.PENDING.value,
        },
    )

    for event_input in request.events:
        summary = await _process_event(
            session,
            batch_id=batch_id,
            simulation_run_id=request.simulation_run_id,
            outlet_id=request.outlet_id,
            provider_code=request.provider_code,
            event_input=event_input,
            received_at=received_at,
            trace=trace,
        )
        summaries.append(summary)
        if summary.normalization_status == NormalizationStatus.REJECTED:
            rejected += 1
        else:
            accepted += 1

    # Fully rejected batches are REJECTED; anything else (including partial
    # rejection) is NORMALIZED — the status domain has no 'partial' value.
    batch_status = (
        NormalizationStatus.REJECTED
        if rejected == len(request.events)
        else NormalizationStatus.NORMALIZED
    )

    await session.execute(
        text(
            """
            UPDATE ingestion_batches
            SET received_event_count = :received, rejected_event_count = :rejected,
                normalization_status = :status
            WHERE ingestion_batch_id = :id
            """
        ),
        {
            "received": accepted,
            "rejected": rejected,
            "status": batch_status.value,
            "id": batch_id,
        },
    )

    await quality_foundation.record_batch_assessment(
        session,
        simulation_run_id=request.simulation_run_id,
        ingestion_batch_id=batch_id,
        outlet_id=request.outlet_id,
        provider_id=provider_id,
        accepted=accepted,
        rejected=rejected,
        total=len(request.events),
    )

    return IngestBatchResponse(
        ingestion_batch_id=batch_id,
        simulation_run_id=request.simulation_run_id,
        outlet_id=request.outlet_id,
        provider_code=request.provider_code,
        source_batch_ref=request.source_batch_ref,
        expected_event_count=len(request.events),
        received_event_count=accepted,
        rejected_event_count=rejected,
        normalization_status=batch_status,
        events=summaries,
    )


async def ingest_generated_batches(
    session: AsyncSession,
    *,
    simulation_run_id: UUID,
    outlet_id: UUID,
    batches: list[GeneratedBatch],
) -> list[IngestBatchResponse]:
    responses: list[IngestBatchResponse] = []
    for batch in batches:
        events: list[IngestEventInput] = []
        for event in batch.events:
            provider = batch.provider_code
            shaped = to_provider_shape(provider, event.event_type, event.payload)
            events.append(
                IngestEventInput(
                    event_type=event.event_type,
                    source_event_ref=event.source_event_ref,
                    source_observed_at=event.source_observed_at,
                    payload=shaped,
                )
            )
        request = IngestBatchRequest(
            simulation_run_id=simulation_run_id,
            outlet_id=outlet_id,
            provider_code=batch.provider_code,
            source_batch_ref=batch.source_batch_ref,
            source_generated_at=batch.source_generated_at,
            events=events,
        )
        responses.append(await ingest_batch(session, request))
    return responses


async def _process_event(
    session: AsyncSession,
    *,
    batch_id: UUID,
    simulation_run_id: UUID,
    outlet_id: UUID,
    provider_code: ProviderCode,
    event_input: IngestEventInput,
    received_at: datetime,
    trace: dict[str, Any],
) -> IngestEventSummary:
    event_id = uuid4()
    safe_payload = {**event_input.payload, "_trace": trace}

    # Check duplicate within batch
    dup = await session.execute(
        text(
            """
            SELECT ingestion_event_id, normalization_status, rejection_code, rejection_detail
            FROM ingestion_events
            WHERE ingestion_batch_id = :batch_id AND source_event_ref = :ref
            """
        ),
        {"batch_id": batch_id, "ref": event_input.source_event_ref},
    )
    dup_row = dup.mappings().first()
    if dup_row:
        return IngestEventSummary(
            ingestion_event_id=dup_row["ingestion_event_id"],
            source_event_ref=event_input.source_event_ref,
            event_type=event_input.event_type,
            normalization_status=NormalizationStatus(dup_row["normalization_status"]),
            rejection_code=RejectionCode(dup_row["rejection_code"]) if dup_row["rejection_code"] else None,
            rejection_detail=dup_row["rejection_detail"],
        )

    rejection_code: str | None = None
    rejection_detail: str | None = None
    status = NormalizationStatus.NORMALIZED
    normalized: Any = None

    try:
        if isinstance(event_input.payload, dict) and event_input.payload.get("__corrupt__"):
            raise NormalizationError("malformed_payload", "Corrupt synthetic payload")

        if not isinstance(event_input.payload, dict):
            raise NormalizationError("malformed_payload", "Payload must be a JSON object")

        normalized = normalize_event(
            provider_code=provider_code,
            event_type=event_input.event_type,
            payload=event_input.payload,
            outlet_id=outlet_id,
            received_at=received_at,
        )
        if normalized is None:
            status = NormalizationStatus.NORMALIZED
        else:
            _validate_account_scope(normalized, outlet_id)
            normalized.model_validate(normalized.model_dump())
    except (NormalizationError, ValidationError, KeyError, TypeError, json.JSONDecodeError) as exc:
        status = NormalizationStatus.REJECTED
        if isinstance(exc, NormalizationError):
            rejection_code = exc.code
            rejection_detail = exc.detail
        else:
            rejection_code = RejectionCode.MALFORMED_PAYLOAD.value
            rejection_detail = str(exc)

    await session.execute(
        text(
            """
            INSERT INTO ingestion_events (
              ingestion_event_id, ingestion_batch_id, event_type, source_event_ref,
              source_observed_at, received_at, safe_payload,
              normalization_status, rejection_code, rejection_detail
            ) VALUES (
              :id, :batch_id, :event_type, :ref, :observed_at, :received_at,
              CAST(:payload AS jsonb), :status, :rejection_code, :rejection_detail
            )
            """
        ),
        {
            "id": event_id,
            "batch_id": batch_id,
            "event_type": event_input.event_type.value,
            "ref": event_input.source_event_ref,
            "observed_at": event_input.source_observed_at,
            "received_at": received_at,
            "payload": json.dumps(safe_payload),
            "status": status.value,
            "rejection_code": rejection_code,
            "rejection_detail": rejection_detail,
        },
    )

    if status == NormalizationStatus.NORMALIZED and normalized is not None:
        await _write_ledger(session, event_id, simulation_run_id, event_input.event_type, normalized)

    return IngestEventSummary(
        ingestion_event_id=event_id,
        source_event_ref=event_input.source_event_ref,
        event_type=event_input.event_type,
        normalization_status=status,
        rejection_code=RejectionCode(rejection_code) if rejection_code else None,
        rejection_detail=rejection_detail,
    )


async def _write_ledger(
    session: AsyncSession,
    event_id: UUID,
    run_id: UUID,
    event_type: FeedEventType,
    normalized: NormalizedTransactionInput | NormalizedCashBalanceInput | NormalizedProviderBalanceInput,
) -> None:
    if isinstance(normalized, NormalizedTransactionInput):
        await ledger_writer.write_transaction(
            session, ingestion_event_id=event_id, simulation_run_id=run_id, data=normalized
        )
    elif isinstance(normalized, NormalizedCashBalanceInput):
        await ledger_writer.write_cash_snapshot(
            session, ingestion_event_id=event_id, simulation_run_id=run_id, data=normalized
        )
    elif isinstance(normalized, NormalizedProviderBalanceInput):
        await ledger_writer.write_provider_snapshot(
            session, ingestion_event_id=event_id, simulation_run_id=run_id, data=normalized
        )


def _validate_account_scope(
    normalized: NormalizedTransactionInput | NormalizedCashBalanceInput | NormalizedProviderBalanceInput,
    batch_outlet_id: UUID,
) -> None:
    account_ids = set(ACCOUNT_IDS.values())
    if hasattr(normalized, "outlet_provider_account_id"):
        if normalized.outlet_provider_account_id in account_ids and batch_outlet_id != DEFAULT_OUTLET_ID:
            raise NormalizationError(
                "account_mismatch",
                "Provider account does not belong to the requested outlet.",
            )
        if hasattr(normalized, "outlet_id") and normalized.outlet_id != batch_outlet_id:
            raise NormalizationError(
                "account_mismatch",
                "Normalized outlet does not match batch outlet.",
            )
    if isinstance(normalized, NormalizedCashBalanceInput) and normalized.outlet_id != batch_outlet_id:
        raise NormalizationError("account_mismatch", "Cash balance outlet does not match batch outlet.")


async def _load_batch_events(session: AsyncSession, batch_id: UUID) -> list[IngestEventSummary]:
    result = await session.execute(
        text(
            """
            SELECT ingestion_event_id, source_event_ref, event_type,
                   normalization_status, rejection_code, rejection_detail
            FROM ingestion_events WHERE ingestion_batch_id = :batch_id
            ORDER BY created_at
            """
        ),
        {"batch_id": batch_id},
    )
    return [
        IngestEventSummary(
            ingestion_event_id=r["ingestion_event_id"],
            source_event_ref=r["source_event_ref"],
            event_type=FeedEventType(r["event_type"]),
            normalization_status=NormalizationStatus(r["normalization_status"]),
            rejection_code=RejectionCode(r["rejection_code"]) if r["rejection_code"] else None,
            rejection_detail=r["rejection_detail"],
        )
        for r in result.mappings().all()
    ]


async def load_active_faults(session: AsyncSession, run_id: UUID) -> list[ActiveFault]:
    result = await session.execute(
        text(
            """
            SELECT fault_injection_id, fault_type, outlet_id, provider_id,
                   parameters, is_enabled
            FROM fault_injections WHERE simulation_run_id = :run_id
            """
        ),
        {"run_id": run_id},
    )
    return [
        ActiveFault(
            fault_injection_id=r["fault_injection_id"],
            fault_type=r["fault_type"],
            outlet_id=r["outlet_id"],
            provider_id=r["provider_id"],
            parameters=r["parameters"] or {},
            is_enabled=r["is_enabled"],
        )
        for r in result.mappings().all()
    ]
