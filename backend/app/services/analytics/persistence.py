"""Append-only persistence for analytical artifacts.

Writes analytics runs, quality assessments/issues, liquidity projections/signals
and their quality links, and anomaly flags/evidence/transaction links. Every
insert preserves run-level lineage and immutable, evidence-backed references with
decimal/timestamp precision intact.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.anomaly import AnomalyFlagOutput
from app.contracts.v1.enums import AnalyticsEngine
from app.contracts.v1.liquidity import LiquidityProjectionOutput
from app.contracts.v1.quality import QualityAssessmentInput


async def create_analytics_run(
    session: AsyncSession,
    *,
    simulation_run_id: UUID,
    engine: AnalyticsEngine,
    engine_version: str,
    configuration: dict,
    input_window_start: datetime,
    input_window_end: datetime,
) -> UUID:
    run_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO analytics_runs (
              analytics_run_id, simulation_run_id, engine, engine_version,
              configuration, input_window_start, input_window_end, status, started_at
            ) VALUES (
              :id, :sim_run_id, :engine, :engine_version, CAST(:config AS jsonb),
              :start, :end, 'running', :started_at
            )
            """
        ),
        {
            "id": run_id,
            "sim_run_id": simulation_run_id,
            "engine": engine.value,
            "engine_version": engine_version,
            "config": json.dumps(configuration),
            "start": input_window_start,
            "end": input_window_end,
            "started_at": datetime.now(timezone.utc),
        },
    )
    return run_id


