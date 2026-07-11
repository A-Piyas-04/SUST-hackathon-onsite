-- =============================================================================
-- Migration 003 — Quality and Intelligence
-- Source of truth: docs/schema.md §9 (quality/analytics), §13 (invariants 8-10).
-- Adds reserve-XOR, confidence/sample constraints, provider-crossing evidence
-- protection, and append-only guards for analytical evidence.
-- =============================================================================

-- =============================================================================
-- 9.1 data_quality_assessments — append-only
-- =============================================================================
CREATE TABLE data_quality_assessments (
  data_quality_assessment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  simulation_run_id          uuid NOT NULL REFERENCES simulation_runs(simulation_run_id),
  ingestion_batch_id         uuid REFERENCES ingestion_batches(ingestion_batch_id),
  outlet_id                  uuid NOT NULL REFERENCES outlets(outlet_id),
  provider_id                uuid NOT NULL REFERENCES providers(provider_id),
  status                     feed_health_status NOT NULL,
  confidence_modifier        score_unit NOT NULL,
  sample_count               integer NOT NULL CHECK (sample_count >= 0),
  latest_source_at           timestamptz,
  assessed_at                timestamptz NOT NULL,
  engine_version             text NOT NULL,
  summary                    text,
  created_at                 timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_dqa_append_only
  BEFORE UPDATE OR DELETE ON data_quality_assessments FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 9.2 data_quality_issues
-- =============================================================================
CREATE TABLE data_quality_issues (
  data_quality_issue_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  data_quality_assessment_id uuid NOT NULL REFERENCES data_quality_assessments(data_quality_assessment_id),
  issue_type                 quality_issue_type NOT NULL,
  severity                   severity NOT NULL,
  field_name                 text,
  evidence                   jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at                 timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- 9.3 analytics_runs — common reproducibility envelope
-- =============================================================================
CREATE TABLE analytics_runs (
  analytics_run_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  simulation_run_id  uuid NOT NULL REFERENCES simulation_runs(simulation_run_id),
  engine             analytics_engine NOT NULL,
  engine_version     text NOT NULL,
  configuration      jsonb NOT NULL DEFAULT '{}'::jsonb,
  input_window_start timestamptz NOT NULL,
  input_window_end   timestamptz NOT NULL,
  status             text NOT NULL DEFAULT 'running'
                       CHECK (status IN ('running','completed','failed')),
  started_at         timestamptz NOT NULL DEFAULT now(),
  completed_at       timestamptz,
  error_summary      text
);

-- =============================================================================
-- 9.4 liquidity_projections — append-only
-- Reserve XOR (docs §9.4/§13.3): shared_cash => both provider cols NULL;
-- provider_e_money => both set (and match the account, enforced by trigger).
-- =============================================================================
CREATE TABLE liquidity_projections (
  liquidity_projection_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analytics_run_id                   uuid NOT NULL REFERENCES analytics_runs(analytics_run_id),
  outlet_id                          uuid NOT NULL REFERENCES outlets(outlet_id),
  reserve_type                       reserve_type NOT NULL,
  outlet_provider_account_id         uuid REFERENCES outlet_provider_accounts(outlet_provider_account_id),
  provider_id                        uuid REFERENCES providers(provider_id),
  primary_data_quality_assessment_id uuid REFERENCES data_quality_assessments(data_quality_assessment_id),
  as_of_at                           timestamptz NOT NULL,
  current_balance                    numeric(18,2) NOT NULL CHECK (current_balance >= 0),
  burn_rate_per_hour                 numeric(18,4) NOT NULL,
  projected_shortage_at              timestamptz,
  lower_bound_at                     timestamptz,
  upper_bound_at                     timestamptz,
  confidence_score                   score_unit NOT NULL,
  confidence_level                   confidence_level NOT NULL,
  sample_count                       integer NOT NULL CHECK (sample_count >= 0),
  is_actionable                      boolean NOT NULL,
  non_actionable_reason              text,
  created_at                         timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT lp_reserve_xor CHECK (
    (reserve_type = 'shared_cash'
       AND provider_id IS NULL AND outlet_provider_account_id IS NULL)
    OR
    (reserve_type = 'provider_e_money'
       AND provider_id IS NOT NULL AND outlet_provider_account_id IS NOT NULL)
  ),
  CONSTRAINT lp_nonpositive_burn_no_shortage CHECK (
    burn_rate_per_hour > 0
      OR (projected_shortage_at IS NULL AND lower_bound_at IS NULL AND upper_bound_at IS NULL)
  ),
  CONSTRAINT lp_nonactionable_reason CHECK (
    is_actionable OR non_actionable_reason IS NOT NULL
  )
);

-- provider_e_money projection: denormalized provider/account identity must agree.
CREATE OR REPLACE FUNCTION enforce_projection_account() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  a_outlet   uuid;
  a_provider uuid;
BEGIN
  IF NEW.reserve_type = 'provider_e_money' THEN
    SELECT outlet_id, provider_id INTO a_outlet, a_provider
    FROM outlet_provider_accounts
    WHERE outlet_provider_account_id = NEW.outlet_provider_account_id;
    IF a_outlet IS NULL THEN
      RAISE EXCEPTION 'unknown outlet_provider_account_id=%', NEW.outlet_provider_account_id
        USING ERRCODE = 'foreign_key_violation';
    END IF;
    IF NEW.provider_id <> a_provider OR NEW.outlet_id <> a_outlet THEN
      RAISE EXCEPTION 'projection provider/outlet (%, %) do not match account % owner (%, %)',
        NEW.provider_id, NEW.outlet_id, NEW.outlet_provider_account_id, a_provider, a_outlet
        USING ERRCODE = 'check_violation';
    END IF;
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER trg_lp_account_consistency
  BEFORE INSERT ON liquidity_projections FOR EACH ROW EXECUTE FUNCTION enforce_projection_account();
CREATE TRIGGER trg_lp_append_only
  BEFORE UPDATE OR DELETE ON liquidity_projections FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 9.5 liquidity_projection_quality_assessments — join
-- =============================================================================
CREATE TABLE liquidity_projection_quality_assessments (
  liquidity_projection_id    uuid NOT NULL REFERENCES liquidity_projections(liquidity_projection_id),
  data_quality_assessment_id uuid NOT NULL REFERENCES data_quality_assessments(data_quality_assessment_id),
  PRIMARY KEY (liquidity_projection_id, data_quality_assessment_id)
);

-- =============================================================================
-- 9.6 liquidity_signals
-- =============================================================================
CREATE TABLE liquidity_signals (
  liquidity_signal_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  liquidity_projection_id uuid NOT NULL REFERENCES liquidity_projections(liquidity_projection_id),
  signal_code             text NOT NULL,
  label                   text NOT NULL,
  numeric_value           numeric,
  unit                    text,
  direction               text NOT NULL
                            CHECK (direction IN ('increases_pressure','reduces_pressure','reduces_confidence')),
  details                 jsonb NOT NULL DEFAULT '{}'::jsonb,
  display_order           integer NOT NULL DEFAULT 0 CHECK (display_order >= 0)
);

-- =============================================================================
-- 9.7 anomaly_rules  (MVP activates only near_identical_amounts; seed in seeds/)
-- =============================================================================
CREATE TABLE anomaly_rules (
  anomaly_rule_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code            text NOT NULL UNIQUE,
  pattern         anomaly_pattern NOT NULL,
  version         text NOT NULL,
  name            text NOT NULL,
  description     text NOT NULL,
  configuration   jsonb NOT NULL DEFAULT '{}'::jsonb,
  is_active       boolean NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_anomaly_rules_updated_at
  BEFORE UPDATE ON anomaly_rules FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 9.8 anomaly_flags — append-only
-- Actionable flags require plausible benign context; suppressed flags require a
-- suppression reason (docs §9.8, §13.9-10).
-- =============================================================================
CREATE TABLE anomaly_flags (
  anomaly_flag_id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analytics_run_id              uuid NOT NULL REFERENCES analytics_runs(analytics_run_id),
  anomaly_rule_id               uuid NOT NULL REFERENCES anomaly_rules(anomaly_rule_id),
  outlet_id                     uuid NOT NULL REFERENCES outlets(outlet_id),
  provider_id                   uuid NOT NULL REFERENCES providers(provider_id),
  outlet_provider_account_id    uuid NOT NULL REFERENCES outlet_provider_accounts(outlet_provider_account_id),
  data_quality_assessment_id    uuid NOT NULL REFERENCES data_quality_assessments(data_quality_assessment_id),
  window_start                  timestamptz NOT NULL,
  window_end                    timestamptz NOT NULL,
  confidence_score              score_unit NOT NULL,
  confidence_level              confidence_level NOT NULL,
  disposition                   anomaly_disposition NOT NULL,
  reason_code                   text NOT NULL,
  evidence_summary              text NOT NULL,
  plausible_benign_explanation  text,
  suppression_reason            text,
  created_at                    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT af_actionable_needs_benign CHECK (
    disposition NOT IN ('requires_review','confirmed_unusual')
      OR plausible_benign_explanation IS NOT NULL
  ),
  CONSTRAINT af_suppressed_needs_reason CHECK (
    disposition <> 'suppressed_data_quality' OR suppression_reason IS NOT NULL
  )
);
CREATE TRIGGER trg_af_account_consistency
  BEFORE INSERT ON anomaly_flags FOR EACH ROW EXECUTE FUNCTION enforce_account_consistency();
CREATE TRIGGER trg_af_append_only
  BEFORE UPDATE OR DELETE ON anomaly_flags FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 9.9 anomaly_evidence_items — append-only structured evidence
-- =============================================================================
CREATE TABLE anomaly_evidence_items (
  anomaly_evidence_item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  anomaly_flag_id          uuid NOT NULL REFERENCES anomaly_flags(anomaly_flag_id),
  evidence_type            text NOT NULL,
  label                    text NOT NULL,
  value                    jsonb NOT NULL DEFAULT '{}'::jsonb,
  display_order            integer NOT NULL DEFAULT 0 CHECK (display_order >= 0),
  created_at               timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_aei_append_only
  BEFORE UPDATE OR DELETE ON anomaly_evidence_items FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 9.10 anomaly_flag_transactions — join; provider-crossing evidence forbidden
-- =============================================================================
CREATE TABLE anomaly_flag_transactions (
  anomaly_flag_id uuid NOT NULL REFERENCES anomaly_flags(anomaly_flag_id),
  transaction_id  uuid NOT NULL REFERENCES transactions(transaction_id),
  PRIMARY KEY (anomaly_flag_id, transaction_id)
);

CREATE OR REPLACE FUNCTION enforce_flag_txn_same_provider() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  f_provider uuid;
  t_provider uuid;
BEGIN
  SELECT provider_id INTO f_provider FROM anomaly_flags   WHERE anomaly_flag_id = NEW.anomaly_flag_id;
  SELECT provider_id INTO t_provider FROM transactions    WHERE transaction_id  = NEW.transaction_id;
  IF f_provider IS DISTINCT FROM t_provider THEN
    RAISE EXCEPTION 'provider-crossing evidence: flag provider % <> transaction provider %',
      f_provider, t_provider USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER trg_aft_same_provider
  BEFORE INSERT ON anomaly_flag_transactions FOR EACH ROW EXECUTE FUNCTION enforce_flag_txn_same_provider();
CREATE TRIGGER trg_aft_append_only
  BEFORE UPDATE OR DELETE ON anomaly_flag_transactions FOR EACH ROW EXECUTE FUNCTION reject_mutation();
