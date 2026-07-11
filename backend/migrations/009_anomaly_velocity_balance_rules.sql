-- =============================================================================
-- Migration 009 — Activate velocity_spike and balance_inconsistency anomaly rules
-- Source of truth: docs/schema.md §9.7 (anomaly_rules)
--
-- Adds seed rows for the two additional MVP anomaly detectors so the analytics
-- runner can dispatch all three implemented patterns independently. No schema
-- change — only forward-only reference data for new rule configurations.
-- See docs/adr/0006-velocity-balance-anomaly-detectors.md for rationale.
-- =============================================================================

INSERT INTO anomaly_rules
  (anomaly_rule_id, code, pattern, version, name, description, configuration, is_active) VALUES
  ('a9000000-0000-0000-0000-000000000002', 'velocity_spike_v1', 'velocity_spike', 'v1',
     'Transaction velocity spike',
     'Flags a short-window transaction count exceeding the outlet''s same-hour baseline by N standard deviations for human review. Being flagged is not a determination of wrongdoing.',
     '{"window_minutes": 10, "std_dev_threshold": 2.0, "minimum_baseline_windows": 3, "minimum_spike_count": 8}'::jsonb,
     true),
  ('a9000000-0000-0000-0000-000000000003', 'balance_inconsistency_v1', 'balance_inconsistency', 'v1',
     'Balance inconsistency / data conflict',
     'Flags when a provider balance feed disagrees with the transaction log or with itself at the same timestamp. Framed as a data-quality finding, not wallet integrity loss.',
     '{"min_discrepancy_amount": 100.0, "min_discrepancy_pct": 0.5, "staleness_soft_minutes": 120}'::jsonb,
     true)
ON CONFLICT (code) DO NOTHING;
