-- =============================================================================
-- Migration 008 — Dashboard shows last-trusted balance for conflicting feeds
-- Source of truth: docs/schema.md §12 (views), and the dashboard state rules
--   "frozen last-known value" / "malformed or conflicting feeds must not be
--   charted as continuous truth" / degraded data must never appear as fresh.
--
-- Problem: v_outlet_dashboard surfaced v_latest_provider_balances.balance, which
-- is deliberately NULL when the latest snapshot is conflicting (two distinct
-- balances at the same observed_at — e.g. Scenario C's injected conflict). The
-- dashboard reader then defaulted NULL -> 0, so every conflicted provider showed
-- "BDT 0.00 · fresh" — a misleading zero that also hid the conflict.
--
-- Fix (view-only; contract, reader, and frontend unchanged): when a provider's
-- current balance is unavailable due to conflict, fall back to the already-
-- computed last_trusted_balance / last_trusted_observed_at, and report the feed
-- health status as 'conflicting' so the value is clearly shown as degraded
-- (the UI already renders a non-fresh feed as "Last trusted …"). Shared cash and
-- provider reserves remain separate; no blended total is introduced.
-- =============================================================================

CREATE OR REPLACE VIEW v_outlet_dashboard WITH (security_invoker = true) AS
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
        -- Conflicting feed: fall back to the last trusted (non-conflicting) value
        -- rather than emitting NULL (which the reader turns into a misleading 0).
        'balance',                    COALESCE(pb.balance, pb.last_trusted_balance),
        'last_trusted_balance',       pb.last_trusted_balance,
        'observed_at',                COALESCE(pb.observed_at, pb.last_trusted_observed_at),
        'is_conflicted',              COALESCE(pb.is_conflicted, false),
        'feed_health',                jsonb_build_object(
                                        -- Never present conflicting data as fresh.
                                        'status', CASE WHEN COALESCE(pb.is_conflicted, false)
                                                       THEN 'conflicting' ELSE fh.status END,
                                        'confidence_modifier', fh.confidence_modifier),
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
