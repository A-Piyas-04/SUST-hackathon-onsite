"""Provider-scoped similar-case retrieval (Feature 3).

Indexing runs best-effort on resolve; retrieval enriches GET case detail only.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.contracts.v1.coordination import (
    SimilarCaseMatch,
    SimilarCasesPanel,
)
from app.contracts.v1.enums import ReviewOutcome

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 512
MIN_CORPUS_SIZE = 2
TOP_K = 3
INSUFFICIENT_MESSAGE = "No comparable cases yet"

_vectorizer = HashingVectorizer(
    n_features=EMBEDDING_DIM,
    alternate_sign=False,
    norm="l2",
    lowercase=True,
    stop_words="english",
)


def embed_text(raw: str) -> list[float]:
    """HashingVectorizer embedding; returns a zero vector for empty input."""
    if not raw or not raw.strip():
        return [0.0] * EMBEDDING_DIM
    vec = _vectorizer.transform([raw.strip()]).toarray()[0]
    return [float(x) for x in vec]


def cosine_similarity(query: list[float], candidate: list[float]) -> float:
    a = np.asarray(query, dtype=np.float64)
    b = np.asarray(candidate, dtype=np.float64)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _join_parts(parts: list[str | None]) -> str:
    return "\n\n".join(p.strip() for p in parts if p and p.strip())


async def _alert_evidence_summary(session: AsyncSession, alert_id: UUID) -> str:
    result = await session.execute(
        text(
            """
            SELECT structured_payload->>'evidence_summary' AS evidence_summary
            FROM alerts
            WHERE alert_id = :alert_id
            """
        ),
        {"alert_id": alert_id},
    )
    row = result.mappings().first()
    if row is None:
        return ""
    return row["evidence_summary"] or ""


async def build_index_text(session: AsyncSession, case_id: UUID) -> str:
    """Compose text indexed when a case is resolved."""
    case_row = (
        await session.execute(
            text(
                """
                SELECT alert_id, resolution_summary
                FROM cases
                WHERE case_id = :case_id
                """
            ),
            {"case_id": case_id},
        )
    ).mappings().first()
    if case_row is None:
        return ""

    notes = (
        await session.execute(
            text(
                """
                SELECT note_text
                FROM case_notes
                WHERE case_id = :case_id
                ORDER BY created_at
                """
            ),
            {"case_id": case_id},
        )
    ).mappings().all()

    review = (
        await session.execute(
            text(
                """
                SELECT review_summary
                FROM case_reviews
                WHERE case_id = :case_id
                """
            ),
            {"case_id": case_id},
        )
    ).mappings().first()

    evidence = await _alert_evidence_summary(session, case_row["alert_id"])
    note_texts = [n["note_text"] for n in notes]
    review_summary = review["review_summary"] if review else None

    return _join_parts(
        [
            evidence,
            case_row["resolution_summary"],
            *note_texts,
            review_summary,
        ]
    )


async def index_resolved_case(
    session: AsyncSession,
    case_id: UUID,
    *,
    corpus_origin: str = "live_resolved",
) -> None:
    """Upsert embedding for a resolved, provider-scoped case."""
    row = (
        await session.execute(
            text(
                """
                SELECT case_id, outlet_id, provider_id, status
                FROM cases
                WHERE case_id = :case_id
                """
            ),
            {"case_id": case_id},
        )
    ).mappings().first()
    if row is None or row["status"] != "resolved" or row["provider_id"] is None:
        return

    source_text = await build_index_text(session, case_id)
    if not source_text.strip():
        return

    embedding = embed_text(source_text)
    await session.execute(
        text(
            """
            INSERT INTO case_embeddings (
              case_id, provider_id, outlet_id, source_text,
              embedding, embedding_dim, corpus_origin
            ) VALUES (
              :case_id, :provider_id, :outlet_id, :source_text,
              :embedding, :embedding_dim, :corpus_origin
            )
            ON CONFLICT (case_id) DO UPDATE SET
              provider_id = EXCLUDED.provider_id,
              outlet_id = EXCLUDED.outlet_id,
              source_text = EXCLUDED.source_text,
              embedding = EXCLUDED.embedding,
              embedding_dim = EXCLUDED.embedding_dim,
              corpus_origin = EXCLUDED.corpus_origin,
              indexed_at = now()
            """
        ),
        {
            "case_id": case_id,
            "provider_id": row["provider_id"],
            "outlet_id": row["outlet_id"],
            "source_text": source_text,
            "embedding": embedding,
            "embedding_dim": EMBEDDING_DIM,
            "corpus_origin": corpus_origin,
        },
    )


async def retrieve_similar_cases(
    session: AsyncSession,
    *,
    case_id: UUID,
    alert_id: UUID,
    provider_id: UUID | None,
) -> SimilarCasesPanel:
    """Provider-filtered similarity search for case detail enrichment."""
    if provider_id is None:
        return SimilarCasesPanel(status="unavailable", matches=[], message=None)

    query_text = await _alert_evidence_summary(session, alert_id)
    if not query_text.strip():
        return SimilarCasesPanel(
            status="insufficient_corpus",
            matches=[],
            message=INSUFFICIENT_MESSAGE,
        )

    query_vec = embed_text(query_text)
    rows = (
        await session.execute(
            text(
                """
                SELECT e.case_id, e.embedding, e.corpus_origin,
                       c.case_number, c.resolution_summary,
                       r.disposition, r.was_false_positive, r.review_summary
                FROM case_embeddings e
                JOIN cases c ON c.case_id = e.case_id
                LEFT JOIN case_reviews r ON r.case_id = e.case_id
                WHERE e.provider_id = :provider_id
                  AND e.case_id <> :case_id
                  AND c.status = 'resolved'
                """
            ),
            {"provider_id": provider_id, "case_id": case_id},
        )
    ).mappings().all()

    if len(rows) < MIN_CORPUS_SIZE:
        return SimilarCasesPanel(
            status="insufficient_corpus",
            matches=[],
            message=INSUFFICIENT_MESSAGE,
        )

    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        sim = cosine_similarity(query_vec, list(row["embedding"]))
        scored.append((sim, row))

    scored.sort(key=lambda item: item[0], reverse=True)
    matches: list[SimilarCaseMatch] = []
    for sim, row in scored[:TOP_K]:
        disposition = row["disposition"]
        matches.append(
            SimilarCaseMatch(
                case_id=row["case_id"],
                case_number=row["case_number"],
                disposition=ReviewOutcome(disposition) if disposition else None,
                was_false_positive=row["was_false_positive"],
                resolution_summary=row["resolution_summary"] or "",
                review_summary=row["review_summary"],
                similarity=round(sim, 4),
                corpus_origin=row["corpus_origin"],
            )
        )

    return SimilarCasesPanel(status="ready", matches=matches, message=None)
