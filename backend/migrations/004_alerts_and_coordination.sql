-- =============================================================================
-- Migration 004 — Alerts and Coordination
-- Source of truth: docs/schema.md §10 (alerts/cases), §13 (invariants 11-16).
-- Alerts hold immutable analytical content; cases hold the mutable human
-- workflow. Every active/published alert must cite >=1 analytical/quality source
-- (deferred constraint, ADR 0005). No table authorizes any financial/punitive
-- action.
-- =============================================================================

-- =============================================================================
-- 10.1 alerts — immutable analytical content (only lifecycle metadata mutable)
-- =============================================================================
CREATE TABLE alerts (
  alert_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  simulation_run_id   uuid NOT NULL REFERENCES simulation_runs(simulation_run_id),
  outlet_id           uuid NOT NULL REFERENCES outlets(outlet_id),
  provider_id         uuid REFERENCES providers(provider_id),   -- NULL only for shared-cash alert
  alert_type          alert_type NOT NULL,
  severity            severity NOT NULL,
  state               alert_state NOT NULL DEFAULT 'active',
  deduplication_key   text NOT NULL,
  title_key           text NOT NULL,
  structured_payload  jsonb NOT NULL DEFAULT '{}'::jsonb,
  requires_case       boolean NOT NULL,
  detected_at         timestamptz NOT NULL,
  created_at          timestamptz NOT NULL DEFAULT now(),
  supersedes_alert_id uuid REFERENCES alerts(alert_id)
);

-- One active alert per condition/window (docs §10.1).
CREATE UNIQUE INDEX uq_alerts_active_dedup
  ON alerts (deduplication_key) WHERE state = 'active';

-- Published-alert immutability: only state / supersedes_alert_id may change; no delete.
CREATE OR REPLACE FUNCTION enforce_alert_immutability() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'alerts are immutable evidence and cannot be deleted (alert_id=%)', OLD.alert_id
      USING ERRCODE = 'restrict_violation';
  END IF;
  IF NEW.simulation_run_id  IS DISTINCT FROM OLD.simulation_run_id
     OR NEW.outlet_id       IS DISTINCT FROM OLD.outlet_id
     OR NEW.provider_id     IS DISTINCT FROM OLD.provider_id
     OR NEW.alert_type      IS DISTINCT FROM OLD.alert_type
     OR NEW.severity        IS DISTINCT FROM OLD.severity
     OR NEW.deduplication_key IS DISTINCT FROM OLD.deduplication_key
     OR NEW.title_key       IS DISTINCT FROM OLD.title_key
     OR NEW.structured_payload IS DISTINCT FROM OLD.structured_payload
     OR NEW.requires_case   IS DISTINCT FROM OLD.requires_case
     OR NEW.detected_at     IS DISTINCT FROM OLD.detected_at
     OR NEW.created_at      IS DISTINCT FROM OLD.created_at THEN
    RAISE EXCEPTION 'published alert analytical content is immutable (alert_id=%); only state/supersedes may change', OLD.alert_id
      USING ERRCODE = 'restrict_violation';
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER trg_alert_immutability
  BEFORE UPDATE OR DELETE ON alerts FOR EACH ROW EXECUTE FUNCTION enforce_alert_immutability();

-- =============================================================================
-- 10.2 Alert source-link tables (no polymorphic FKs)
-- =============================================================================
CREATE TABLE alert_liquidity_projections (
  alert_id                uuid NOT NULL REFERENCES alerts(alert_id),
  liquidity_projection_id uuid NOT NULL REFERENCES liquidity_projections(liquidity_projection_id),
  PRIMARY KEY (alert_id, liquidity_projection_id)
);

CREATE TABLE alert_anomaly_flags (
  alert_id        uuid NOT NULL REFERENCES alerts(alert_id),
  anomaly_flag_id uuid NOT NULL REFERENCES anomaly_flags(anomaly_flag_id),
  PRIMARY KEY (alert_id, anomaly_flag_id)
);

