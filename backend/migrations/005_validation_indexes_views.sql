-- =============================================================================
-- Migration 005 — Validation, Indexes, and Read Models (Views)
-- Source of truth: docs/schema.md §11 (validation), §12 (views), §14 (indexes).
-- Views set security_invoker = true so Row Level Security (migration 006) is
-- enforced through the read models for the querying role. No view exposes a
-- blended monetary total (docs §12, §13.3).
-- =============================================================================

-- =============================================================================
-- 11.1 validation_runs / 11.2 ground_truth_labels / 11.3 metric_results
-- =============================================================================
CREATE TABLE validation_runs (
  validation_run_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name               text NOT NULL,
  dataset_split      validation_split NOT NULL,
  engine_version     text NOT NULL,
  configuration      jsonb NOT NULL DEFAULT '{}'::jsonb,
  started_at         timestamptz NOT NULL DEFAULT now(),
  completed_at       timestamptz,
  status             text NOT NULL DEFAULT 'running'
                       CHECK (status IN ('running','completed','failed')),
  created_by_user_id uuid REFERENCES app_users(user_id)
);

CREATE TABLE ground_truth_labels (
  ground_truth_label_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  validation_run_id     uuid NOT NULL REFERENCES validation_runs(validation_run_id),
  simulation_run_id     uuid NOT NULL REFERENCES simulation_runs(simulation_run_id),
  outlet_id             uuid NOT NULL REFERENCES outlets(outlet_id),
  provider_id           uuid REFERENCES providers(provider_id),
  label_type            text NOT NULL
                          CHECK (label_type IN ('shortage','anomaly','normal','data_quality_incident')),
  expected_value        jsonb NOT NULL DEFAULT '{}'::jsonb,
  window_start          timestamptz NOT NULL,
  window_end            timestamptz NOT NULL,
  created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE metric_results (
  metric_result_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  validation_run_id uuid NOT NULL REFERENCES validation_runs(validation_run_id),
  metric_code       text NOT NULL,
  category          text NOT NULL
                      CHECK (category IN ('analytics','performance','reliability','explainability')),
  value             numeric NOT NULL,
  unit              text NOT NULL,
  sample_size       integer NOT NULL CHECK (sample_size > 0),
  method            text NOT NULL,
  limitations       text NOT NULL,
  details           jsonb NOT NULL DEFAULT '{}'::jsonb,
  computed_at       timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- §14 Indexes
-- =============================================================================
CREATE INDEX ix_txn_outlet_provider_time   ON transactions (outlet_id, provider_id, occurred_at DESC);
CREATE INDEX ix_txn_provider_party_time     ON transactions (provider_id, synthetic_party_ref, occurred_at DESC);
CREATE INDEX ix_cash_outlet_time            ON cash_balance_snapshots (outlet_id, observed_at DESC, received_at DESC);
CREATE INDEX ix_pbs_account_time            ON provider_balance_snapshots (outlet_provider_account_id, observed_at DESC, received_at DESC);
CREATE INDEX ix_batch_outlet_provider_time  ON ingestion_batches (outlet_id, provider_id, received_at DESC);
CREATE INDEX ix_dqa_outlet_provider_time    ON data_quality_assessments (outlet_id, provider_id, assessed_at DESC);
CREATE INDEX ix_lp_outlet_reserve_time      ON liquidity_projections (outlet_id, reserve_type, provider_id, as_of_at DESC);
CREATE INDEX ix_af_outlet_provider_time     ON anomaly_flags (outlet_id, provider_id, window_end DESC);
CREATE INDEX ix_alerts_queue                ON alerts (outlet_id, provider_id, state, severity, detected_at DESC);
CREATE INDEX ix_cases_provider_status       ON cases (provider_id, status, updated_at DESC);
CREATE INDEX ix_cases_outlet_status         ON cases (outlet_id, status, updated_at DESC);
CREATE INDEX ix_notifications_recipient      ON notifications (recipient_user_id, status, queued_at DESC);
CREATE INDEX ix_audit_case_time             ON audit_events (case_id, occurred_at);

-- =============================================================================
-- §12 Views
-- =============================================================================

-- v_latest_cash_balance — latest shared-cash snapshot per outlet (no provider cols).
CREATE VIEW v_latest_cash_balance WITH (security_invoker = true) AS
SELECT DISTINCT ON (outlet_id)
  outlet_id, cash_balance_snapshot_id, simulation_run_id, balance, currency_code,
  observed_at, received_at, source_kind, created_at
FROM cash_balance_snapshots
ORDER BY outlet_id, observed_at DESC, received_at DESC, created_at DESC;

-- v_latest_provider_balances — one row per account; surfaces conflicts without
-- ever selecting a candidate as truth and without summing providers (docs §12).
CREATE VIEW v_latest_provider_balances WITH (security_invoker = true) AS
WITH per_ts AS (
  SELECT outlet_provider_account_id, observed_at, count(DISTINCT balance) AS distinct_bal
  FROM provider_balance_snapshots
  GROUP BY outlet_provider_account_id, observed_at
),
latest AS (
  SELECT
    pbs.*,
    row_number() OVER (PARTITION BY outlet_provider_account_id
                       ORDER BY observed_at DESC, received_at DESC, created_at DESC) AS rn
  FROM provider_balance_snapshots pbs
)
SELECT
  l.outlet_provider_account_id,
  l.outlet_id,
  l.provider_id,
  l.currency_code,
  (pt.distinct_bal > 1)                                    AS is_conflicted,
  CASE WHEN pt.distinct_bal > 1 THEN NULL ELSE l.balance     END AS balance,
  CASE WHEN pt.distinct_bal > 1 THEN NULL ELSE l.observed_at END AS observed_at,
  l.received_at,
  lt.balance     AS last_trusted_balance,
  lt.observed_at AS last_trusted_observed_at
FROM latest l
JOIN per_ts pt
  ON pt.outlet_provider_account_id = l.outlet_provider_account_id
 AND pt.observed_at = l.observed_at
LEFT JOIN LATERAL (
  SELECT s.balance, s.observed_at
  FROM provider_balance_snapshots s
  WHERE s.outlet_provider_account_id = l.outlet_provider_account_id
    AND s.observed_at IN (
      SELECT s2.observed_at
      FROM provider_balance_snapshots s2
      WHERE s2.outlet_provider_account_id = l.outlet_provider_account_id
      GROUP BY s2.observed_at
      HAVING count(DISTINCT s2.balance) = 1
    )
  ORDER BY s.observed_at DESC, s.received_at DESC
  LIMIT 1
) lt ON true
WHERE l.rn = 1;

-- v_current_feed_health — latest quality assessment per outlet/provider.
CREATE VIEW v_current_feed_health WITH (security_invoker = true) AS
SELECT DISTINCT ON (outlet_id, provider_id)
  outlet_id, provider_id, data_quality_assessment_id, status, confidence_modifier,
  sample_count, latest_source_at, assessed_at, engine_version, summary
FROM data_quality_assessments
ORDER BY outlet_id, provider_id, assessed_at DESC, created_at DESC;

-- v_latest_liquidity_projections — latest per outlet + reserve identity
-- (shared_cash collapses to one row per outlet; providers one per account).
CREATE VIEW v_latest_liquidity_projections WITH (security_invoker = true) AS
SELECT DISTINCT ON (outlet_id, reserve_type, outlet_provider_account_id)
  liquidity_projection_id, analytics_run_id, outlet_id, reserve_type,
  outlet_provider_account_id, provider_id, primary_data_quality_assessment_id,
  as_of_at, current_balance, burn_rate_per_hour, projected_shortage_at,
  lower_bound_at, upper_bound_at, confidence_score, confidence_level,
  sample_count, is_actionable, non_actionable_reason, created_at
FROM liquidity_projections
ORDER BY outlet_id, reserve_type, outlet_provider_account_id, as_of_at DESC, created_at DESC;

-- v_outlet_dashboard — separated shared cash + provider array; NO blended total.
CREATE VIEW v_outlet_dashboard WITH (security_invoker = true) AS
SELECT
  o.outlet_id,
  o.synthetic_code,
  o.display_name,
  o.area_id,
  o.currency_code,
  jsonb_build_object(
    'balance',     cb.balance,
    'currency',    cb.currency_code,
    'observed_at', cb.observed_at,
    'projection',  (
      SELECT jsonb_build_object(
               'shortage_at',      lp.projected_shortage_at,
               'confidence_score', lp.confidence_score,
               'confidence_level', lp.confidence_level)
      FROM v_latest_liquidity_projections lp
      WHERE lp.outlet_id = o.outlet_id AND lp.reserve_type = 'shared_cash'
    )
  ) AS shared_cash,
  (
    SELECT COALESCE(jsonb_agg(
      jsonb_build_object(
        'provider',                   jsonb_build_object('code', pr.code, 'display_name', pr.display_name),
        'outlet_provider_account_id', opa.outlet_provider_account_id,
        'balance',                    pb.balance,
        'last_trusted_balance',       pb.last_trusted_balance,
        'observed_at',                pb.observed_at,
        'is_conflicted',              COALESCE(pb.is_conflicted, false),
        'feed_health',                jsonb_build_object('status', fh.status, 'confidence_modifier', fh.confidence_modifier),
        'projection',                 jsonb_build_object(
                                        'shortage_at',      lp.projected_shortage_at,
                                        'confidence_score', lp.confidence_score,
                                        'confidence_level', lp.confidence_level)
      ) ORDER BY pr.code), '[]'::jsonb)
    FROM outlet_provider_accounts opa
    JOIN providers pr ON pr.provider_id = opa.provider_id
    LEFT JOIN v_latest_provider_balances pb   ON pb.outlet_provider_account_id = opa.outlet_provider_account_id
    LEFT JOIN v_current_feed_health fh         ON fh.outlet_id = opa.outlet_id AND fh.provider_id = opa.provider_id
    LEFT JOIN v_latest_liquidity_projections lp ON lp.outlet_id = opa.outlet_id
                                               AND lp.reserve_type = 'provider_e_money'
                                               AND lp.outlet_provider_account_id = opa.outlet_provider_account_id
    WHERE opa.outlet_id = o.outlet_id AND opa.is_active
  ) AS providers,
  (
    SELECT COALESCE(jsonb_agg(
      jsonb_build_object(
        'alert_id',    a.alert_id,
        'type',        a.alert_type,
        'severity',    a.severity,
        'provider_id', a.provider_id,
        'detected_at', a.detected_at
      ) ORDER BY a.detected_at DESC), '[]'::jsonb)
    FROM alerts a
    WHERE a.outlet_id = o.outlet_id AND a.state = 'active'
  ) AS alerts,
  now() AS generated_at
FROM outlets o
LEFT JOIN v_latest_cash_balance cb ON cb.outlet_id = o.outlet_id;

-- v_case_timeline — chronological, deterministically ordered case history.
CREATE VIEW v_case_timeline WITH (security_invoker = true) AS
SELECT case_id, event_at, event_type, event_id, actor_user_id, detail
FROM (
  SELECT c.case_id, af.created_at AS event_at, 'anomaly_flag' AS event_type,
         af.anomaly_flag_id AS event_id, NULL::uuid AS actor_user_id,
         jsonb_build_object('disposition', af.disposition) AS detail, 0 AS ord
  FROM cases c
  JOIN alerts a ON a.alert_id = c.alert_id
  JOIN alert_anomaly_flags aaf ON aaf.alert_id = a.alert_id
  JOIN anomaly_flags af ON af.anomaly_flag_id = aaf.anomaly_flag_id
  UNION ALL
  SELECT c.case_id, lp.created_at, 'liquidity_projection', lp.liquidity_projection_id, NULL,
         jsonb_build_object('reserve_type', lp.reserve_type), 0
  FROM cases c
  JOIN alerts a ON a.alert_id = c.alert_id
  JOIN alert_liquidity_projections alp ON alp.alert_id = a.alert_id
  JOIN liquidity_projections lp ON lp.liquidity_projection_id = alp.liquidity_projection_id
  UNION ALL
  SELECT c.case_id, a.created_at, 'alert_created', a.alert_id, NULL,
         jsonb_build_object('alert_type', a.alert_type, 'severity', a.severity), 1
  FROM cases c JOIN alerts a ON a.alert_id = c.alert_id
  UNION ALL
  SELECT c.case_id, c.opened_at, 'case_opened', c.case_id, NULL,
         jsonb_build_object('status', 'open'), 2
  FROM cases c
  UNION ALL
  SELECT ca.case_id, ca.assigned_at, 'assignment', ca.case_assignment_id, ca.assigned_by_user_id,
         jsonb_build_object('to_role', ca.assigned_to_role, 'reason', ca.reason), 3
  FROM case_assignments ca
  UNION ALL
  SELECT sh.case_id, sh.changed_at, 'status_change', sh.case_status_history_id, sh.changed_by_user_id,
         jsonb_build_object('from', sh.from_status, 'to', sh.to_status), 4
  FROM case_status_history sh
  UNION ALL
  SELECT n.case_id, n.created_at, 'note', n.case_note_id, n.author_user_id,
         jsonb_build_object('note_type', n.note_type), 5
  FROM case_notes n
  UNION ALL
  SELECT nt.case_id, nt.queued_at, 'notification', nt.notification_id, nt.recipient_user_id,
         jsonb_build_object('channel', nt.channel, 'status', nt.status), 6
  FROM notifications nt
  UNION ALL
  SELECT r.case_id, r.reviewed_at, 'review', r.case_review_id, r.reviewed_by_user_id,
         jsonb_build_object('disposition', r.disposition), 7
  FROM case_reviews r
  UNION ALL
  SELECT ae.case_id, ae.occurred_at, 'audit', ae.audit_event_id, ae.actor_user_id,
         jsonb_build_object('action', ae.action), 8
  FROM audit_events ae WHERE ae.case_id IS NOT NULL
) t
ORDER BY case_id, event_at, ord, event_id;

-- v_validation_summary — latest completed metric results for the metrics panel.
CREATE VIEW v_validation_summary WITH (security_invoker = true) AS
SELECT DISTINCT ON (mr.metric_code)
  mr.metric_code, mr.category, mr.value, mr.unit, mr.sample_size, mr.method,
  mr.limitations, mr.details, mr.computed_at,
  vr.validation_run_id, vr.name AS validation_run_name, vr.engine_version
FROM metric_results mr
JOIN validation_runs vr ON vr.validation_run_id = mr.validation_run_id
WHERE vr.status = 'completed'
ORDER BY mr.metric_code, mr.computed_at DESC;
