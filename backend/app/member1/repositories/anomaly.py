from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.member1.repositories.db import fetch_all, fetch_one


async def list_anomaly_flags(
    session: AsyncSession, outlet_id: UUID, *, provider_id: UUID | None = None, limit: int = 50
) -> list[dict]:
    return await fetch_all(
        session,
        """
        SELECT anomaly_flag_id, analytics_run_id, anomaly_rule_id, outlet_id, provider_id, outlet_provider_account_id,
               window_start, window_end, confidence_score, confidence_level, disposition, reason_code,
               evidence_summary, plausible_benign_explanation, suppression_reason
        FROM anomaly_flags
        WHERE outlet_id = :outlet_id AND (:provider_id IS NULL OR provider_id = :provider_id)
        ORDER BY window_end DESC
        LIMIT :limit
        """,
        {"outlet_id": str(outlet_id), "provider_id": str(provider_id) if provider_id else None, "limit": limit},
    )


async def get_anomaly_flag_detail(session: AsyncSession, anomaly_flag_id: UUID) -> dict | None:
    flag = await fetch_one(
        session,
        """
        SELECT anomaly_flag_id, analytics_run_id, anomaly_rule_id, outlet_id, provider_id, outlet_provider_account_id,
               window_start, window_end, confidence_score, confidence_level, disposition, reason_code,
               evidence_summary, plausible_benign_explanation, suppression_reason
        FROM anomaly_flags
        WHERE anomaly_flag_id = :anomaly_flag_id
        """,
        {"anomaly_flag_id": str(anomaly_flag_id)},
    )
    if flag is None:
        return None

    evidence_items = await fetch_all(
        session,
        "SELECT evidence_type, label, value, display_order FROM anomaly_evidence_items WHERE anomaly_flag_id = :id ORDER BY display_order",
        {"id": str(anomaly_flag_id)},
    )
    transactions = await fetch_all(
        session,
        "SELECT transaction_id FROM anomaly_flag_transactions WHERE anomaly_flag_id = :id",
        {"id": str(anomaly_flag_id)},
    )
    flag["evidence_items"] = evidence_items
    flag["transaction_ids"] = [t["transaction_id"] for t in transactions]
    return flag
