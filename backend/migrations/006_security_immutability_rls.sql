-- =============================================================================
-- Migration 006 — Security, Immutability, and Row Level Security
-- Source of truth: docs/schema.md §13 (invariants 16-18), §15 (RLS matrix).
--
-- Expected request context (set by the Phase 2 application layer):
--   * Supabase: a JWT whose `sub` claim is the app_users.user_id; RLS reads it
--     through auth.uid().
--   * Local/tests: `SET LOCAL request.jwt.claims = '{"sub":"<uuid>","role":"authenticated"}'`
--     and `SET LOCAL ROLE authenticated`; or `SET LOCAL app.current_user_id = '<uuid>'`.
--
-- Roles anon/authenticated/service_role are created only if absent (Supabase
-- already provides them). service_role BYPASSRLS. Scope-resolver helpers are
-- SECURITY DEFINER so RLS on parent tables cannot recurse; they only compute a
-- boolean about the *caller's* own scopes (ADR 0004).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS app;

-- --- Guarded Supabase roles ---------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN BYPASSRLS;
  END IF;
END
$$;

-- =============================================================================
-- Identity + scope helper functions
-- =============================================================================

-- Caller identity: auth.uid() (Supabase) -> request.jwt.claims.sub -> GUC.
CREATE OR REPLACE FUNCTION app.current_user_id() RETURNS uuid
LANGUAGE plpgsql STABLE
SET search_path = public, app, auth, pg_temp
AS $$
DECLARE
  uid uuid;
BEGIN
  BEGIN
    uid := auth.uid();
  EXCEPTION WHEN OTHERS THEN
    uid := NULL;
  END;
  IF uid IS NULL THEN
    BEGIN
      uid := nullif(current_setting('app.current_user_id', true), '')::uuid;
    EXCEPTION WHEN OTHERS THEN
      uid := NULL;
    END;
  END IF;
  RETURN uid;
END
$$;

-- Provider-confidential access: provider match (area-limited when the scope sets
-- an area) OR agent/outlet combined context. A NULL provider scope is NEVER a
-- wildcard (docs §13.16, §6.6).
CREATE OR REPLACE FUNCTION app.has_provider_scope(p_provider uuid, p_outlet uuid)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, app, auth, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM user_access_scopes s
    LEFT JOIN outlets o ON o.outlet_id = p_outlet
    WHERE s.user_id = app.current_user_id()
      AND (
        (s.provider_id IS NOT NULL AND s.provider_id = p_provider
          AND (s.area_id IS NULL OR s.area_id = o.area_id))
        OR
        (s.outlet_id IS NOT NULL AND s.outlet_id = p_outlet)
      )
  );
$$;

-- Shared-cash / outlet access: outlet scope, area scope, or a provider scope that
-- actually holds an account at that outlet. Never a bare provider wildcard.
CREATE OR REPLACE FUNCTION app.has_outlet_scope(p_outlet uuid)
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, app, auth, pg_temp
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM user_access_scopes s
    LEFT JOIN outlets o ON o.outlet_id = p_outlet
    WHERE s.user_id = app.current_user_id()
      AND (
        (s.outlet_id IS NOT NULL AND s.outlet_id = p_outlet)
        OR (s.area_id IS NOT NULL AND s.area_id = o.area_id)
        OR (s.provider_id IS NOT NULL AND EXISTS (
              SELECT 1 FROM outlet_provider_accounts opa
              WHERE opa.outlet_id = p_outlet AND opa.provider_id = s.provider_id))
      )
  );
$$;

