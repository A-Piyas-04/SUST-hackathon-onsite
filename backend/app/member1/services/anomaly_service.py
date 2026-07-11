from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories import anomaly as anomaly_repo
from app.member1.schemas.anomaly import AnomalyEvidenceItemOut, AnomalyFlagDetailOut, AnomalyFlagOut


def _to_out(row: dict) -> AnomalyFlagOut:
    return AnomalyFlagOut(
        anomaly_flag_id=row["anomaly_flag_id"],
        analytics_run_id=row["analytics_run_id"],
        anomaly_rule_id=row["anomaly_rule_id"],
        outlet_id=row["outlet_id"],
        provider_id=row["provider_id"],
        outlet_provider_account_id=row["outlet_provider_account_id"],
        window_start=row["window_start"],
        window_end=row["window_end"],
        confidence_score=float(row["confidence_score"]),
        confidence_level=row["confidence_level"],
        disposition=row["disposition"],
        reason_code=row.get("reason_code"),
        evidence_summary=row["evidence_summary"],
        plausible_benign_explanation=row.get("plausible_benign_explanation"),
        suppression_reason=row.get("suppression_reason"),
    )


async def list_anomaly_flags(session: AsyncSession, outlet_id: UUID, *, provider_id: UUID | None = None, limit: int = 50) -> list[AnomalyFlagOut]:
    rows = await anomaly_repo.list_anomaly_flags(session, outlet_id, provider_id=provider_id, limit=limit)
    return [_to_out(r) for r in rows]


async def get_anomaly_flag_detail(session: AsyncSession, anomaly_flag_id: UUID) -> AnomalyFlagDetailOut | None:
    row = await anomaly_repo.get_anomaly_flag_detail(session, anomaly_flag_id)
    if row is None:
        return None
    base = _to_out(row)
    return AnomalyFlagDetailOut(
        **base.model_dump(),
        evidence_items=[AnomalyEvidenceItemOut(**e) for e in row["evidence_items"]],
        transaction_ids=row["transaction_ids"],
    )
