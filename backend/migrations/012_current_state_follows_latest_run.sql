-- Migration 012 — Current dashboard state follows scenario run order
--
-- Synthetic scenarios have different timeline lengths. Ordering current-state
-- rows only by observed_at lets an older, longer scenario remain visible after
-- a newer, shorter scenario completes. Prioritize the real simulation run
-- start time first, then use observation time within that run.

CREATE OR REPLACE VIEW v_latest_cash_balance WITH (security_invoker = true) AS
SELECT DISTINCT ON (c.outlet_id)
  c.outlet_id, c.cash_balance_snapshot_id, c.simulation_run_id, c.balance,
  c.currency_code, c.observed_at, c.received_at, c.source_kind, c.created_at
FROM cash_balance_snapshots c
JOIN simulation_runs sr ON sr.simulation_run_id = c.simulation_run_id
ORDER BY c.outlet_id, sr.started_at DESC, c.observed_at DESC,
         c.received_at DESC, c.created_at DESC, c.cash_balance_snapshot_id DESC;

CREATE OR REPLACE VIEW v_latest_provider_balances WITH (security_invoker = true) AS
WITH per_ts AS (
  SELECT simulation_run_id, outlet_provider_account_id, observed_at,
         count(DISTINCT balance) AS distinct_bal
  FROM provider_balance_snapshots
  GROUP BY simulation_run_id, outlet_provider_account_id, observed_at
),
latest AS (
  SELECT
    pbs.*,
    row_number() OVER (
      PARTITION BY pbs.outlet_provider_account_id
      ORDER BY sr.started_at DESC, pbs.observed_at DESC,
               pbs.received_at DESC, pbs.created_at DESC,
               pbs.provider_balance_snapshot_id DESC
    ) AS rn
  FROM provider_balance_snapshots pbs
  JOIN simulation_runs sr ON sr.simulation_run_id = pbs.simulation_run_id
)
SELECT
  l.outlet_provider_account_id,
  l.outlet_id,
  l.provider_id,
  l.currency_code,
  (pt.distinct_bal > 1) AS is_conflicted,
  CASE WHEN pt.distinct_bal > 1 THEN NULL ELSE l.balance END AS balance,
  CASE WHEN pt.distinct_bal > 1 THEN NULL ELSE l.observed_at END AS observed_at,
  l.received_at,
  lt.balance AS last_trusted_balance,
  lt.observed_at AS last_trusted_observed_at
FROM latest l
JOIN per_ts pt
  ON pt.simulation_run_id = l.simulation_run_id
 AND pt.outlet_provider_account_id = l.outlet_provider_account_id
 AND pt.observed_at = l.observed_at
LEFT JOIN LATERAL (
  SELECT s.balance, s.observed_at
  FROM provider_balance_snapshots s
  WHERE s.simulation_run_id = l.simulation_run_id
    AND s.outlet_provider_account_id = l.outlet_provider_account_id
    AND s.observed_at IN (
      SELECT s2.observed_at
      FROM provider_balance_snapshots s2
      WHERE s2.simulation_run_id = l.simulation_run_id
        AND s2.outlet_provider_account_id = l.outlet_provider_account_id
      GROUP BY s2.observed_at
      HAVING count(DISTINCT s2.balance) = 1
    )
  ORDER BY s.observed_at DESC, s.received_at DESC, s.created_at DESC
  LIMIT 1
) lt ON true
WHERE l.rn = 1;

CREATE OR REPLACE VIEW v_current_feed_health WITH (security_invoker = true) AS
SELECT DISTINCT ON (dqa.outlet_id, dqa.provider_id)
  dqa.outlet_id, dqa.provider_id, dqa.data_quality_assessment_id, dqa.status,
  dqa.confidence_modifier, dqa.sample_count, dqa.latest_source_at,
  dqa.assessed_at, dqa.engine_version, dqa.summary
FROM data_quality_assessments dqa
JOIN simulation_runs sr ON sr.simulation_run_id = dqa.simulation_run_id
ORDER BY dqa.outlet_id, dqa.provider_id, sr.started_at DESC,
         dqa.assessed_at DESC, dqa.created_at DESC,
         dqa.data_quality_assessment_id DESC;

CREATE OR REPLACE VIEW v_latest_liquidity_projections WITH (security_invoker = true) AS
SELECT DISTINCT ON (lp.outlet_id, lp.reserve_type, lp.outlet_provider_account_id)
  lp.liquidity_projection_id, lp.analytics_run_id, lp.outlet_id, lp.reserve_type,
  lp.outlet_provider_account_id, lp.provider_id,
  lp.primary_data_quality_assessment_id, lp.as_of_at, lp.current_balance,
  lp.burn_rate_per_hour, lp.projected_shortage_at, lp.lower_bound_at,
  lp.upper_bound_at, lp.confidence_score, lp.confidence_level, lp.sample_count,
  lp.is_actionable, lp.non_actionable_reason, lp.created_at
FROM liquidity_projections lp
JOIN analytics_runs ar ON ar.analytics_run_id = lp.analytics_run_id
JOIN simulation_runs sr ON sr.simulation_run_id = ar.simulation_run_id
ORDER BY lp.outlet_id, lp.reserve_type, lp.outlet_provider_account_id,
         sr.started_at DESC, ar.started_at DESC, lp.as_of_at DESC,
         lp.created_at DESC, lp.liquidity_projection_id DESC;
