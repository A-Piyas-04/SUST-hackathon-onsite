"""Interim pre-Phase-4 data quality assessments from ingestion metadata."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.enums import FeedHealthStatus, ProviderCode, QualityIssueType, Severity
from app.contracts.v1.ledger import DataQualityHistoryResponse, DataQualityItem, DataQualityResponse
from app.contracts.v1.quality import QualityAssessmentInput, QualityIssueInput


ENGINE_VERSION = "phase3-foundation"


async def record_batch_assessment(
    session: AsyncSession,
    *,
    simulation_run_id: UUID,
    ingestion_batch_id: UUID,
    outlet_id: UUID,
    provider_id: UUID,
    accepted: int,
    rejected: int,
    total: int,
) -> UUID:
    if rejected == total and total > 0:
        status = FeedHealthStatus.MISSING if accepted == 0 else FeedHealthStatus.CONFLICTING
        modifier = 0.3
    elif rejected > 0:
        status = FeedHealthStatus.STALE
        modifier = 0.6
    else:
        status = FeedHealthStatus.FRESH
        modifier = 1.0

    assessment_id = uuid4()
    summary = (
        f"Pre-Phase-4 foundation assessment: {accepted}/{total} events accepted, "
        f"{rejected} rejected."
    )
    await session.execute(
        text(
            """
            INSERT INTO data_quality_assessments (
              data_quality_assessment_id, simulation_run_id, ingestion_batch_id,
              outlet_id, provider_id, status, confidence_modifier, sample_count,
              latest_source_at, assessed_at, engine_version, summary
            ) VALUES (
              :id, :run_id, :batch_id, :outlet_id, :provider_id, :status,
              :modifier, :sample_count, :latest_source_at, :assessed_at,
              :engine_version, :summary
            )
            """
        ),
        {
            "id": assessment_id,
            "run_id": simulation_run_id,
            "batch_id": ingestion_batch_id,
            "outlet_id": outlet_id,
            "provider_id": provider_id,
            "status": status.value,
            "modifier": modifier,
            "sample_count": total,
            "latest_source_at": datetime.now(timezone.utc),
            "assessed_at": datetime.now(timezone.utc),
            "engine_version": ENGINE_VERSION,
            "summary": summary,
        },
    )

    if rejected > 0:
        await session.execute(
            text(
                """
                INSERT INTO data_quality_issues (
                  data_quality_issue_id, data_quality_assessment_id,
                  issue_type, severity, field_name, evidence
                ) VALUES (
                  gen_random_uuid(), :assessment_id, :issue_type, :severity,
                  :field_name, CAST(:evidence AS jsonb)
                )
                """
            ),
            {
                "assessment_id": assessment_id,
                "issue_type": QualityIssueType.MALFORMED_PAYLOAD.value,
                "severity": Severity.MEDIUM.value,
                "field_name": None,
                "evidence": json.dumps({"rejected_count": rejected}),
            },
        )

    return assessment_id


async def get_current_data_quality(session: AsyncSession, outlet_id: UUID) -> DataQualityResponse:
    result = await session.execute(
        text(
            """
            SELECT fh.*, p.code AS provider_code
            FROM v_current_feed_health fh
            JOIN providers p ON p.provider_id = fh.provider_id
            WHERE fh.outlet_id = :outlet_id
            ORDER BY p.code
            """
        ),
        {"outlet_id": outlet_id},
    )
    items: list[DataQualityItem] = []
    for r in result.mappings().all():
        assessment = QualityAssessmentInput(
            simulation_run_id=UUID("00000000-0000-0000-0000-000000000000"),
            outlet_id=outlet_id,
            provider_id=r["provider_id"],
            status=FeedHealthStatus(r["status"]),
            confidence_modifier=float(r["confidence_modifier"]),
            sample_count=int(r["sample_count"]),
            latest_source_at=r["latest_source_at"],
            assessed_at=r["assessed_at"],
            engine_version=r["engine_version"] or ENGINE_VERSION,
            summary=r["summary"] or "",
        )
        items.append(
            DataQualityItem(provider=ProviderCode(r["provider_code"]), assessment=assessment)
        )

    if not items:
        # Return placeholder per-provider fresh status when no assessments yet
        provs = await session.execute(
            text(
                """
                SELECT p.provider_id, p.code
                FROM outlet_provider_accounts opa
                JOIN providers p ON p.provider_id = opa.provider_id
                WHERE opa.outlet_id = :outlet_id AND opa.is_active
                """
            ),
            {"outlet_id": outlet_id},
        )
        now = datetime.now(timezone.utc)
        for r in provs.mappings().all():
            items.append(
                DataQualityItem(
                    provider=ProviderCode(r["code"]),
                    assessment=QualityAssessmentInput(
                        simulation_run_id=UUID("00000000-0000-0000-0000-000000000000"),
                        outlet_id=outlet_id,
                        provider_id=r["provider_id"],
                        status=FeedHealthStatus.MISSING,
                        confidence_modifier=0.0,
                        sample_count=0,
                        assessed_at=now,
                        engine_version=ENGINE_VERSION,
                        summary="No ingestion assessments recorded yet.",
                    ),
                )
            )

    return DataQualityResponse(outlet_id=outlet_id, providers=items)


async def get_data_quality_history(session: AsyncSession, outlet_id: UUID) -> DataQualityHistoryResponse:
    result = await session.execute(
        text(
            """
            SELECT dqa.*, p.code AS provider_code
            FROM data_quality_assessments dqa
            JOIN providers p ON p.provider_id = dqa.provider_id
            WHERE dqa.outlet_id = :outlet_id
            ORDER BY dqa.assessed_at DESC
            LIMIT 50
            """
        ),
        {"outlet_id": outlet_id},
    )
    assessments: list[DataQualityItem] = []
    for r in result.mappings().all():
        assessments.append(
            DataQualityItem(
                provider=ProviderCode(r["provider_code"]),
                assessment=QualityAssessmentInput(
                    data_quality_assessment_id=r["data_quality_assessment_id"],
                    simulation_run_id=r["simulation_run_id"],
                    ingestion_batch_id=r["ingestion_batch_id"],
                    outlet_id=r["outlet_id"],
                    provider_id=r["provider_id"],
                    status=FeedHealthStatus(r["status"]),
                    confidence_modifier=float(r["confidence_modifier"]),
                    sample_count=int(r["sample_count"]),
                    latest_source_at=r["latest_source_at"],
                    assessed_at=r["assessed_at"],
                    engine_version=r["engine_version"],
                    summary=r["summary"] or "",
                ),
            )
        )
    return DataQualityHistoryResponse(outlet_id=outlet_id, assessments=assessments)