CREATE TABLE alert_quality_assessments (
  alert_id                   uuid NOT NULL REFERENCES alerts(alert_id),
  data_quality_assessment_id uuid NOT NULL REFERENCES data_quality_assessments(data_quality_assessment_id),
  PRIMARY KEY (alert_id, data_quality_assessment_id)
);

-- A suppressed anomaly flag cannot back an anomaly/combined alert (docs §10.2, §13.10).
CREATE OR REPLACE FUNCTION enforce_no_suppressed_anomaly_link() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  a_type alert_type;
  disp   anomaly_disposition;
BEGIN
  SELECT alert_type INTO a_type FROM alerts        WHERE alert_id = NEW.alert_id;
  SELECT disposition INTO disp  FROM anomaly_flags  WHERE anomaly_flag_id = NEW.anomaly_flag_id;
  IF disp = 'suppressed_data_quality' AND a_type IN ('anomaly','combined') THEN
    RAISE EXCEPTION 'suppressed anomaly flag % cannot be linked to a %-type alert',
      NEW.anomaly_flag_id, a_type USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER trg_aaf_no_suppressed_link
  BEFORE INSERT ON alert_anomaly_flags FOR EACH ROW EXECUTE FUNCTION enforce_no_suppressed_anomaly_link();

-- Every alert cites >=1 source across the three link tables (deferred, ADR 0005).
CREATE OR REPLACE FUNCTION enforce_alert_has_source() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  n int;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM alerts WHERE alert_id = NEW.alert_id) THEN
    RETURN NULL;  -- alert removed within the same tx; nothing to validate
  END IF;
  SELECT
      (SELECT count(*) FROM alert_liquidity_projections WHERE alert_id = NEW.alert_id)
    + (SELECT count(*) FROM alert_anomaly_flags         WHERE alert_id = NEW.alert_id)
    + (SELECT count(*) FROM alert_quality_assessments   WHERE alert_id = NEW.alert_id)
  INTO n;
  IF n = 0 THEN
    RAISE EXCEPTION 'alert % must cite at least one projection, anomaly flag, or data-quality assessment (docs §13.11)', NEW.alert_id
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NULL;
END
$$;
CREATE CONSTRAINT TRIGGER trg_alert_has_source
  AFTER INSERT OR UPDATE ON alerts
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION enforce_alert_has_source();

-- =============================================================================
-- 10.3 explanation_templates
-- =============================================================================
CREATE TABLE explanation_templates (
  explanation_template_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  template_key            text NOT NULL,
  locale                  locale_code NOT NULL,
  version                 integer NOT NULL CHECK (version > 0),
  alert_type              alert_type NOT NULL,
  situation_template      text NOT NULL,
  evidence_template       text NOT NULL,
  uncertainty_template    text NOT NULL,
  next_step_template      text NOT NULL,
  benign_context_template text,
  is_active               boolean NOT NULL DEFAULT true,
  created_at              timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_template_key_locale_version UNIQUE (template_key, locale, version)
);

-- =============================================================================
-- 10.4 alert_explanations — immutable render snapshot
-- =============================================================================
CREATE TABLE alert_explanations (
  alert_explanation_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id                uuid NOT NULL REFERENCES alerts(alert_id),
  explanation_template_id uuid NOT NULL REFERENCES explanation_templates(explanation_template_id),
  locale                  locale_code NOT NULL,
  situation_text          text NOT NULL,
  evidence_text           text NOT NULL,
  uncertainty_text        text NOT NULL,
  next_step_text          text NOT NULL,
  benign_context_text     text,
  rendered_at             timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_explanation_alert_locale UNIQUE (alert_id, locale)
);

