-- =============================================================================
-- Migration 011 — Case similar-embedding index (Feature 3: RAG retrieval)
-- Stores provider-scoped text embeddings for resolved cases. Forward-only.
-- =============================================================================

CREATE TABLE case_embeddings (
  case_id        uuid PRIMARY KEY REFERENCES cases(case_id) ON DELETE CASCADE,
  provider_id    uuid NOT NULL,
  outlet_id      uuid NOT NULL,
  source_text    text NOT NULL,
  embedding      double precision[] NOT NULL,
  embedding_dim  integer NOT NULL CHECK (embedding_dim > 0),
  corpus_origin  text NOT NULL
    CHECK (corpus_origin IN ('seeded_demo', 'live_resolved')),
  indexed_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX case_embeddings_provider_idx ON case_embeddings (provider_id);

ALTER TABLE case_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_case_embeddings ON case_embeddings FOR SELECT TO authenticated
  USING (app.has_case_access(case_id));

GRANT SELECT ON case_embeddings TO authenticated;
GRANT ALL ON case_embeddings TO service_role;
