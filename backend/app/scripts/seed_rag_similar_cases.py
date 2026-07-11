#!/usr/bin/env python3
"""Idempotent seed for RAG similar-case demo corpus (CASE-SEED-RAG-*).

Inserts provider-scoped resolved cases with distinctive scenario narratives and
indexes embeddings with corpus_origin=seeded_demo. Invoked from run_migrations seed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg2
import psycopg2.extras

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.coordination.similar_cases import EMBEDDING_DIM, embed_text  # noqa: E402

OUTLET = "0b000000-0000-0000-0000-000000000001"
BKASH = "11111111-1111-1111-1111-111111111111"
NAGAD = "22222222-2222-2222-2222-222222222222"
ROCKET = "33333333-3333-3333-3333-333333333333"
OPA = {
    BKASH: "e1000000-0000-0000-0000-000000000001",
    NAGAD: "e2000000-0000-0000-0000-000000000001",
    ROCKET: "e3000000-0000-0000-0000-000000000001",
}
ROUTING = {
    BKASH: "40000000-0000-0000-0000-000000000002",
    NAGAD: "40000000-0000-0000-0000-000000000003",
    ROCKET: "40000000-0000-0000-0000-000000000004",
}
OPS = {
    BKASH: "d0000000-0000-0000-0000-000000000b01",
    NAGAD: "d0000000-0000-0000-0000-000000000b02",
    ROCKET: "d0000000-0000-0000-0000-000000000b03",
}
SCENARIO_D = "5c000000-0000-0000-0000-00000000000d"
ANOMALY_RULE = "a9000000-0000-0000-0000-000000000001"
EXPL_TEMPLATE = "7e000000-0000-0000-0000-0000000000e3"

SIM_RUN = "f0000000-0000-0000-0000-000000000001"
ANALYTICS_RUN = "f0000000-0000-0000-0000-000000000010"
DQA = {
    BKASH: "f0000000-0000-0000-0000-000000000020",
    NAGAD: "f0000000-0000-0000-0000-000000000021",
    ROCKET: "f0000000-0000-0000-0000-000000000022",
}

SEED_CASES = [
    {
        "suffix": "BKASH-001",
        "provider": BKASH,
        "provider_label": "bKash",
        "scenario": "eid_demand",
        "evidence_summary": (
            "Velocity spike detected: 12 bKash cash-out transactions at Outlet 001 "
            "within 10 minutes, exceeding the outlet same-hour baseline. Pattern may "
            "reflect pre-Eid market demand."
        ),
        "resolution_summary": (
            "Coordinated with outlet agent; confirmed pre-Eid cash-out surge from regular "
            "customers. No further action required."
        ),
        "note_text": (
            "Called outlet; agent reports festival shopping demand. Matches prior Eid patterns."
        ),
        "review_summary": (
            "Benign operational spike consistent with seasonal pre-Eid demand; marked false "
            "positive for review purposes."
        ),
        "disposition": "benign_operational",
        "was_false_positive": True,
    },
    {
        "suffix": "BKASH-002",
        "provider": BKASH,
        "provider_label": "bKash",
        "scenario": "salary_day",
        "evidence_summary": (
            "Near-identical repeated bKash cash-out amounts (5,000 BDT) from 6 distinct "
            "parties within 15 minutes at Outlet 001."
        ),
        "resolution_summary": (
            "Verified salary-day disbursement schedule with employer partners. Repeated round "
            "amounts are expected."
        ),
        "note_text": "Employer salary batch confirmed for month-end. Standard disbursement pattern.",
        "review_summary": (
            "Salary-day repeated amounts dismissed as normal operational pattern."
        ),
        "disposition": "benign_operational",
        "was_false_positive": True,
    },
    {
        "suffix": "BKASH-003",
        "provider": BKASH,
        "provider_label": "bKash",
        "scenario": "unusual_cluster",
        "evidence_summary": (
            "Cluster of 8 near-identical bKash cash-out transactions from 3 accounts within "
            "20 minutes at Outlet 001, with velocity above baseline."
        ),
        "resolution_summary": (
            "Escalated review completed; unusual concentration confirmed and outlet monitoring "
            "increased."
        ),
        "note_text": (
            "Risk analyst reviewed account diversity; pattern remains review-worthy."
        ),
        "review_summary": (
            "Confirmed unusual activity requiring operational follow-up; not determined to be fraud."
        ),
        "disposition": "confirmed_unusual",
        "was_false_positive": False,
    },
    {
        "suffix": "NAGAD-001",
        "provider": NAGAD,
        "provider_label": "Nagad",
        "scenario": "eid_demand",
        "evidence_summary": (
            "Velocity spike detected: 12 Nagad cash-out transactions at Outlet 001 within "
            "10 minutes, exceeding the outlet same-hour baseline. Pattern may reflect pre-Eid "
            "market demand."
        ),
        "resolution_summary": (
            "Coordinated with outlet agent; confirmed pre-Eid cash-out surge from regular "
            "customers. No further action required."
        ),
        "note_text": (
            "Called outlet; agent reports festival shopping demand. Matches prior Eid patterns."
        ),
        "review_summary": (
            "Benign operational spike consistent with seasonal pre-Eid demand; marked false "
            "positive for review purposes."
        ),
        "disposition": "benign_operational",
        "was_false_positive": True,
    },
    {
        "suffix": "NAGAD-002",
        "provider": NAGAD,
        "provider_label": "Nagad",
        "scenario": "salary_day",
        "evidence_summary": (
            "Near-identical repeated Nagad cash-out amounts (5,000 BDT) from 6 distinct "
            "parties within 15 minutes at Outlet 001."
        ),
        "resolution_summary": (
            "Verified salary-day disbursement schedule with employer partners. Repeated round "
            "amounts are expected."
        ),
        "note_text": "Employer salary batch confirmed for month-end. Standard disbursement pattern.",
        "review_summary": (
            "Salary-day repeated amounts dismissed as normal operational pattern."
        ),
        "disposition": "benign_operational",
        "was_false_positive": True,
    },
    {
        "suffix": "NAGAD-003",
        "provider": NAGAD,
        "provider_label": "Nagad",
        "scenario": "unusual_cluster",
        "evidence_summary": (
            "Cluster of 8 near-identical Nagad cash-out transactions from 3 accounts within "
            "20 minutes at Outlet 001, with velocity above baseline."
        ),
        "resolution_summary": (
            "Escalated review completed; unusual concentration confirmed and outlet monitoring "
            "increased."
        ),
        "note_text": (
            "Risk analyst reviewed account diversity; pattern remains review-worthy."
        ),
        "review_summary": (
            "Confirmed unusual activity requiring operational follow-up; not determined to be fraud."
        ),
        "disposition": "confirmed_unusual",
        "was_false_positive": False,
    },
    {
        "suffix": "ROCKET-001",
        "provider": ROCKET,
        "provider_label": "Rocket",
        "scenario": "eid_demand",
        "evidence_summary": (
            "Velocity spike detected: 12 Rocket cash-out transactions at Outlet 001 within "
            "10 minutes, exceeding the outlet same-hour baseline. Pattern may reflect pre-Eid "
            "market demand."
        ),
        "resolution_summary": (
            "Coordinated with outlet agent; confirmed pre-Eid cash-out surge from regular "
            "customers. No further action required."
        ),
        "note_text": (
            "Called outlet; agent reports festival shopping demand. Matches prior Eid patterns."
        ),
        "review_summary": (
            "Benign operational spike consistent with seasonal pre-Eid demand; marked false "
            "positive for review purposes."
        ),
        "disposition": "benign_operational",
        "was_false_positive": True,
    },
    {
        "suffix": "ROCKET-002",
        "provider": ROCKET,
        "provider_label": "Rocket",
        "scenario": "salary_day",
        "evidence_summary": (
            "Near-identical repeated Rocket cash-out amounts (5,000 BDT) from 6 distinct "
            "parties within 15 minutes at Outlet 001."
        ),
        "resolution_summary": (
            "Verified salary-day disbursement schedule with employer partners. Repeated round "
            "amounts are expected."
        ),
        "note_text": "Employer salary batch confirmed for month-end. Standard disbursement pattern.",
        "review_summary": (
            "Salary-day repeated amounts dismissed as normal operational pattern."
        ),
        "disposition": "benign_operational",
        "was_false_positive": True,
    },
    {
        "suffix": "ROCKET-003",
        "provider": ROCKET,
        "provider_label": "Rocket",
        "scenario": "unusual_cluster",
        "evidence_summary": (
            "Cluster of 8 near-identical Rocket cash-out transactions from 3 accounts within "
            "20 minutes at Outlet 001, with velocity above baseline."
        ),
        "resolution_summary": (
            "Escalated review completed; unusual concentration confirmed and outlet monitoring "
            "increased."
        ),
        "note_text": (
            "Risk analyst reviewed account diversity; pattern remains review-worthy."
        ),
        "review_summary": (
            "Confirmed unusual activity requiring operational follow-up; not determined to be fraud."
        ),
        "disposition": "confirmed_unusual",
        "was_false_positive": False,
    },
]


def _ids_for_index(idx: int) -> dict[str, str]:
    tail = f"{idx:012x}"
    return {
        "alert": f"f1000000-0000-4000-8000-{tail}",
        "flag": f"f2000000-0000-4000-8000-{tail}",
        "case": f"f3000000-0000-4000-8000-{tail}",
        "note": f"f4000000-0000-4000-8000-{tail}",
        "review": f"f5000000-0000-4000-8000-{tail}",
    }


def _dsn() -> str:
    for key in ("DIRECT_DATABASE_URL", "TEST_DATABASE_URL", "DATABASE_URL"):
        val = os.environ.get(key)
        if val:
            return val.replace("+asyncpg", "").replace("+psycopg2", "")
    raise SystemExit("No database URL configured for RAG seed.")


def _join_parts(parts: list[str]) -> str:
    return "\n\n".join(p.strip() for p in parts if p and p.strip())


def _ensure_infrastructure(cur) -> None:
    cur.execute(
        """
        INSERT INTO simulation_runs
          (simulation_run_id, scenario_id, seed, config_snapshot, status, completed_at)
        VALUES (%s, %s, 20999001, '{"dataset":"rag_seed"}'::jsonb, 'completed', now())
        ON CONFLICT (simulation_run_id) DO NOTHING
        """,
        (SIM_RUN, SCENARIO_D),
    )
    cur.execute(
        """
        INSERT INTO analytics_runs
          (analytics_run_id, simulation_run_id, engine, engine_version,
           input_window_start, input_window_end, status, completed_at)
        VALUES (%s, %s, 'anomaly', 'rag-seed-v1', '2026-07-01', '2026-07-05', 'completed', now())
        ON CONFLICT (analytics_run_id) DO NOTHING
        """,
        (ANALYTICS_RUN, SIM_RUN),
    )
    for provider, dqa_id in DQA.items():
        cur.execute(
            """
            INSERT INTO data_quality_assessments
              (data_quality_assessment_id, simulation_run_id, outlet_id, provider_id,
               status, confidence_modifier, sample_count, assessed_at, engine_version)
            VALUES (%s, %s, %s, %s, 'fresh', 1.0, 50, '2026-07-05', 'rag-seed-v1')
            ON CONFLICT (data_quality_assessment_id) DO NOTHING
            """,
            (dqa_id, SIM_RUN, OUTLET, provider),
        )


def _seed_one_case(cur, idx: int, spec: dict) -> None:
    ids = _ids_for_index(idx)
    provider = spec["provider"]
    suffix = spec["suffix"]
    case_number = f"CASE-SEED-RAG-{suffix}"
    dedup_key = f"rag-seed-{suffix.lower()}"
    payload = {
        "evidence_summary": spec["evidence_summary"],
        "recommended_next_step": "Review evidence and coordinate through approved provider-scoped procedures.",
        "confidence": "0.8500",
        "confidence_level": "high",
        "evidence": [],
    }

    cur.execute(
        """
        INSERT INTO anomaly_flags
          (anomaly_flag_id, analytics_run_id, anomaly_rule_id, outlet_id, provider_id,
           outlet_provider_account_id, data_quality_assessment_id, window_start, window_end,
           confidence_score, confidence_level, disposition, reason_code, evidence_summary,
           plausible_benign_explanation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, '2026-07-05', '2026-07-05', 0.85, 'high',
                'requires_review', 'rag_seed', %s, 'May reflect normal event-driven demand.')
        ON CONFLICT (anomaly_flag_id) DO NOTHING
        """,
        (
            ids["flag"],
            ANALYTICS_RUN,
            ANOMALY_RULE,
            OUTLET,
            provider,
            OPA[provider],
            DQA[provider],
            spec["evidence_summary"],
        ),
    )
    cur.execute(
        """
        INSERT INTO alerts
          (alert_id, simulation_run_id, outlet_id, provider_id, alert_type, severity,
           deduplication_key, title_key, structured_payload, requires_case, detected_at)
        VALUES (%s, %s, %s, %s, 'anomaly', 'medium', %s, 'anomaly_velocity_spike',
                %s::jsonb, true, '2026-07-05')
        ON CONFLICT (alert_id) DO NOTHING
        """,
        (ids["alert"], SIM_RUN, OUTLET, provider, dedup_key, psycopg2.extras.Json(payload)),
    )
    cur.execute(
        """
        INSERT INTO alert_anomaly_flags (alert_id, anomaly_flag_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        (ids["alert"], ids["flag"]),
    )
    cur.execute(
        """
        INSERT INTO alert_explanations
          (alert_explanation_id, alert_id, explanation_template_id, locale,
           situation_text, evidence_text, uncertainty_text, next_step_text, benign_context_text)
        VALUES (%s, %s, %s, 'en', %s, %s,
                'Pattern may reflect normal event-driven demand.',
                'Review listed transactions through authorized procedures.',
                'May reflect normal pre-event demand.')
        ON CONFLICT (alert_id, locale) DO NOTHING
        """,
        (
            f"f6000000-0000-4000-8000-{idx:012x}",
            ids["alert"],
            EXPL_TEMPLATE,
            f"Possible unusual {spec['provider_label']} activity at Outlet 001.",
            spec["evidence_summary"],
        ),
    )
    cur.execute(
        """
        INSERT INTO cases
          (case_id, case_number, alert_id, outlet_id, provider_id, routing_rule_id,
           status, current_owner_user_id, current_owner_role, recommended_next_step,
           opened_at, acknowledged_at, escalated_at, resolved_at, resolution_summary, version)
        VALUES (%s, %s, %s, %s, %s, %s, 'resolved', %s, 'provider_ops',
                'Review evidence and coordinate through approved provider-scoped procedures.',
                '2026-07-04', '2026-07-04', '2026-07-04', '2026-07-05', %s, 1)
        ON CONFLICT (case_id) DO NOTHING
        """,
        (
            ids["case"],
            case_number,
            ids["alert"],
            OUTLET,
            provider,
            ROUTING[provider],
            OPS[provider],
            spec["resolution_summary"],
        ),
    )
    cur.execute(
        """
        INSERT INTO case_notes
          (case_note_id, case_id, author_user_id, note_text, note_type)
        VALUES (%s, %s, %s, %s, 'resolution')
        ON CONFLICT (case_note_id) DO NOTHING
        """,
        (ids["note"], ids["case"], OPS[provider], spec["note_text"]),
    )
    cur.execute(
        """
        INSERT INTO case_reviews
          (case_review_id, case_id, reviewed_by_user_id, disposition,
           was_false_positive, review_summary)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (case_id) DO NOTHING
        """,
        (
            ids["review"],
            ids["case"],
            OPS[provider],
            spec["disposition"],
            spec["was_false_positive"],
            spec["review_summary"],
        ),
    )

    source_text = _join_parts(
        [
            spec["evidence_summary"],
            spec["resolution_summary"],
            spec["note_text"],
            spec["review_summary"],
        ]
    )
    embedding = embed_text(source_text)
    cur.execute(
        """
        INSERT INTO case_embeddings
          (case_id, provider_id, outlet_id, source_text, embedding, embedding_dim, corpus_origin)
        VALUES (%s, %s, %s, %s, %s, %s, 'seeded_demo')
        ON CONFLICT (case_id) DO UPDATE SET
          provider_id = EXCLUDED.provider_id,
          outlet_id = EXCLUDED.outlet_id,
          source_text = EXCLUDED.source_text,
          embedding = EXCLUDED.embedding,
          embedding_dim = EXCLUDED.embedding_dim,
          corpus_origin = EXCLUDED.corpus_origin,
          indexed_at = now()
        """,
        (ids["case"], provider, OUTLET, source_text, embedding, EMBEDDING_DIM),
    )


def main() -> int:
    conn = psycopg2.connect(_dsn())
    try:
        with conn:
            with conn.cursor() as cur:
                _ensure_infrastructure(cur)
                for idx, spec in enumerate(SEED_CASES, start=1):
                    _seed_one_case(cur, idx, spec)
        print("  RAG similar-case seed corpus applied (idempotent).")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
