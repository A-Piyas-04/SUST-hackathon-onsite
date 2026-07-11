"""Feature 3 — RAG similar-case retrieval tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from app.core.auth import BKASH, NAGAD, OUTLET1
from app.services.coordination.similar_cases import embed_text
from tests.phase5.conftest import anomaly_alert, publish, start_run

BKASH_SEED_CASE = "f3000000-0000-4000-8000-000000000001"
BKASH_SEED_CASE_2 = "f3000000-0000-4000-8000-000000000002"
NAGAD_SEED_CASE = "f3000000-0000-4000-8000-000000000004"
NAGAD_SEED_CASE_2 = "f3000000-0000-4000-8000-000000000005"
BKASH_EID_RESOLUTION = (
    "Coordinated with outlet agent; confirmed pre-Eid cash-out surge from regular "
    "customers. No further action required."
)


def _open_bkash_case(client, ops_headers, admin_headers):
    run_id = start_run(client, admin_headers, "scenario_b")
    published = publish(client, admin_headers, run_id)
    alert = anomaly_alert(published)
    assert alert is not None
    resp = client.post(f"/api/v1/alerts/{alert['alert_id']}/cases", json={}, headers=ops_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_cold_start_insufficient_corpus(client, bkash_ops_headers, admin_headers, conn):
    """Fewer than MIN_CORPUS_SIZE embeddings => empty panel, explicit message."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM case_embeddings WHERE provider_id = %s",
            (str(BKASH),),
        )
        conn.commit()

    case = _open_bkash_case(client, bkash_ops_headers, admin_headers)
    detail = client.get(f"/api/v1/cases/{case['case_id']}", headers=bkash_ops_headers).json()
    panel = detail["similar_cases"]
    assert panel["status"] == "insufficient_corpus"
    assert panel["matches"] == []
    assert panel["message"] == "No comparable cases yet"


def test_provider_scoping_never_crosses(client, bkash_ops_headers, admin_headers, conn):
    """Near-identical text under different providers must not cross-retrieve."""
    shared = (
        "Velocity spike detected: 12 cash-out transactions at Outlet 001 within 10 minutes, "
        "exceeding the outlet same-hour baseline. Pattern may reflect pre-Eid market demand."
    )
    vec = embed_text(shared)
    with conn.cursor() as cur:
        for case_id, provider in (
            (BKASH_SEED_CASE, BKASH),
            (BKASH_SEED_CASE_2, BKASH),
            (NAGAD_SEED_CASE, NAGAD),
            (NAGAD_SEED_CASE_2, NAGAD),
        ):
            cur.execute(
                """
                INSERT INTO case_embeddings
                  (case_id, provider_id, outlet_id, source_text, embedding, embedding_dim, corpus_origin)
                VALUES (%s, %s, %s, %s, %s, 512, 'seeded_demo')
                ON CONFLICT (case_id) DO UPDATE SET
                  embedding = EXCLUDED.embedding,
                  source_text = EXCLUDED.source_text,
                  provider_id = EXCLUDED.provider_id
                """,
                (case_id, str(provider), str(OUTLET1), shared, vec),
            )
        conn.commit()

    case = _open_bkash_case(client, bkash_ops_headers, admin_headers)
    detail = client.get(f"/api/v1/cases/{case['case_id']}", headers=bkash_ops_headers).json()
    panel = detail["similar_cases"]
    assert panel["status"] == "ready"
    matched_ids = {m["case_id"] for m in panel["matches"]}
    assert NAGAD_SEED_CASE not in matched_ids
    assert NAGAD_SEED_CASE_2 not in matched_ids


def test_retrieved_text_is_verbatim(client, bkash_ops_headers, admin_headers):
    """Returned summaries must match stored records exactly."""
    case = _open_bkash_case(client, bkash_ops_headers, admin_headers)
    detail = client.get(f"/api/v1/cases/{case['case_id']}", headers=bkash_ops_headers).json()
    panel = detail["similar_cases"]
    assert panel["status"] == "ready"
    assert len(panel["matches"]) >= 2

    eid_match = next(
        (m for m in panel["matches"] if m["case_number"] == "CASE-SEED-RAG-BKASH-001"),
        None,
    )
    assert eid_match is not None
    assert eid_match["resolution_summary"] == BKASH_EID_RESOLUTION
    assert "Benign operational spike consistent with seasonal pre-Eid demand" in (
        eid_match["review_summary"] or ""
    )


def test_retrieval_failure_does_not_break_case_detail(client, bkash_ops_headers, admin_headers):
    case = _open_bkash_case(client, bkash_ops_headers, admin_headers)
    with patch(
        "app.services.coordination.cases.similar_cases.retrieve_similar_cases",
        new_callable=AsyncMock,
        side_effect=RuntimeError("embedding service down"),
    ):
        resp = client.get(f"/api/v1/cases/{case['case_id']}", headers=bkash_ops_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["case_id"] == case["case_id"]
    assert body["case_number"] == case["case_number"]
    assert body["similar_cases"]["status"] == "unavailable"
    assert body["similar_cases"]["matches"] == []


def test_mutation_responses_omit_similar_cases(client, bkash_ops_headers, admin_headers):
    """Lifecycle mutations keep similar_cases unset (additive GET-only field)."""
    case = _open_bkash_case(client, bkash_ops_headers, admin_headers)
    assert case.get("similar_cases") is None
    ack = client.post(
        f"/api/v1/cases/{case['case_id']}/acknowledge", json={}, headers=bkash_ops_headers
    ).json()
    assert ack.get("similar_cases") is None


def test_resolve_indexes_live_embedding(client, bkash_ops_headers, admin_headers, conn):
    case = _open_bkash_case(client, bkash_ops_headers, admin_headers)
    cid = case["case_id"]
    client.post(f"/api/v1/cases/{cid}/acknowledge", json={}, headers=bkash_ops_headers)
    resolved = client.post(
        f"/api/v1/cases/{cid}/resolve",
        json={"resolution_summary": "Live resolve text for embedding index test."},
        headers=bkash_ops_headers,
    )
    assert resolved.status_code == 200

    with conn.cursor() as cur:
        cur.execute(
            "SELECT corpus_origin, source_text FROM case_embeddings WHERE case_id = %s",
            (cid,),
        )
        row = cur.fetchone()
    assert row is not None
    assert row[0] == "live_resolved"
    assert "Live resolve text for embedding index test." in row[1]


def test_e2e_similar_panel_with_seeded_matches(client, bkash_ops_headers, admin_headers):
    """Open case with Eid-like evidence returns seeded matches with similarity scores."""
    case = _open_bkash_case(client, bkash_ops_headers, admin_headers)
    detail = client.get(f"/api/v1/cases/{case['case_id']}", headers=bkash_ops_headers).json()
    panel = detail["similar_cases"]
    assert panel["status"] == "ready"
    assert len(panel["matches"]) >= 2
    assert all(0.0 <= m["similarity"] <= 1.0 for m in panel["matches"])
    assert any(m["corpus_origin"] == "seeded_demo" for m in panel["matches"])
    assert any(m["case_number"].startswith("CASE-SEED-RAG-") for m in panel["matches"])
