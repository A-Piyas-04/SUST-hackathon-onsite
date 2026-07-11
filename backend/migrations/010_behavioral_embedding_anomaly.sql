-- =============================================================================
-- Migration 010 — Behavioral embedding anomaly detector
-- Source of truth: docs/schema.md §9.7 (anomaly_rules), docs/AI_ML_FEATURES.md
--
-- Adds the behavioral_embedding pattern value and an active seed rule for the
-- fourth MVP anomaly detector (k-NN distance on per-outlet feature vectors).
-- No table changes — only domain evolution and forward-only reference data.
-- See docs/adr/0007-behavioral-embedding-anomaly-detector.md for rationale.
-- =============================================================================

ALTER DOMAIN anomaly_pattern DROP CONSTRAINT anomaly_pattern_check;
ALTER DOMAIN anomaly_pattern ADD CONSTRAINT anomaly_pattern_check CHECK (
  VALUE IN (
    'near_identical_amounts',
    'velocity_spike',
    'transaction_splitting',
    'circular_activity',
    'balance_inconsistency',
    'time_anomaly',
    'failure_rate',
    'behavioral_embedding'
  )
);

INSERT INTO anomaly_rules
  (anomaly_rule_id, code, pattern, version, name, description, configuration, is_active) VALUES
  ('a9000000-0000-0000-0000-000000000004', 'behavioral_embedding_v1', 'behavioral_embedding', 'v1',
     'Behavioral embedding / k-NN outlier',
     'Flags a transaction whose feature vector sits unusually far from this outlet''s own historical neighborhood for human review. Evidence shows nearest historical neighbors for comparison. Being flagged is not a determination of wrongdoing.',
     '{"k": 3, "distance_threshold": 2.5, "minimum_history_transactions": 10, "window_minutes": 60}'::jsonb,
     true)
ON CONFLICT (code) DO NOTHING;
