"""Ingestion batch/event persistence.

# TODO(owner=Member1, Phase 3): wire normalized ingestion_events into
# transactions/cash_balance_snapshots/provider_balance_snapshots (the
# Provider Feed Ingestion & Normalization module). Phase 1 only proves the
# batch/event shape persists correctly and that rejected events are flagged.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories.db import fetch_all, fetch_one


def _classify_event(event: dict[str, Any]) -> tuple[str, str | None, str | None]:
    """Minimal normalization rule for Phase 1: an event with a populated
    payload and an observed timestamp is normalized; anything else is
    rejected with a reason. Real normalization rules land in Phase 3."""
    if not event.get("safe_payload"):
        return "rejected", "missing_field", "safe_payload was empty"
    if not event.get("source_observed_at"):
        return "rejected", "missing_field", "source_observed_at was missing"
    return "normalized", None, None


async def create_ingestion_batch(
    session: AsyncSession,
    *,
    simulation_run_id: UUID,
    outlet_id: UUID,
    provider_id: UUID,
    source_batch_ref: str,
    source_generated_at: datetime | None,
    events: list[dict[str, Any]],
) -> dict:
    classified = [(_classify_event(e), e) for e in events]
    rejected_count = sum(1 for (status, _, _), _ in classified if status == "rejected")
    normalization_status = "rejected" if rejected_count == len(events) and events else ("normalized" if events else "pending")

    batch = await fetch_one(
        session,
        """
        INSERT INTO ingestion_batches
            (simulation_run_id, outlet_id, provider_id, source_batch_ref, source_generated_at,
             expected_event_count, received_event_count, rejected_event_count, normalization_status)
        VALUES (:simulation_run_id, :outlet_id, :provider_id, :source_batch_ref, :source_generated_at,
                :expected_event_count, :received_event_count, :rejected_event_count, :normalization_status)
        RETURNING ingestion_batch_id, simulation_run_id, outlet_id, provider_id, source_batch_ref,
                  received_at, expected_event_count, received_event_count, rejected_event_count, normalization_status
        """,
        {
            "simulation_run_id": str(simulation_run_id),
            "outlet_id": str(outlet_id),
            "provider_id": str(provider_id),
            "source_batch_ref": source_batch_ref,
            "source_generated_at": source_generated_at,
            "expected_event_count": len(events),
            "received_event_count": len(events),
            "rejected_event_count": rejected_count,
            "normalization_status": normalization_status,
        },
    )
    assert batch is not None
    batch_id = batch["ingestion_batch_id"]

    for (status, rejection_code, rejection_detail), event in classified:
        await fetch_one(
            session,
            """
            INSERT INTO ingestion_events
                (ingestion_batch_id, event_type, source_event_ref, source_observed_at, safe_payload,
                 normalization_status, rejection_code, rejection_detail)
            VALUES (:ingestion_batch_id, :event_type, :source_event_ref, :source_observed_at, :safe_payload,
                    :normalization_status, :rejection_code, :rejection_detail)
            RETURNING ingestion_event_id
            """,
            {
                "ingestion_batch_id": str(batch_id),
                "event_type": event["event_type"],
                "source_event_ref": event["source_event_ref"],
                "source_observed_at": event.get("source_observed_at"),
                "safe_payload": json.dumps(event.get("safe_payload") or {}),
                "normalization_status": status,
                "rejection_code": rejection_code,
                "rejection_detail": rejection_detail,
            },
        )

    return batch


async def get_current_feed_health(session: AsyncSession, outlet_id: UUID, *, provider_id: UUID | None = None) -> list[dict]:
    return await fetch_all(
        session,
        """
        SELECT data_quality_assessment_id, outlet_id, provider_id, status, confidence_modifier,
               sample_count, latest_source_at, assessed_at, summary, issues
        FROM v_current_feed_health
        WHERE outlet_id = :outlet_id AND (:provider_id IS NULL OR provider_id = :provider_id)
        ORDER BY assessed_at DESC
        """,
        {"outlet_id": str(outlet_id), "provider_id": str(provider_id) if provider_id else None},
    )


async def get_feed_health_history(
    session: AsyncSession, outlet_id: UUID, *, provider_id: UUID | None = None, limit: int = 50
) -> list[dict]:
    return await fetch_all(
        session,
        """
        SELECT data_quality_assessment_id, outlet_id, provider_id, status, confidence_modifier,
               sample_count, latest_source_at, assessed_at, summary,
               '[]'::jsonb AS issues
        FROM data_quality_assessments
        WHERE outlet_id = :outlet_id AND (:provider_id IS NULL OR provider_id = :provider_id)
        ORDER BY assessed_at DESC
        LIMIT :limit
        """,
        {"outlet_id": str(outlet_id), "provider_id": str(provider_id) if provider_id else None, "limit": limit},
    )