-- Parent-resolving helpers (SECURITY DEFINER => no RLS recursion).
CREATE OR REPLACE FUNCTION app.has_assessment_access(p_assessment uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, app, auth, pg_temp AS $$
  SELECT app.has_provider_scope(d.provider_id, d.outlet_id)
  FROM data_quality_assessments d WHERE d.data_quality_assessment_id = p_assessment;
$$;

CREATE OR REPLACE FUNCTION app.has_projection_access(p_projection uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, app, auth, pg_temp AS $$
  SELECT CASE WHEN lp.reserve_type = 'shared_cash'
              THEN app.has_outlet_scope(lp.outlet_id)
              ELSE app.has_provider_scope(lp.provider_id, lp.outlet_id) END
  FROM liquidity_projections lp WHERE lp.liquidity_projection_id = p_projection;
$$;

CREATE OR REPLACE FUNCTION app.has_flag_access(p_flag uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, app, auth, pg_temp AS $$
  SELECT app.has_provider_scope(f.provider_id, f.outlet_id)
  FROM anomaly_flags f WHERE f.anomaly_flag_id = p_flag;
$$;

CREATE OR REPLACE FUNCTION app.has_alert_access(p_alert uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, app, auth, pg_temp AS $$
  SELECT CASE WHEN a.provider_id IS NULL
              THEN app.has_outlet_scope(a.outlet_id)
              ELSE app.has_provider_scope(a.provider_id, a.outlet_id) END
  FROM alerts a WHERE a.alert_id = p_alert;
$$;

CREATE OR REPLACE FUNCTION app.has_case_access(p_case uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, app, auth, pg_temp AS $$
  SELECT CASE WHEN c.provider_id IS NULL
              THEN app.has_outlet_scope(c.outlet_id)
              ELSE app.has_provider_scope(c.provider_id, c.outlet_id) END
  FROM cases c WHERE c.case_id = p_case;
$$;

CREATE OR REPLACE FUNCTION app.has_batch_access(p_batch uuid)
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, app, auth, pg_temp AS $$
  SELECT app.has_provider_scope(b.provider_id, b.outlet_id)
  FROM ingestion_batches b WHERE b.ingestion_batch_id = p_batch;
$$;

-- =============================================================================
-- Grants — least privilege
-- =============================================================================
GRANT USAGE ON SCHEMA public, app, auth TO anon, authenticated, service_role;

-- service_role: full access (and BYPASSRLS).
GRANT ALL ON ALL TABLES    IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- authenticated: read-only through RLS on confidential tables + reference reads.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;

-- anon: only non-confidential simulated reference data.
GRANT SELECT ON providers, areas, simulation_scenarios, anomaly_rules,
                routing_rules, explanation_templates TO anon;

-- Policy/helper functions must be executable by the roles that hit RLS.
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO anon, authenticated, service_role;

-- =============================================================================
-- Enable RLS + SELECT policies (provider/outlet/area scoped)
-- =============================================================================

-- Own identity/scope visibility.
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_app_users ON app_users FOR SELECT TO authenticated
  USING (user_id = app.current_user_id());

ALTER TABLE user_access_scopes ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_user_access_scopes ON user_access_scopes FOR SELECT TO authenticated
  USING (user_id = app.current_user_id());

-- Provider-confidential rows (provider_id + outlet_id present).
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_transactions ON transactions FOR SELECT TO authenticated
  USING (app.has_provider_scope(provider_id, outlet_id));

ALTER TABLE provider_balance_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_pbs ON provider_balance_snapshots FOR SELECT TO authenticated
  USING (app.has_provider_scope(provider_id, outlet_id));

ALTER TABLE data_quality_assessments ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_dqa ON data_quality_assessments FOR SELECT TO authenticated
  USING (app.has_provider_scope(provider_id, outlet_id));

ALTER TABLE anomaly_flags ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_anomaly_flags ON anomaly_flags FOR SELECT TO authenticated
  USING (app.has_provider_scope(provider_id, outlet_id));

ALTER TABLE ingestion_batches ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_ingestion_batches ON ingestion_batches FOR SELECT TO authenticated
  USING (app.has_provider_scope(provider_id, outlet_id));

-- Outlet-only shared-cash rows (no provider column).
ALTER TABLE cash_balance_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_cash ON cash_balance_snapshots FOR SELECT TO authenticated
  USING (app.has_outlet_scope(outlet_id));

-- Mixed reserve rows.
ALTER TABLE liquidity_projections ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_lp ON liquidity_projections FOR SELECT TO authenticated
  USING (CASE WHEN reserve_type = 'shared_cash'
              THEN app.has_outlet_scope(outlet_id)
              ELSE app.has_provider_scope(provider_id, outlet_id) END);

-- Nullable-provider rows (shared-cash scoped when provider is null).
ALTER TABLE fault_injections ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_fault_injections ON fault_injections FOR SELECT TO authenticated
  USING (CASE WHEN provider_id IS NULL
              THEN app.has_outlet_scope(outlet_id)
              ELSE app.has_provider_scope(provider_id, outlet_id) END);

ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_alerts ON alerts FOR SELECT TO authenticated
  USING (CASE WHEN provider_id IS NULL
              THEN app.has_outlet_scope(outlet_id)
              ELSE app.has_provider_scope(provider_id, outlet_id) END);

ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_cases ON cases FOR SELECT TO authenticated
  USING (CASE WHEN provider_id IS NULL
              THEN app.has_outlet_scope(outlet_id)
              ELSE app.has_provider_scope(provider_id, outlet_id) END);

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_audit_events ON audit_events FOR SELECT TO authenticated
  USING (
    (provider_id IS NOT NULL AND app.has_provider_scope(provider_id, outlet_id))
    OR (provider_id IS NULL AND outlet_id IS NOT NULL AND app.has_outlet_scope(outlet_id))
  );

-- Child/evidence tables resolved through their parent's scope.
ALTER TABLE ingestion_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_ingestion_events ON ingestion_events FOR SELECT TO authenticated
  USING (app.has_batch_access(ingestion_batch_id));

ALTER TABLE data_quality_issues ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_dqi ON data_quality_issues FOR SELECT TO authenticated
  USING (app.has_assessment_access(data_quality_assessment_id));

ALTER TABLE liquidity_signals ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_lsig ON liquidity_signals FOR SELECT TO authenticated
  USING (app.has_projection_access(liquidity_projection_id));

ALTER TABLE liquidity_projection_quality_assessments ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_lpqa ON liquidity_projection_quality_assessments FOR SELECT TO authenticated
  USING (app.has_projection_access(liquidity_projection_id));

ALTER TABLE anomaly_evidence_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_aei ON anomaly_evidence_items FOR SELECT TO authenticated
  USING (app.has_flag_access(anomaly_flag_id));

ALTER TABLE anomaly_flag_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_aft ON anomaly_flag_transactions FOR SELECT TO authenticated
  USING (app.has_flag_access(anomaly_flag_id));

ALTER TABLE alert_liquidity_projections ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_alp ON alert_liquidity_projections FOR SELECT TO authenticated
  USING (app.has_alert_access(alert_id));

ALTER TABLE alert_anomaly_flags ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_aaf ON alert_anomaly_flags FOR SELECT TO authenticated
  USING (app.has_alert_access(alert_id));

ALTER TABLE alert_quality_assessments ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_aqa ON alert_quality_assessments FOR SELECT TO authenticated
  USING (app.has_alert_access(alert_id));

ALTER TABLE alert_explanations ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_alert_explanations ON alert_explanations FOR SELECT TO authenticated
  USING (app.has_alert_access(alert_id));

ALTER TABLE case_assignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_case_assignments ON case_assignments FOR SELECT TO authenticated
  USING (app.has_case_access(case_id));

ALTER TABLE case_status_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_case_status_history ON case_status_history FOR SELECT TO authenticated
  USING (app.has_case_access(case_id));

ALTER TABLE case_notes ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_case_notes ON case_notes FOR SELECT TO authenticated
  USING (app.has_case_access(case_id));

ALTER TABLE case_reviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_case_reviews ON case_reviews FOR SELECT TO authenticated
  USING (app.has_case_access(case_id));

ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_notifications ON notifications FOR SELECT TO authenticated
  USING (recipient_user_id = app.current_user_id() OR app.has_case_access(case_id));

-- Analytics/simulation envelope rows are non-provider-confidential metadata but
-- gated to authenticated (service writes them). Enable RLS with permissive read.
ALTER TABLE analytics_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_analytics_runs ON analytics_runs FOR SELECT TO authenticated USING (true);

ALTER TABLE simulation_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY sel_simulation_runs ON simulation_runs FOR SELECT TO authenticated USING (true);
