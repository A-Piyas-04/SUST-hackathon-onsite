"""Simulation run artifact reset — append-only ledger safe."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def delete_run_artifacts(session: AsyncSession, run_id: UUID) -> None:
    """Remove non-append-only ingestion metadata for a simulation run.

    Ledger tables (transactions, balance snapshots) and data_quality_assessments
    are append-only and cannot be deleted per schema migration 002/003.
    """
    await session.execute(
        text(
            """
            DELETE FROM ingestion_events
            WHERE ingestion_batch_id IN (
              SELECT ingestion_batch_id FROM ingestion_batches
              WHERE simulation_run_id = :run_id
            )
            """
        ),
        {"run_id": run_id},
    )
    await session.execute(
        text("DELETE FROM ingestion_batches WHERE simulation_run_id = :run_id"),
        {"run_id": run_id},
    )
