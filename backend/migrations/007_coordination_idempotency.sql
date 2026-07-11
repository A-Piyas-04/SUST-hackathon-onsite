-- =============================================================================
-- Migration 007 — Coordination idempotency (Phase 5)
-- Source of truth: docs/16-hour-hackathon-phase-distribution.md (Phase 5),
--                  docs/Problem_Statement.md §14 (advisory-only guardrails).
-- Forward-only (docs/schema.md §4.2). Adds a duplicate-mutation defense for case
-- workflow endpoints so a replayed request produces no duplicated side effects
-- and returns the original response. No financial/punitive semantics.
-- =============================================================================

CREATE TABLE coordination_idempotency_keys (
  idempotency_key text        NOT NULL,
  scope_key       text        NOT NULL,   -- e.g. 'case:<uuid>' or 'alert:<uuid>:case'
  action          text        NOT NULL,   -- workflow action name
  actor_user_id   uuid        REFERENCES app_users(user_id),
  response_status integer     NOT NULL,
  response_body   jsonb       NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT pk_coordination_idempotency PRIMARY KEY (idempotency_key, scope_key, action)
);

-- Replay defense is append-only: a stored idempotency record is never mutated.
CREATE TRIGGER trg_coordination_idempotency_append_only
  BEFORE UPDATE OR DELETE ON coordination_idempotency_keys
  FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- Least-privilege grants (service writes; authenticated may read own replay rows).
GRANT SELECT, INSERT ON coordination_idempotency_keys TO service_role;
GRANT SELECT ON coordination_idempotency_keys TO authenticated;
