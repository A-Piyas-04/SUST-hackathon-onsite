from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories import ingestion as ingestion_repo
from app.member1.schemas.ingestion import CreateIngestionBatchRequest, FeedHealthOut, IngestionBatchOut


async def create_ingestion_batch(session: AsyncSession, payload: CreateIngestionBatchRequest) -> IngestionBatchOut:
    row = await ingestion_repo.create_ingestion_batch(
        session,
        simulation_run_id=payload.simulation_run_id,
        outlet_id=payload.outlet_id,
        provider_id=payload.provider_id,
        source_batch_ref=payload.source_batch_ref,
        source_generated_at=payload.source_generated_at,
        events=[e.model_dump() for e in payload.events],
    )
    return IngestionBatchOut(**row)


def _to_feed_health_out(row: dict) -> FeedHealthOut:
    return FeedHealthOut(
        data_quality_assessment_id=row["data_quality_assessment_id"],
        outlet_id=row["outlet_id"],
        provider_id=row["provider_id"],
        status=row["status"],
        confidence_modifier=float(row["confidence_modifier"]),
        sample_count=row["sample_count"],
        latest_source_at=row.get("latest_source_at"),
        assessed_at=row["assessed_at"],
        summary=row["summary"],
        issues=row.get("issues") or [],
    )


async def get_current_feed_health(session: AsyncSession, outlet_id: UUID, *, provider_id: UUID | None = None) -> list[FeedHealthOut]:
    rows = await ingestion_repo.get_current_feed_health(session, outlet_id, provider_id=provider_id)
    return [_to_feed_health_out(r) for r in rows]


async def get_feed_health_history(session: AsyncSession, outlet_id: UUID, *, provider_id: UUID | None = None, limit: int = 50) -> list[FeedHealthOut]:
    rows = await ingestion_repo.get_feed_health_history(session, outlet_id, provider_id=provider_id, limit=limit)
    return [_to_feed_health_out(r) for r in rows]