async def complete_analytics_run(
    session: AsyncSession,
    analytics_run_id: UUID,
    *,
    status: str = "completed",
    error_summary: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            UPDATE analytics_runs
            SET status = :status, completed_at = :completed_at, error_summary = :err
            WHERE analytics_run_id = :id
            """
        ),
        {
            "status": status,
            "completed_at": datetime.now(timezone.utc),
            "err": error_summary,
            "id": analytics_run_id,
        },
    )


async def insert_quality_assessment(
    session: AsyncSession, assessment: QualityAssessmentInput
) -> UUID:
    assessment_id = assessment.data_quality_assessment_id or uuid4()
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
            "run_id": assessment.simulation_run_id,
            "batch_id": assessment.ingestion_batch_id,
            "outlet_id": assessment.outlet_id,
            "provider_id": assessment.provider_id,
            "status": assessment.status.value,
            "modifier": Decimal(str(assessment.confidence_modifier)),
            "sample_count": assessment.sample_count,
            "latest_source_at": assessment.latest_source_at,
            "assessed_at": assessment.assessed_at,
            "engine_version": assessment.engine_version,
            "summary": assessment.summary,
        },
    )
    for issue in assessment.issues:
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
                "issue_type": issue.issue_type.value,
                "severity": issue.severity.value,
                "field_name": issue.field_name,
                "evidence": json.dumps(issue.evidence or {}),
            },
        )
    return assessment_id


async def insert_liquidity_projection(
    session: AsyncSession,
    projection: LiquidityProjectionOutput,
    *,
    analytics_run_id: UUID,
    primary_assessment_id: UUID | None,
    linked_assessment_ids: tuple[UUID, ...] = (),
) -> UUID:
    projection_id = projection.liquidity_projection_id or uuid4()
    await session.execute(
        text(
            """
            INSERT INTO liquidity_projections (
              liquidity_projection_id, analytics_run_id, outlet_id, reserve_type,
              outlet_provider_account_id, provider_id, primary_data_quality_assessment_id,
              as_of_at, current_balance, burn_rate_per_hour, projected_shortage_at,
              lower_bound_at, upper_bound_at, confidence_score, confidence_level,
              sample_count, is_actionable, non_actionable_reason
            ) VALUES (
              :id, :run_id, :outlet_id, :reserve_type, :account_id, :provider_id,
              :primary_dqa, :as_of, :current_balance, :burn_rate, :shortage_at,
              :lower, :upper, :confidence_score, :confidence_level, :sample_count,
              :is_actionable, :non_actionable_reason
            )
            """
        ),
        {
            "id": projection_id,
            "run_id": analytics_run_id,
            "outlet_id": projection.outlet_id,
            "reserve_type": projection.reserve_type.value,
            "account_id": projection.outlet_provider_account_id,
            "provider_id": projection.provider_id,
            "primary_dqa": primary_assessment_id,
            "as_of": projection.as_of_at,
            "current_balance": projection.current_balance,
            "burn_rate": projection.burn_rate_per_hour,
            "shortage_at": projection.projected_shortage_at,
            "lower": projection.lower_bound_at,
            "upper": projection.upper_bound_at,
            "confidence_score": projection.confidence_score,
            "confidence_level": projection.confidence_level.value,
            "sample_count": projection.sample_count,
            "is_actionable": projection.is_actionable,
            "non_actionable_reason": projection.non_actionable_reason,
        },
    )
    for signal in projection.signals:
        await session.execute(
            text(
                """
                INSERT INTO liquidity_signals (
                  liquidity_signal_id, liquidity_projection_id, signal_code, label,
                  numeric_value, unit, direction, details, display_order
                ) VALUES (
                  gen_random_uuid(), :projection_id, :signal_code, :label,
                  :numeric_value, :unit, :direction, CAST(:details AS jsonb), :display_order
                )
                """
            ),
            {
                "projection_id": projection_id,
                "signal_code": signal.signal_code,
                "label": signal.label,
                "numeric_value": signal.numeric_value,
                "unit": signal.unit,
                "direction": signal.direction or "reduces_confidence",
                "details": json.dumps(signal.details or {}),
                "display_order": signal.display_order,
            },
        )
    linked = set(linked_assessment_ids)
    if primary_assessment_id is not None:
        linked.add(primary_assessment_id)
    for assessment_id in linked:
        await session.execute(
            text(
                """
                INSERT INTO liquidity_projection_quality_assessments (
                  liquidity_projection_id, data_quality_assessment_id
                ) VALUES (:projection_id, :assessment_id)
                ON CONFLICT DO NOTHING
                """
            ),
            {"projection_id": projection_id, "assessment_id": assessment_id},
        )
    return projection_id


async def insert_anomaly_flag(
    session: AsyncSession,
    flag: AnomalyFlagOutput,
    *,
    analytics_run_id: UUID,
    anomaly_rule_id: UUID,
) -> UUID:
    flag_id = flag.anomaly_flag_id or uuid4()
    await session.execute(
        text(
            """
            INSERT INTO anomaly_flags (
              anomaly_flag_id, analytics_run_id, anomaly_rule_id, outlet_id,
              provider_id, outlet_provider_account_id, data_quality_assessment_id,
              window_start, window_end, confidence_score, confidence_level,
              disposition, reason_code, evidence_summary,
              plausible_benign_explanation, suppression_reason
            ) VALUES (
              :id, :run_id, :rule_id, :outlet_id, :provider_id, :account_id,
              :dqa_id, :window_start, :window_end, :confidence_score,
              :confidence_level, :disposition, :reason_code, :evidence_summary,
              :benign, :suppression_reason
            )
            """
        ),
        {
            "id": flag_id,
            "run_id": analytics_run_id,
            "rule_id": anomaly_rule_id,
            "outlet_id": flag.outlet_id,
            "provider_id": flag.provider_id,
            "account_id": flag.outlet_provider_account_id,
            "dqa_id": flag.data_quality_assessment_id,
            "window_start": flag.window_start,
            "window_end": flag.window_end,
            "confidence_score": flag.confidence_score,
            "confidence_level": flag.confidence_level.value,
            "disposition": flag.disposition.value,
            "reason_code": flag.reason_code,
            "evidence_summary": flag.evidence_summary,
            "benign": flag.plausible_benign_explanation,
            "suppression_reason": flag.suppression_reason,
        },
    )
    for item in flag.evidence_items:
        await session.execute(
            text(
                """
                INSERT INTO anomaly_evidence_items (
                  anomaly_evidence_item_id, anomaly_flag_id, evidence_type, label,
                  value, display_order
                ) VALUES (
                  gen_random_uuid(), :flag_id, :evidence_type, :label,
                  CAST(:value AS jsonb), :display_order
                )
                """
            ),
            {
                "flag_id": flag_id,
                "evidence_type": item.evidence_type,
                "label": item.label,
                "value": json.dumps(item.value),
                "display_order": item.display_order,
            },
        )
    for txn_id in flag.transaction_ids:
        await session.execute(
            text(
                """
                INSERT INTO anomaly_flag_transactions (anomaly_flag_id, transaction_id)
                VALUES (:flag_id, :txn_id)
                ON CONFLICT DO NOTHING
                """
            ),
            {"flag_id": flag_id, "txn_id": txn_id},
        )
    return flag_id
