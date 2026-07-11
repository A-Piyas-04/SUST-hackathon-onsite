# ADR 0008: RAG Similar-Case Retrieval

## Status

Accepted — 2026-07-12

## Context

Feature 3 in `docs/AI_ML_FEATURES.md` requires surfacing similar previously
resolved cases when a reviewer opens a case. The corpus must be provider-scoped,
retrieval-only (no generation), and degrade gracefully when history is thin.

## Decision

1. **Embedding** — `sklearn.feature_extraction.text.HashingVectorizer` with
   512 features, `alternate_sign=False`, L2 normalization. Cosine similarity
   for ranking. No external embedding API; `scikit-learn` is already a project
   dependency (Feature 1 calibration).

2. **Storage** — Forward migration `011_case_similar_embeddings.sql` adds
   `case_embeddings` with denormalized `provider_id` for query-level filtering
   before similarity is computed.

3. **Indexing** — On successful `resolve()`, best-effort upsert of embedding
   built from alert `evidence_summary` + `resolution_summary` + `case_notes` +
   `case_reviews.review_summary`. Failures never roll back resolve.

4. **Retrieval** — `GET /api/v1/cases/{id}` attaches `similar_cases` panel.
   Query text is the linked alert's `evidence_summary` only. SQL filters
   `WHERE provider_id = :pid` first; never post-filters across providers.

5. **Cold start** — Minimum corpus size **2** resolved embeddings per provider
   (excluding current case). Below threshold: `status=insufficient_corpus`,
   message `"No comparable cases yet"`, empty `matches`.

6. **Demo seed** — Separate `CASE-SEED-RAG-*` corpus (option B); moderate_demo
   cases unchanged. Seeded rows carry `corpus_origin=seeded_demo`; live resolves
   carry `live_resolved`. API exposes origin so judges can distinguish seed
   from live history.

7. **Shared-cash cases** (`provider_id IS NULL`) — indexing and retrieval
   skipped (`status=unavailable`); Feature 3 is provider-scoped by design.

## Consequences

- Case detail responses gain an optional `similar_cases` field; mutation
  endpoints unchanged.
- HashingVectorizer gives stable vectors without corpus refitting; quality is
  adequate at demo scale.
- Nine seeded resolved cases (three per provider) support E2E demos after
  `run_migrations.py seed`.