-- Anomaly/combined alerts require a benign-context render (docs §10.4).
CREATE OR REPLACE FUNCTION enforce_explanation_benign_context() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  a_type alert_type;
BEGIN
  SELECT alert_type INTO a_type FROM alerts WHERE alert_id = NEW.alert_id;
  IF a_type IN ('anomaly','combined') AND NEW.benign_context_text IS NULL THEN
    RAISE EXCEPTION 'benign_context_text is required for %-type alert explanations (alert_id=%)',
      a_type, NEW.alert_id USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER trg_explanation_benign_context
  BEFORE INSERT ON alert_explanations FOR EACH ROW EXECUTE FUNCTION enforce_explanation_benign_context();
CREATE TRIGGER trg_explanation_append_only
  BEFORE UPDATE OR DELETE ON alert_explanations FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 10.5 routing_rules
-- =============================================================================
CREATE TABLE routing_rules (
  routing_rule_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name             text NOT NULL,
  provider_id      uuid REFERENCES providers(provider_id),  -- NULL = fallback/shared cash
  area_id          uuid REFERENCES areas(area_id),
  alert_type       alert_type,                              -- NULL = wildcard
  minimum_severity severity NOT NULL,
  target_role      app_role NOT NULL,
  priority         integer NOT NULL DEFAULT 100,            -- lower wins
  is_active        boolean NOT NULL DEFAULT true,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_routing_rules_updated_at
  BEFORE UPDATE ON routing_rules FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 10.6 cases — mutable current workflow state
-- =============================================================================
CREATE TABLE cases (
  case_id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_number           text NOT NULL UNIQUE,
  alert_id              uuid NOT NULL UNIQUE REFERENCES alerts(alert_id),
  outlet_id             uuid NOT NULL REFERENCES outlets(outlet_id),
  provider_id           uuid REFERENCES providers(provider_id),
  routing_rule_id       uuid REFERENCES routing_rules(routing_rule_id),
  status                case_status NOT NULL DEFAULT 'open',
  current_owner_user_id uuid REFERENCES app_users(user_id),
  current_owner_role    app_role NOT NULL,
  recommended_next_step text NOT NULL,
  opened_at             timestamptz NOT NULL DEFAULT now(),
  acknowledged_at       timestamptz,
  escalated_at          timestamptz,
  resolved_at           timestamptz,
  resolution_summary    text,
  version               integer NOT NULL DEFAULT 1,
  updated_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT case_resolved_needs_summary CHECK (
    status <> 'resolved' OR (resolution_summary IS NOT NULL AND resolved_at IS NOT NULL)
  )
);
CREATE TRIGGER trg_cases_updated_at
  BEFORE UPDATE ON cases FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Case scope must match its source alert (docs §10.6, §13.13).
CREATE OR REPLACE FUNCTION enforce_case_scope_matches_alert() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  a_outlet   uuid;
  a_provider uuid;
BEGIN
  SELECT outlet_id, provider_id INTO a_outlet, a_provider FROM alerts WHERE alert_id = NEW.alert_id;
  IF NEW.outlet_id <> a_outlet OR NEW.provider_id IS DISTINCT FROM a_provider THEN
    RAISE EXCEPTION 'case scope (outlet=%, provider=%) does not match alert scope (outlet=%, provider=%)',
      NEW.outlet_id, NEW.provider_id, a_outlet, a_provider USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER trg_case_scope_matches_alert
  BEFORE INSERT OR UPDATE ON cases FOR EACH ROW EXECUTE FUNCTION enforce_case_scope_matches_alert();

-- Legal case-status transitions only (docs §10.6). No reopening.
CREATE OR REPLACE FUNCTION enforce_case_transition() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status IS DISTINCT FROM OLD.status THEN
    IF NOT (
      (OLD.status = 'open'         AND NEW.status IN ('acknowledged','escalated')) OR
      (OLD.status = 'acknowledged' AND NEW.status IN ('escalated','resolved'))     OR
      (OLD.status = 'escalated'    AND NEW.status = 'resolved')
    ) THEN
      RAISE EXCEPTION 'illegal case transition % -> % (case_id=%)', OLD.status, NEW.status, OLD.case_id
        USING ERRCODE = 'check_violation';
    END IF;
  END IF;
  RETURN NEW;
END
$$;
CREATE TRIGGER trg_case_transition
  BEFORE UPDATE ON cases FOR EACH ROW EXECUTE FUNCTION enforce_case_transition();

-- =============================================================================
-- 10.7 case_assignments — append-only
-- =============================================================================
CREATE TABLE case_assignments (
  case_assignment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id            uuid NOT NULL REFERENCES cases(case_id),
  assigned_to_user_id uuid REFERENCES app_users(user_id),
  assigned_to_role   app_role NOT NULL,
  assigned_by_user_id uuid REFERENCES app_users(user_id),
  reason             assignment_reason NOT NULL,
  routing_rule_id    uuid REFERENCES routing_rules(routing_rule_id),
  comment            text,
  assigned_at        timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_case_assignments_append_only
  BEFORE UPDATE OR DELETE ON case_assignments FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 10.8 case_status_history — append-only
-- =============================================================================
CREATE TABLE case_status_history (
  case_status_history_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id            uuid NOT NULL REFERENCES cases(case_id),
  from_status        case_status,   -- NULL only for initial creation
  to_status          case_status NOT NULL,
  changed_by_user_id uuid REFERENCES app_users(user_id),
  reason             text,
  changed_at         timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_case_status_history_append_only
  BEFORE UPDATE OR DELETE ON case_status_history FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 10.9 case_notes — append-only
-- =============================================================================
CREATE TABLE case_notes (
  case_note_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id        uuid NOT NULL REFERENCES cases(case_id),
  author_user_id uuid NOT NULL REFERENCES app_users(user_id),
  note_text      text NOT NULL,
  note_type      text NOT NULL CHECK (note_type IN ('general','contact_attempt','evidence','resolution')),
  created_at     timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_case_notes_append_only
  BEFORE UPDATE OR DELETE ON case_notes FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 10.10 notifications (mutable delivery state)
-- =============================================================================
CREATE TABLE notifications (
  notification_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id            uuid NOT NULL REFERENCES cases(case_id),
  recipient_user_id  uuid REFERENCES app_users(user_id),
  recipient_role     app_role NOT NULL,
  channel            notification_channel NOT NULL DEFAULT 'in_app',
  status             notification_status NOT NULL DEFAULT 'queued',
  payload            jsonb NOT NULL DEFAULT '{}'::jsonb,
  queued_at          timestamptz NOT NULL DEFAULT now(),
  delivered_at       timestamptz,
  read_at            timestamptz,
  failure_reason     text
);

-- =============================================================================
-- 10.11 case_reviews (advisory; never a fraud verdict)
-- =============================================================================
CREATE TABLE case_reviews (
  case_review_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id             uuid NOT NULL UNIQUE REFERENCES cases(case_id),
  reviewed_by_user_id uuid NOT NULL REFERENCES app_users(user_id),
  disposition         review_outcome NOT NULL,
  was_false_positive  boolean,
  review_summary      text NOT NULL,
  reviewed_at         timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- 10.12 audit_events — strictly append-only
-- =============================================================================
CREATE TABLE audit_events (
  audit_event_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id         uuid REFERENCES cases(case_id),
  alert_id        uuid REFERENCES alerts(alert_id),
  provider_id     uuid REFERENCES providers(provider_id),
  outlet_id       uuid REFERENCES outlets(outlet_id),
  actor_user_id   uuid REFERENCES app_users(user_id),
  actor_type      text NOT NULL CHECK (actor_type IN ('user','routing_engine','analytics_engine','system')),
  action          text NOT NULL,
  entity_type     text,
  entity_id       uuid,
  previous_values jsonb,
  new_values      jsonb,
  request_id      text,
  occurred_at     timestamptz NOT NULL DEFAULT now(),
  hash            text
);
CREATE TRIGGER trg_audit_events_append_only
  BEFORE UPDATE OR DELETE ON audit_events FOR EACH ROW EXECUTE FUNCTION reject_mutation();
