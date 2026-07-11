--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: app; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA app;


--
-- Name: auth; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA auth;


--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: alert_state; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.alert_state AS text
	CONSTRAINT alert_state_check CHECK ((VALUE = ANY (ARRAY['active'::text, 'superseded'::text, 'closed'::text])));


--
-- Name: alert_type; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.alert_type AS text
	CONSTRAINT alert_type_check CHECK ((VALUE = ANY (ARRAY['liquidity'::text, 'anomaly'::text, 'combined'::text, 'data_quality'::text])));


--
-- Name: analytics_engine; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.analytics_engine AS text
	CONSTRAINT analytics_engine_check CHECK ((VALUE = ANY (ARRAY['liquidity'::text, 'anomaly'::text, 'data_quality'::text])));


--
-- Name: anomaly_disposition; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.anomaly_disposition AS text
	CONSTRAINT anomaly_disposition_check CHECK ((VALUE = ANY (ARRAY['requires_review'::text, 'suppressed_data_quality'::text, 'dismissed_benign'::text, 'confirmed_unusual'::text, 'inconclusive'::text])));


--
-- Name: anomaly_pattern; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.anomaly_pattern AS text
	CONSTRAINT anomaly_pattern_check CHECK ((VALUE = ANY (ARRAY['near_identical_amounts'::text, 'velocity_spike'::text, 'transaction_splitting'::text, 'circular_activity'::text, 'balance_inconsistency'::text, 'time_anomaly'::text, 'failure_rate'::text])));


--
-- Name: app_role; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.app_role AS text
	CONSTRAINT app_role_check CHECK ((VALUE = ANY (ARRAY['agent'::text, 'field_officer'::text, 'area_manager'::text, 'provider_ops'::text, 'risk_analyst'::text, 'management'::text, 'admin'::text])));


--
-- Name: area_level; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.area_level AS text
	CONSTRAINT area_level_check CHECK ((VALUE = ANY (ARRAY['territory'::text, 'area'::text, 'thana'::text, 'district'::text, 'region'::text])));


--
-- Name: assignment_reason; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.assignment_reason AS text
	CONSTRAINT assignment_reason_check CHECK ((VALUE = ANY (ARRAY['initial_route'::text, 'manual_assign'::text, 'reassign'::text, 'escalation'::text])));


--
-- Name: case_status; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.case_status AS text
	CONSTRAINT case_status_check CHECK ((VALUE = ANY (ARRAY['open'::text, 'acknowledged'::text, 'escalated'::text, 'resolved'::text])));


--
-- Name: confidence_level; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.confidence_level AS text
	CONSTRAINT confidence_level_check CHECK ((VALUE = ANY (ARRAY['high'::text, 'medium'::text, 'low'::text, 'unavailable'::text])));


--
-- Name: currency_bdt; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.currency_bdt AS character(3)
	CONSTRAINT currency_bdt_check CHECK ((VALUE = 'BDT'::bpchar));


--
-- Name: fault_type; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.fault_type AS text
	CONSTRAINT fault_type_check CHECK ((VALUE = ANY (ARRAY['delay'::text, 'missing_feed'::text, 'missing_field'::text, 'conflicting_balance'::text, 'malformed_payload'::text])));


--
-- Name: feed_event_type; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.feed_event_type AS text
	CONSTRAINT feed_event_type_check CHECK ((VALUE = ANY (ARRAY['transaction'::text, 'provider_balance'::text, 'cash_balance'::text, 'heartbeat'::text])));


--
-- Name: feed_health_status; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.feed_health_status AS text
	CONSTRAINT feed_health_status_check CHECK ((VALUE = ANY (ARRAY['fresh'::text, 'stale'::text, 'missing'::text, 'conflicting'::text])));


--
-- Name: locale_code; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.locale_code AS text
	CONSTRAINT locale_code_check CHECK ((VALUE = ANY (ARRAY['en'::text, 'bn'::text, 'bn_latn'::text])));


--
-- Name: normalization_status; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.normalization_status AS text
	CONSTRAINT normalization_status_check CHECK ((VALUE = ANY (ARRAY['pending'::text, 'normalized'::text, 'rejected'::text])));


--
-- Name: notification_channel; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.notification_channel AS text
	CONSTRAINT notification_channel_check CHECK ((VALUE = ANY (ARRAY['in_app'::text, 'webhook'::text, 'email_stub'::text])));


--
-- Name: notification_status; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.notification_status AS text
	CONSTRAINT notification_status_check CHECK ((VALUE = ANY (ARRAY['queued'::text, 'delivered'::text, 'read'::text, 'failed'::text])));


--
-- Name: provider_code; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.provider_code AS text
	CONSTRAINT provider_code_check CHECK ((VALUE = ANY (ARRAY['bkash'::text, 'nagad'::text, 'rocket'::text])));


--
-- Name: quality_issue_type; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.quality_issue_type AS text
	CONSTRAINT quality_issue_type_check CHECK ((VALUE = ANY (ARRAY['late_arrival'::text, 'missing_feed'::text, 'missing_field'::text, 'conflicting_snapshot'::text, 'impossible_transition'::text, 'insufficient_samples'::text, 'malformed_payload'::text])));


--
-- Name: reserve_type; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.reserve_type AS text
	CONSTRAINT reserve_type_check CHECK ((VALUE = ANY (ARRAY['shared_cash'::text, 'provider_e_money'::text])));


--
-- Name: review_outcome; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.review_outcome AS text
	CONSTRAINT review_outcome_check CHECK ((VALUE = ANY (ARRAY['benign_operational'::text, 'requires_follow_up'::text, 'data_quality_issue'::text, 'confirmed_unusual'::text, 'inconclusive'::text])));


--
-- Name: score_unit; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.score_unit AS numeric(5,4)
	CONSTRAINT score_unit_check CHECK (((VALUE >= (0)::numeric) AND (VALUE <= (1)::numeric)));


--
-- Name: severity; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.severity AS text
	CONSTRAINT severity_check CHECK ((VALUE = ANY (ARRAY['info'::text, 'low'::text, 'medium'::text, 'high'::text, 'critical'::text])));


--
-- Name: transaction_status; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.transaction_status AS text
	CONSTRAINT transaction_status_check CHECK ((VALUE = ANY (ARRAY['pending'::text, 'completed'::text, 'failed'::text, 'reversed'::text])));


--
-- Name: transaction_type; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.transaction_type AS text
	CONSTRAINT transaction_type_check CHECK ((VALUE = ANY (ARRAY['cash_in'::text, 'cash_out'::text, 'payment'::text, 'refund'::text, 'adjustment'::text])));


--
-- Name: validation_split; Type: DOMAIN; Schema: public; Owner: -
--

CREATE DOMAIN public.validation_split AS text
	CONSTRAINT validation_split_check CHECK ((VALUE = ANY (ARRAY['tuning'::text, 'held_out'::text, 'demo'::text])));


--
-- Name: current_user_id(); Type: FUNCTION; Schema: app; Owner: -
--

CREATE FUNCTION app.current_user_id() RETURNS uuid
    LANGUAGE plpgsql STABLE
    SET search_path TO 'public', 'app', 'auth', 'pg_temp'
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


--
-- Name: has_alert_access(uuid); Type: FUNCTION; Schema: app; Owner: -
--

CREATE FUNCTION app.has_alert_access(p_alert uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO 'public', 'app', 'auth', 'pg_temp'
    AS $$
  SELECT CASE WHEN a.provider_id IS NULL
              THEN app.has_outlet_scope(a.outlet_id)
              ELSE app.has_provider_scope(a.provider_id, a.outlet_id) END
  FROM alerts a WHERE a.alert_id = p_alert;
$$;


--
-- Name: has_assessment_access(uuid); Type: FUNCTION; Schema: app; Owner: -
--

CREATE FUNCTION app.has_assessment_access(p_assessment uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO 'public', 'app', 'auth', 'pg_temp'
    AS $$
  SELECT app.has_provider_scope(d.provider_id, d.outlet_id)
  FROM data_quality_assessments d WHERE d.data_quality_assessment_id = p_assessment;
$$;


--
-- Name: has_batch_access(uuid); Type: FUNCTION; Schema: app; Owner: -
--

CREATE FUNCTION app.has_batch_access(p_batch uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO 'public', 'app', 'auth', 'pg_temp'
    AS $$
  SELECT app.has_provider_scope(b.provider_id, b.outlet_id)
  FROM ingestion_batches b WHERE b.ingestion_batch_id = p_batch;
$$;


--
-- Name: has_case_access(uuid); Type: FUNCTION; Schema: app; Owner: -
--

CREATE FUNCTION app.has_case_access(p_case uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO 'public', 'app', 'auth', 'pg_temp'
    AS $$
  SELECT CASE WHEN c.provider_id IS NULL
              THEN app.has_outlet_scope(c.outlet_id)
              ELSE app.has_provider_scope(c.provider_id, c.outlet_id) END
  FROM cases c WHERE c.case_id = p_case;
$$;


--
-- Name: has_flag_access(uuid); Type: FUNCTION; Schema: app; Owner: -
--

CREATE FUNCTION app.has_flag_access(p_flag uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO 'public', 'app', 'auth', 'pg_temp'
    AS $$
  SELECT app.has_provider_scope(f.provider_id, f.outlet_id)
  FROM anomaly_flags f WHERE f.anomaly_flag_id = p_flag;
$$;


--
-- Name: has_outlet_scope(uuid); Type: FUNCTION; Schema: app; Owner: -
--

CREATE FUNCTION app.has_outlet_scope(p_outlet uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO 'public', 'app', 'auth', 'pg_temp'
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


--
-- Name: has_projection_access(uuid); Type: FUNCTION; Schema: app; Owner: -
--

CREATE FUNCTION app.has_projection_access(p_projection uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO 'public', 'app', 'auth', 'pg_temp'
    AS $$
  SELECT CASE WHEN lp.reserve_type = 'shared_cash'
              THEN app.has_outlet_scope(lp.outlet_id)
              ELSE app.has_provider_scope(lp.provider_id, lp.outlet_id) END
  FROM liquidity_projections lp WHERE lp.liquidity_projection_id = p_projection;
$$;


--
-- Name: has_provider_scope(uuid, uuid); Type: FUNCTION; Schema: app; Owner: -
--

CREATE FUNCTION app.has_provider_scope(p_provider uuid, p_outlet uuid) RETURNS boolean
    LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path TO 'public', 'app', 'auth', 'pg_temp'
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


--
-- Name: uid(); Type: FUNCTION; Schema: auth; Owner: -
--

CREATE FUNCTION auth.uid() RETURNS uuid
    LANGUAGE sql STABLE
    AS $$
        SELECT nullif(
          current_setting('request.jwt.claims', true)::json ->> 'sub', ''
        )::uuid
      $$;


--
-- Name: areas_prevent_cycle(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.areas_prevent_cycle() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  ancestor uuid := NEW.parent_area_id;
  depth    int  := 0;
BEGIN
  WHILE ancestor IS NOT NULL LOOP
    IF ancestor = NEW.area_id THEN
      RAISE EXCEPTION 'area hierarchy cycle detected at area_id=%', NEW.area_id
        USING ERRCODE = 'check_violation';
    END IF;
    SELECT parent_area_id INTO ancestor FROM areas WHERE area_id = ancestor;
    depth := depth + 1;
    IF depth > 64 THEN
      RAISE EXCEPTION 'area hierarchy too deep (possible cycle) at area_id=%', NEW.area_id
        USING ERRCODE = 'check_violation';
    END IF;
  END LOOP;
  RETURN NEW;
END
$$;


--
-- Name: enforce_account_consistency(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_account_consistency() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  a_outlet   uuid;
  a_provider uuid;
BEGIN
  SELECT outlet_id, provider_id INTO a_outlet, a_provider
  FROM outlet_provider_accounts
  WHERE outlet_provider_account_id = NEW.outlet_provider_account_id;

  IF a_outlet IS NULL THEN
    RAISE EXCEPTION 'unknown outlet_provider_account_id=%', NEW.outlet_provider_account_id
      USING ERRCODE = 'foreign_key_violation';
  END IF;

  IF NEW.provider_id <> a_provider OR NEW.outlet_id <> a_outlet THEN
    RAISE EXCEPTION
      'denormalized provider/outlet (%, %) do not match account % owner (%, %)',
      NEW.provider_id, NEW.outlet_id, NEW.outlet_provider_account_id, a_provider, a_outlet
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END
$$;


--
-- Name: enforce_alert_has_source(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_alert_has_source() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: enforce_alert_immutability(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_alert_immutability() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: enforce_case_scope_matches_alert(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_case_scope_matches_alert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: enforce_case_transition(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_case_transition() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: enforce_explanation_benign_context(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_explanation_benign_context() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: enforce_flag_txn_same_provider(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_flag_txn_same_provider() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: enforce_no_suppressed_anomaly_link(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_no_suppressed_anomaly_link() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: enforce_projection_account(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.enforce_projection_account() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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


--
-- Name: reject_ledger_from_rejected_event(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.reject_ledger_from_rejected_event() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  st normalization_status;
BEGIN
  IF NEW.ingestion_event_id IS NULL THEN
    RETURN NEW;
  END IF;
  SELECT normalization_status INTO st
  FROM ingestion_events WHERE ingestion_event_id = NEW.ingestion_event_id;
  IF st = 'rejected' THEN
    RAISE EXCEPTION 'rejected ingestion event % cannot produce a ledger row', NEW.ingestion_event_id
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END
$$;


--
-- Name: reject_mutation(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.reject_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  RAISE EXCEPTION 'append-only table %.% forbids %',
    TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP
    USING ERRCODE = 'restrict_violation';
  RETURN NULL;
END
$$;


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: users; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: alert_anomaly_flags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert_anomaly_flags (
    alert_id uuid NOT NULL,
    anomaly_flag_id uuid NOT NULL
);


--
-- Name: alert_explanations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert_explanations (
    alert_explanation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    alert_id uuid NOT NULL,
    explanation_template_id uuid NOT NULL,
    locale public.locale_code NOT NULL,
    situation_text text NOT NULL,
    evidence_text text NOT NULL,
    uncertainty_text text NOT NULL,
    next_step_text text NOT NULL,
    benign_context_text text,
    rendered_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: alert_liquidity_projections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert_liquidity_projections (
    alert_id uuid NOT NULL,
    liquidity_projection_id uuid NOT NULL
);


--
-- Name: alert_quality_assessments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alert_quality_assessments (
    alert_id uuid NOT NULL,
    data_quality_assessment_id uuid NOT NULL
);


--
-- Name: alerts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alerts (
    alert_id uuid DEFAULT gen_random_uuid() NOT NULL,
    simulation_run_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    provider_id uuid,
    alert_type public.alert_type NOT NULL,
    severity public.severity NOT NULL,
    state public.alert_state DEFAULT 'active'::text NOT NULL,
    deduplication_key text NOT NULL,
    title_key text NOT NULL,
    structured_payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    requires_case boolean NOT NULL,
    detected_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    supersedes_alert_id uuid
);


--
-- Name: analytics_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analytics_runs (
    analytics_run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    simulation_run_id uuid NOT NULL,
    engine public.analytics_engine NOT NULL,
    engine_version text NOT NULL,
    configuration jsonb DEFAULT '{}'::jsonb NOT NULL,
    input_window_start timestamp with time zone NOT NULL,
    input_window_end timestamp with time zone NOT NULL,
    status text DEFAULT 'running'::text NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    error_summary text,
    CONSTRAINT analytics_runs_status_check CHECK ((status = ANY (ARRAY['running'::text, 'completed'::text, 'failed'::text])))
);


--
-- Name: anomaly_evidence_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anomaly_evidence_items (
    anomaly_evidence_item_id uuid DEFAULT gen_random_uuid() NOT NULL,
    anomaly_flag_id uuid NOT NULL,
    evidence_type text NOT NULL,
    label text NOT NULL,
    value jsonb DEFAULT '{}'::jsonb NOT NULL,
    display_order integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT anomaly_evidence_items_display_order_check CHECK ((display_order >= 0))
);


--
-- Name: anomaly_flag_transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anomaly_flag_transactions (
    anomaly_flag_id uuid NOT NULL,
    transaction_id uuid NOT NULL
);


--
-- Name: anomaly_flags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anomaly_flags (
    anomaly_flag_id uuid DEFAULT gen_random_uuid() NOT NULL,
    analytics_run_id uuid NOT NULL,
    anomaly_rule_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    provider_id uuid NOT NULL,
    outlet_provider_account_id uuid NOT NULL,
    data_quality_assessment_id uuid NOT NULL,
    window_start timestamp with time zone NOT NULL,
    window_end timestamp with time zone NOT NULL,
    confidence_score public.score_unit NOT NULL,
    confidence_level public.confidence_level NOT NULL,
    disposition public.anomaly_disposition NOT NULL,
    reason_code text NOT NULL,
    evidence_summary text NOT NULL,
    plausible_benign_explanation text,
    suppression_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT af_actionable_needs_benign CHECK ((((disposition)::text <> ALL (ARRAY['requires_review'::text, 'confirmed_unusual'::text])) OR (plausible_benign_explanation IS NOT NULL))),
    CONSTRAINT af_suppressed_needs_reason CHECK ((((disposition)::text <> 'suppressed_data_quality'::text) OR (suppression_reason IS NOT NULL)))
);


--
-- Name: anomaly_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.anomaly_rules (
    anomaly_rule_id uuid DEFAULT gen_random_uuid() NOT NULL,
    code text NOT NULL,
    pattern public.anomaly_pattern NOT NULL,
    version text NOT NULL,
    name text NOT NULL,
    description text NOT NULL,
    configuration jsonb DEFAULT '{}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: app_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_users (
    user_id uuid NOT NULL,
    display_name text,
    preferred_locale public.locale_code DEFAULT 'en'::text NOT NULL,
    is_demo_user boolean DEFAULT true NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: areas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.areas (
    area_id uuid DEFAULT gen_random_uuid() NOT NULL,
    parent_area_id uuid,
    code text NOT NULL,
    name text NOT NULL,
    level public.area_level NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT areas_no_self_parent CHECK (((parent_area_id IS NULL) OR (parent_area_id <> area_id)))
);


--
-- Name: audit_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_events (
    audit_event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid,
    alert_id uuid,
    provider_id uuid,
    outlet_id uuid,
    actor_user_id uuid,
    actor_type text NOT NULL,
    action text NOT NULL,
    entity_type text,
    entity_id uuid,
    previous_values jsonb,
    new_values jsonb,
    request_id text,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    hash text,
    CONSTRAINT audit_events_actor_type_check CHECK ((actor_type = ANY (ARRAY['user'::text, 'routing_engine'::text, 'analytics_engine'::text, 'system'::text])))
);


--
-- Name: case_assignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.case_assignments (
    case_assignment_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    assigned_to_user_id uuid,
    assigned_to_role public.app_role NOT NULL,
    assigned_by_user_id uuid,
    reason public.assignment_reason NOT NULL,
    routing_rule_id uuid,
    comment text,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: case_notes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.case_notes (
    case_note_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    author_user_id uuid NOT NULL,
    note_text text NOT NULL,
    note_type text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT case_notes_note_type_check CHECK ((note_type = ANY (ARRAY['general'::text, 'contact_attempt'::text, 'evidence'::text, 'resolution'::text])))
);


--
-- Name: case_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.case_reviews (
    case_review_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    reviewed_by_user_id uuid NOT NULL,
    disposition public.review_outcome NOT NULL,
    was_false_positive boolean,
    review_summary text NOT NULL,
    reviewed_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: case_status_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.case_status_history (
    case_status_history_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    from_status public.case_status,
    to_status public.case_status NOT NULL,
    changed_by_user_id uuid,
    reason text,
    changed_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: cases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cases (
    case_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_number text NOT NULL,
    alert_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    provider_id uuid,
    routing_rule_id uuid,
    status public.case_status DEFAULT 'open'::text NOT NULL,
    current_owner_user_id uuid,
    current_owner_role public.app_role NOT NULL,
    recommended_next_step text NOT NULL,
    opened_at timestamp with time zone DEFAULT now() NOT NULL,
    acknowledged_at timestamp with time zone,
    escalated_at timestamp with time zone,
    resolved_at timestamp with time zone,
    resolution_summary text,
    version integer DEFAULT 1 NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT case_resolved_needs_summary CHECK ((((status)::text <> 'resolved'::text) OR ((resolution_summary IS NOT NULL) AND (resolved_at IS NOT NULL))))
);


--
-- Name: cash_balance_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cash_balance_snapshots (
    cash_balance_snapshot_id uuid DEFAULT gen_random_uuid() NOT NULL,
    ingestion_event_id uuid,
    simulation_run_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    balance numeric(18,2) NOT NULL,
    currency_code public.currency_bdt DEFAULT 'BDT'::bpchar NOT NULL,
    observed_at timestamp with time zone NOT NULL,
    received_at timestamp with time zone NOT NULL,
    source_kind text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT cash_balance_snapshots_balance_check CHECK ((balance >= (0)::numeric)),
    CONSTRAINT cash_balance_snapshots_source_kind_check CHECK ((source_kind = ANY (ARRAY['feed'::text, 'derived'::text, 'seed'::text])))
);


--
-- Name: data_quality_assessments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_quality_assessments (
    data_quality_assessment_id uuid DEFAULT gen_random_uuid() NOT NULL,
    simulation_run_id uuid NOT NULL,
    ingestion_batch_id uuid,
    outlet_id uuid NOT NULL,
    provider_id uuid NOT NULL,
    status public.feed_health_status NOT NULL,
    confidence_modifier public.score_unit NOT NULL,
    sample_count integer NOT NULL,
    latest_source_at timestamp with time zone,
    assessed_at timestamp with time zone NOT NULL,
    engine_version text NOT NULL,
    summary text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT data_quality_assessments_sample_count_check CHECK ((sample_count >= 0))
);


--
-- Name: data_quality_issues; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_quality_issues (
    data_quality_issue_id uuid DEFAULT gen_random_uuid() NOT NULL,
    data_quality_assessment_id uuid NOT NULL,
    issue_type public.quality_issue_type NOT NULL,
    severity public.severity NOT NULL,
    field_name text,
    evidence jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: explanation_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.explanation_templates (
    explanation_template_id uuid DEFAULT gen_random_uuid() NOT NULL,
    template_key text NOT NULL,
    locale public.locale_code NOT NULL,
    version integer NOT NULL,
    alert_type public.alert_type NOT NULL,
    situation_template text NOT NULL,
    evidence_template text NOT NULL,
    uncertainty_template text NOT NULL,
    next_step_template text NOT NULL,
    benign_context_template text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT explanation_templates_version_check CHECK ((version > 0))
);


--
-- Name: fault_injections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fault_injections (
    fault_injection_id uuid DEFAULT gen_random_uuid() NOT NULL,
    simulation_run_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    provider_id uuid,
    fault_type public.fault_type NOT NULL,
    parameters jsonb DEFAULT '{}'::jsonb NOT NULL,
    scheduled_at timestamp with time zone DEFAULT now() NOT NULL,
    applied_at timestamp with time zone,
    ended_at timestamp with time zone,
    is_enabled boolean DEFAULT true NOT NULL
);


--
-- Name: ground_truth_labels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ground_truth_labels (
    ground_truth_label_id uuid DEFAULT gen_random_uuid() NOT NULL,
    validation_run_id uuid NOT NULL,
    simulation_run_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    provider_id uuid,
    label_type text NOT NULL,
    expected_value jsonb DEFAULT '{}'::jsonb NOT NULL,
    window_start timestamp with time zone NOT NULL,
    window_end timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ground_truth_labels_label_type_check CHECK ((label_type = ANY (ARRAY['shortage'::text, 'anomaly'::text, 'normal'::text, 'data_quality_incident'::text])))
);


--
-- Name: ingestion_batches; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingestion_batches (
    ingestion_batch_id uuid DEFAULT gen_random_uuid() NOT NULL,
    simulation_run_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    provider_id uuid NOT NULL,
    source_batch_ref text NOT NULL,
    source_generated_at timestamp with time zone,
    received_at timestamp with time zone NOT NULL,
    expected_event_count integer DEFAULT 0 NOT NULL,
    received_event_count integer DEFAULT 0 NOT NULL,
    rejected_event_count integer DEFAULT 0 NOT NULL,
    normalization_status public.normalization_status NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ingestion_batches_expected_event_count_check CHECK ((expected_event_count >= 0)),
    CONSTRAINT ingestion_batches_received_event_count_check CHECK ((received_event_count >= 0)),
    CONSTRAINT ingestion_batches_rejected_event_count_check CHECK ((rejected_event_count >= 0))
);


--
-- Name: ingestion_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingestion_events (
    ingestion_event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    ingestion_batch_id uuid NOT NULL,
    event_type public.feed_event_type NOT NULL,
    source_event_ref text NOT NULL,
    source_observed_at timestamp with time zone,
    received_at timestamp with time zone NOT NULL,
    safe_payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    normalization_status public.normalization_status NOT NULL,
    rejection_code text,
    rejection_detail text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: liquidity_projection_quality_assessments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.liquidity_projection_quality_assessments (
    liquidity_projection_id uuid NOT NULL,
    data_quality_assessment_id uuid NOT NULL
);


--
-- Name: liquidity_projections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.liquidity_projections (
    liquidity_projection_id uuid DEFAULT gen_random_uuid() NOT NULL,
    analytics_run_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    reserve_type public.reserve_type NOT NULL,
    outlet_provider_account_id uuid,
    provider_id uuid,
    primary_data_quality_assessment_id uuid,
    as_of_at timestamp with time zone NOT NULL,
    current_balance numeric(18,2) NOT NULL,
    burn_rate_per_hour numeric(18,4) NOT NULL,
    projected_shortage_at timestamp with time zone,
    lower_bound_at timestamp with time zone,
    upper_bound_at timestamp with time zone,
    confidence_score public.score_unit NOT NULL,
    confidence_level public.confidence_level NOT NULL,
    sample_count integer NOT NULL,
    is_actionable boolean NOT NULL,
    non_actionable_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT liquidity_projections_current_balance_check CHECK ((current_balance >= (0)::numeric)),
    CONSTRAINT liquidity_projections_sample_count_check CHECK ((sample_count >= 0)),
    CONSTRAINT lp_nonactionable_reason CHECK ((is_actionable OR (non_actionable_reason IS NOT NULL))),
    CONSTRAINT lp_nonpositive_burn_no_shortage CHECK (((burn_rate_per_hour > (0)::numeric) OR ((projected_shortage_at IS NULL) AND (lower_bound_at IS NULL) AND (upper_bound_at IS NULL)))),
    CONSTRAINT lp_reserve_xor CHECK (((((reserve_type)::text = 'shared_cash'::text) AND (provider_id IS NULL) AND (outlet_provider_account_id IS NULL)) OR (((reserve_type)::text = 'provider_e_money'::text) AND (provider_id IS NOT NULL) AND (outlet_provider_account_id IS NOT NULL))))
);


--
-- Name: liquidity_signals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.liquidity_signals (
    liquidity_signal_id uuid DEFAULT gen_random_uuid() NOT NULL,
    liquidity_projection_id uuid NOT NULL,
    signal_code text NOT NULL,
    label text NOT NULL,
    numeric_value numeric,
    unit text,
    direction text NOT NULL,
    details jsonb DEFAULT '{}'::jsonb NOT NULL,
    display_order integer DEFAULT 0 NOT NULL,
    CONSTRAINT liquidity_signals_direction_check CHECK ((direction = ANY (ARRAY['increases_pressure'::text, 'reduces_pressure'::text, 'reduces_confidence'::text]))),
    CONSTRAINT liquidity_signals_display_order_check CHECK ((display_order >= 0))
);


--
-- Name: metric_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.metric_results (
    metric_result_id uuid DEFAULT gen_random_uuid() NOT NULL,
    validation_run_id uuid NOT NULL,
    metric_code text NOT NULL,
    category text NOT NULL,
    value numeric NOT NULL,
    unit text NOT NULL,
    sample_size integer NOT NULL,
    method text NOT NULL,
    limitations text NOT NULL,
    details jsonb DEFAULT '{}'::jsonb NOT NULL,
    computed_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT metric_results_category_check CHECK ((category = ANY (ARRAY['analytics'::text, 'performance'::text, 'reliability'::text, 'explainability'::text]))),
    CONSTRAINT metric_results_sample_size_check CHECK ((sample_size > 0))
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    notification_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    recipient_user_id uuid,
    recipient_role public.app_role NOT NULL,
    channel public.notification_channel DEFAULT 'in_app'::text NOT NULL,
    status public.notification_status DEFAULT 'queued'::text NOT NULL,
    payload jsonb DEFAULT '{}'::jsonb NOT NULL,
    queued_at timestamp with time zone DEFAULT now() NOT NULL,
    delivered_at timestamp with time zone,
    read_at timestamp with time zone,
    failure_reason text
);


--
-- Name: outlet_provider_accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.outlet_provider_accounts (
    outlet_provider_account_id uuid DEFAULT gen_random_uuid() NOT NULL,
    outlet_id uuid NOT NULL,
    provider_id uuid NOT NULL,
    synthetic_account_ref text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: outlets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.outlets (
    outlet_id uuid DEFAULT gen_random_uuid() NOT NULL,
    synthetic_code text NOT NULL,
    display_name text NOT NULL,
    area_id uuid NOT NULL,
    currency_code public.currency_bdt DEFAULT 'BDT'::bpchar NOT NULL,
    latitude numeric(9,6),
    longitude numeric(9,6),
    is_synthetic boolean DEFAULT true NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT outlets_must_be_synthetic CHECK (is_synthetic)
);


--
-- Name: provider_balance_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.provider_balance_snapshots (
    provider_balance_snapshot_id uuid DEFAULT gen_random_uuid() NOT NULL,
    ingestion_event_id uuid,
    simulation_run_id uuid NOT NULL,
    outlet_provider_account_id uuid NOT NULL,
    provider_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    balance numeric(18,2) NOT NULL,
    currency_code public.currency_bdt DEFAULT 'BDT'::bpchar NOT NULL,
    observed_at timestamp with time zone NOT NULL,
    received_at timestamp with time zone NOT NULL,
    source_kind text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT provider_balance_snapshots_balance_check CHECK ((balance >= (0)::numeric)),
    CONSTRAINT provider_balance_snapshots_source_kind_check CHECK ((source_kind = ANY (ARRAY['feed'::text, 'derived'::text, 'seed'::text])))
);


--
-- Name: providers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.providers (
    provider_id uuid DEFAULT gen_random_uuid() NOT NULL,
    code public.provider_code NOT NULL,
    display_name text NOT NULL,
    display_color text,
    is_simulated boolean DEFAULT true NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT providers_must_be_simulated CHECK (is_simulated)
);


--
-- Name: routing_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.routing_rules (
    routing_rule_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    provider_id uuid,
    area_id uuid,
    alert_type public.alert_type,
    minimum_severity public.severity NOT NULL,
    target_role public.app_role NOT NULL,
    priority integer DEFAULT 100 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version text NOT NULL,
    name text NOT NULL,
    checksum text NOT NULL,
    applied_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: simulation_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.simulation_runs (
    simulation_run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    scenario_id uuid NOT NULL,
    seed bigint NOT NULL,
    config_snapshot jsonb NOT NULL,
    status text DEFAULT 'queued'::text NOT NULL,
    started_by_user_id uuid,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    error_summary text,
    CONSTRAINT simulation_runs_status_check CHECK ((status = ANY (ARRAY['queued'::text, 'running'::text, 'completed'::text, 'failed'::text, 'reset'::text])))
);


--
-- Name: simulation_scenarios; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.simulation_scenarios (
    scenario_id uuid DEFAULT gen_random_uuid() NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    description text NOT NULL,
    default_seed bigint NOT NULL,
    default_config jsonb DEFAULT '{}'::jsonb NOT NULL,
    validation_split public.validation_split NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT simulation_scenarios_code_check CHECK ((code = ANY (ARRAY['normal'::text, 'scenario_a'::text, 'scenario_b'::text, 'scenario_c'::text, 'scenario_d'::text])))
);


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transactions (
    transaction_id uuid DEFAULT gen_random_uuid() NOT NULL,
    ingestion_event_id uuid NOT NULL,
    simulation_run_id uuid NOT NULL,
    outlet_provider_account_id uuid NOT NULL,
    provider_id uuid NOT NULL,
    outlet_id uuid NOT NULL,
    synthetic_transaction_ref text NOT NULL,
    synthetic_party_ref text NOT NULL,
    transaction_type public.transaction_type NOT NULL,
    status public.transaction_status NOT NULL,
    amount numeric(18,2) NOT NULL,
    currency_code public.currency_bdt DEFAULT 'BDT'::bpchar NOT NULL,
    occurred_at timestamp with time zone NOT NULL,
    received_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT transactions_amount_check CHECK ((amount > (0)::numeric))
);


--
-- Name: user_access_scopes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_access_scopes (
    user_access_scope_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    role public.app_role NOT NULL,
    provider_id uuid,
    area_id uuid,
    outlet_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT uas_role_shape CHECK (((((role)::text <> 'agent'::text) OR (outlet_id IS NOT NULL)) AND (((role)::text <> ALL (ARRAY['provider_ops'::text, 'risk_analyst'::text])) OR (provider_id IS NOT NULL)) AND (((role)::text <> ALL (ARRAY['field_officer'::text, 'area_manager'::text])) OR (area_id IS NOT NULL))))
);


--
-- Name: v_case_timeline; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_case_timeline WITH (security_invoker='true') AS
 SELECT case_id,
    event_at,
    event_type,
    event_id,
    actor_user_id,
    detail
   FROM ( SELECT c.case_id,
            af.created_at AS event_at,
            'anomaly_flag'::text AS event_type,
            af.anomaly_flag_id AS event_id,
            NULL::uuid AS actor_user_id,
            jsonb_build_object('disposition', af.disposition) AS detail,
            0 AS ord
           FROM (((public.cases c
             JOIN public.alerts a ON ((a.alert_id = c.alert_id)))
             JOIN public.alert_anomaly_flags aaf ON ((aaf.alert_id = a.alert_id)))
             JOIN public.anomaly_flags af ON ((af.anomaly_flag_id = aaf.anomaly_flag_id)))
        UNION ALL
         SELECT c.case_id,
            lp.created_at,
            'liquidity_projection'::text,
            lp.liquidity_projection_id,
            NULL::uuid,
            jsonb_build_object('reserve_type', lp.reserve_type) AS jsonb_build_object,
            0
           FROM (((public.cases c
             JOIN public.alerts a ON ((a.alert_id = c.alert_id)))
             JOIN public.alert_liquidity_projections alp ON ((alp.alert_id = a.alert_id)))
             JOIN public.liquidity_projections lp ON ((lp.liquidity_projection_id = alp.liquidity_projection_id)))
        UNION ALL
         SELECT c.case_id,
            a.created_at,
            'alert_created'::text,
            a.alert_id,
            NULL::uuid,
            jsonb_build_object('alert_type', a.alert_type, 'severity', a.severity) AS jsonb_build_object,
            1
           FROM (public.cases c
             JOIN public.alerts a ON ((a.alert_id = c.alert_id)))
        UNION ALL
         SELECT c.case_id,
            c.opened_at,
            'case_opened'::text,
            c.case_id,
            NULL::uuid,
            jsonb_build_object('status', 'open') AS jsonb_build_object,
            2
           FROM public.cases c
        UNION ALL
         SELECT ca.case_id,
            ca.assigned_at,
            'assignment'::text,
            ca.case_assignment_id,
            ca.assigned_by_user_id,
            jsonb_build_object('to_role', ca.assigned_to_role, 'reason', ca.reason) AS jsonb_build_object,
            3
           FROM public.case_assignments ca
        UNION ALL
         SELECT sh.case_id,
            sh.changed_at,
            'status_change'::text,
            sh.case_status_history_id,
            sh.changed_by_user_id,
            jsonb_build_object('from', sh.from_status, 'to', sh.to_status) AS jsonb_build_object,
            4
           FROM public.case_status_history sh
        UNION ALL
         SELECT n.case_id,
            n.created_at,
            'note'::text,
            n.case_note_id,
            n.author_user_id,
            jsonb_build_object('note_type', n.note_type) AS jsonb_build_object,
            5
           FROM public.case_notes n
        UNION ALL
         SELECT nt.case_id,
            nt.queued_at,
            'notification'::text,
            nt.notification_id,
            nt.recipient_user_id,
            jsonb_build_object('channel', nt.channel, 'status', nt.status) AS jsonb_build_object,
            6
           FROM public.notifications nt
        UNION ALL
         SELECT r.case_id,
            r.reviewed_at,
            'review'::text,
            r.case_review_id,
            r.reviewed_by_user_id,
            jsonb_build_object('disposition', r.disposition) AS jsonb_build_object,
            7
           FROM public.case_reviews r
        UNION ALL
         SELECT ae.case_id,
            ae.occurred_at,
            'audit'::text,
            ae.audit_event_id,
            ae.actor_user_id,
            jsonb_build_object('action', ae.action) AS jsonb_build_object,
            8
           FROM public.audit_events ae
          WHERE (ae.case_id IS NOT NULL)) t
  ORDER BY case_id, event_at, ord, event_id;


--
-- Name: v_current_feed_health; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_current_feed_health WITH (security_invoker='true') AS
 SELECT DISTINCT ON (outlet_id, provider_id) outlet_id,
    provider_id,
    data_quality_assessment_id,
    status,
    confidence_modifier,
    sample_count,
    latest_source_at,
    assessed_at,
    engine_version,
    summary
   FROM public.data_quality_assessments
  ORDER BY outlet_id, provider_id, assessed_at DESC, created_at DESC;


--
-- Name: v_latest_cash_balance; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_latest_cash_balance WITH (security_invoker='true') AS
 SELECT DISTINCT ON (outlet_id) outlet_id,
    cash_balance_snapshot_id,
    simulation_run_id,
    balance,
    currency_code,
    observed_at,
    received_at,
    source_kind,
    created_at
   FROM public.cash_balance_snapshots
  ORDER BY outlet_id, observed_at DESC, received_at DESC, created_at DESC;


--
-- Name: v_latest_liquidity_projections; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_latest_liquidity_projections WITH (security_invoker='true') AS
 SELECT DISTINCT ON (outlet_id, reserve_type, outlet_provider_account_id) liquidity_projection_id,
    analytics_run_id,
    outlet_id,
    reserve_type,
    outlet_provider_account_id,
    provider_id,
    primary_data_quality_assessment_id,
    as_of_at,
    current_balance,
    burn_rate_per_hour,
    projected_shortage_at,
    lower_bound_at,
    upper_bound_at,
    confidence_score,
    confidence_level,
    sample_count,
    is_actionable,
    non_actionable_reason,
    created_at
   FROM public.liquidity_projections
  ORDER BY outlet_id, reserve_type, outlet_provider_account_id, as_of_at DESC, created_at DESC;


--
-- Name: v_latest_provider_balances; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_latest_provider_balances WITH (security_invoker='true') AS
 WITH per_ts AS (
         SELECT provider_balance_snapshots.outlet_provider_account_id,
            provider_balance_snapshots.observed_at,
            count(DISTINCT provider_balance_snapshots.balance) AS distinct_bal
           FROM public.provider_balance_snapshots
          GROUP BY provider_balance_snapshots.outlet_provider_account_id, provider_balance_snapshots.observed_at
        ), latest AS (
         SELECT pbs.provider_balance_snapshot_id,
            pbs.ingestion_event_id,
            pbs.simulation_run_id,
            pbs.outlet_provider_account_id,
            pbs.provider_id,
            pbs.outlet_id,
            pbs.balance,
            pbs.currency_code,
            pbs.observed_at,
            pbs.received_at,
            pbs.source_kind,
            pbs.created_at,
            row_number() OVER (PARTITION BY pbs.outlet_provider_account_id ORDER BY pbs.observed_at DESC, pbs.received_at DESC, pbs.created_at DESC) AS rn
           FROM public.provider_balance_snapshots pbs
        )
 SELECT l.outlet_provider_account_id,
    l.outlet_id,
    l.provider_id,
    l.currency_code,
    (pt.distinct_bal > 1) AS is_conflicted,
        CASE
            WHEN (pt.distinct_bal > 1) THEN NULL::numeric
            ELSE l.balance
        END AS balance,
        CASE
            WHEN (pt.distinct_bal > 1) THEN NULL::timestamp with time zone
            ELSE l.observed_at
        END AS observed_at,
    l.received_at,
    lt.balance AS last_trusted_balance,
    lt.observed_at AS last_trusted_observed_at
   FROM ((latest l
     JOIN per_ts pt ON (((pt.outlet_provider_account_id = l.outlet_provider_account_id) AND (pt.observed_at = l.observed_at))))
     LEFT JOIN LATERAL ( SELECT s.balance,
            s.observed_at
           FROM public.provider_balance_snapshots s
          WHERE ((s.outlet_provider_account_id = l.outlet_provider_account_id) AND (s.observed_at IN ( SELECT s2.observed_at
                   FROM public.provider_balance_snapshots s2
                  WHERE (s2.outlet_provider_account_id = l.outlet_provider_account_id)
                  GROUP BY s2.observed_at
                 HAVING (count(DISTINCT s2.balance) = 1))))
          ORDER BY s.observed_at DESC, s.received_at DESC
         LIMIT 1) lt ON (true))
  WHERE (l.rn = 1);


--
-- Name: v_outlet_dashboard; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_outlet_dashboard WITH (security_invoker='true') AS
 SELECT o.outlet_id,
    o.synthetic_code,
    o.display_name,
    o.area_id,
    o.currency_code,
    jsonb_build_object('balance', cb.balance, 'currency', cb.currency_code, 'observed_at', cb.observed_at, 'projection', ( SELECT jsonb_build_object('shortage_at', lp.projected_shortage_at, 'confidence_score', lp.confidence_score, 'confidence_level', lp.confidence_level) AS jsonb_build_object
           FROM public.v_latest_liquidity_projections lp
          WHERE ((lp.outlet_id = o.outlet_id) AND ((lp.reserve_type)::text = 'shared_cash'::text)))) AS shared_cash,
    ( SELECT COALESCE(jsonb_agg(jsonb_build_object('provider', jsonb_build_object('code', pr.code, 'display_name', pr.display_name), 'outlet_provider_account_id', opa.outlet_provider_account_id, 'balance', pb.balance, 'last_trusted_balance', pb.last_trusted_balance, 'observed_at', pb.observed_at, 'is_conflicted', COALESCE(pb.is_conflicted, false), 'feed_health', jsonb_build_object('status', fh.status, 'confidence_modifier', fh.confidence_modifier), 'projection', jsonb_build_object('shortage_at', lp.projected_shortage_at, 'confidence_score', lp.confidence_score, 'confidence_level', lp.confidence_level)) ORDER BY pr.code), '[]'::jsonb) AS "coalesce"
           FROM ((((public.outlet_provider_accounts opa
             JOIN public.providers pr ON ((pr.provider_id = opa.provider_id)))
             LEFT JOIN public.v_latest_provider_balances pb ON ((pb.outlet_provider_account_id = opa.outlet_provider_account_id)))
             LEFT JOIN public.v_current_feed_health fh ON (((fh.outlet_id = opa.outlet_id) AND (fh.provider_id = opa.provider_id))))
             LEFT JOIN public.v_latest_liquidity_projections lp ON (((lp.outlet_id = opa.outlet_id) AND ((lp.reserve_type)::text = 'provider_e_money'::text) AND (lp.outlet_provider_account_id = opa.outlet_provider_account_id))))
          WHERE ((opa.outlet_id = o.outlet_id) AND opa.is_active)) AS providers,
    ( SELECT COALESCE(jsonb_agg(jsonb_build_object('alert_id', a.alert_id, 'type', a.alert_type, 'severity', a.severity, 'provider_id', a.provider_id, 'detected_at', a.detected_at) ORDER BY a.detected_at DESC), '[]'::jsonb) AS "coalesce"
           FROM public.alerts a
          WHERE ((a.outlet_id = o.outlet_id) AND ((a.state)::text = 'active'::text))) AS alerts,
    now() AS generated_at
   FROM (public.outlets o
     LEFT JOIN public.v_latest_cash_balance cb ON ((cb.outlet_id = o.outlet_id)));


--
-- Name: validation_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.validation_runs (
    validation_run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    dataset_split public.validation_split NOT NULL,
    engine_version text NOT NULL,
    configuration jsonb DEFAULT '{}'::jsonb NOT NULL,
    started_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    status text DEFAULT 'running'::text NOT NULL,
    created_by_user_id uuid,
    CONSTRAINT validation_runs_status_check CHECK ((status = ANY (ARRAY['running'::text, 'completed'::text, 'failed'::text])))
);


--
-- Name: v_validation_summary; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_validation_summary WITH (security_invoker='true') AS
 SELECT DISTINCT ON (mr.metric_code) mr.metric_code,
    mr.category,
    mr.value,
    mr.unit,
    mr.sample_size,
    mr.method,
    mr.limitations,
    mr.details,
    mr.computed_at,
    vr.validation_run_id,
    vr.name AS validation_run_name,
    vr.engine_version
   FROM (public.metric_results mr
     JOIN public.validation_runs vr ON ((vr.validation_run_id = mr.validation_run_id)))
  WHERE (vr.status = 'completed'::text)
  ORDER BY mr.metric_code, mr.computed_at DESC;


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: alert_anomaly_flags alert_anomaly_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_anomaly_flags
    ADD CONSTRAINT alert_anomaly_flags_pkey PRIMARY KEY (alert_id, anomaly_flag_id);


--
-- Name: alert_explanations alert_explanations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_explanations
    ADD CONSTRAINT alert_explanations_pkey PRIMARY KEY (alert_explanation_id);


--
-- Name: alert_liquidity_projections alert_liquidity_projections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_liquidity_projections
    ADD CONSTRAINT alert_liquidity_projections_pkey PRIMARY KEY (alert_id, liquidity_projection_id);


--
-- Name: alert_quality_assessments alert_quality_assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_quality_assessments
    ADD CONSTRAINT alert_quality_assessments_pkey PRIMARY KEY (alert_id, data_quality_assessment_id);


--
-- Name: alerts alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_pkey PRIMARY KEY (alert_id);


--
-- Name: analytics_runs analytics_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_runs
    ADD CONSTRAINT analytics_runs_pkey PRIMARY KEY (analytics_run_id);


--
-- Name: anomaly_evidence_items anomaly_evidence_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_evidence_items
    ADD CONSTRAINT anomaly_evidence_items_pkey PRIMARY KEY (anomaly_evidence_item_id);


--
-- Name: anomaly_flag_transactions anomaly_flag_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flag_transactions
    ADD CONSTRAINT anomaly_flag_transactions_pkey PRIMARY KEY (anomaly_flag_id, transaction_id);


--
-- Name: anomaly_flags anomaly_flags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flags
    ADD CONSTRAINT anomaly_flags_pkey PRIMARY KEY (anomaly_flag_id);


--
-- Name: anomaly_rules anomaly_rules_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_rules
    ADD CONSTRAINT anomaly_rules_code_key UNIQUE (code);


--
-- Name: anomaly_rules anomaly_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_rules
    ADD CONSTRAINT anomaly_rules_pkey PRIMARY KEY (anomaly_rule_id);


--
-- Name: app_users app_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_users
    ADD CONSTRAINT app_users_pkey PRIMARY KEY (user_id);


--
-- Name: areas areas_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT areas_code_key UNIQUE (code);


--
-- Name: areas areas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT areas_pkey PRIMARY KEY (area_id);


--
-- Name: audit_events audit_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_pkey PRIMARY KEY (audit_event_id);


--
-- Name: case_assignments case_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_assignments
    ADD CONSTRAINT case_assignments_pkey PRIMARY KEY (case_assignment_id);


--
-- Name: case_notes case_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_notes
    ADD CONSTRAINT case_notes_pkey PRIMARY KEY (case_note_id);


--
-- Name: case_reviews case_reviews_case_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_reviews
    ADD CONSTRAINT case_reviews_case_id_key UNIQUE (case_id);


--
-- Name: case_reviews case_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_reviews
    ADD CONSTRAINT case_reviews_pkey PRIMARY KEY (case_review_id);


--
-- Name: case_status_history case_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_status_history
    ADD CONSTRAINT case_status_history_pkey PRIMARY KEY (case_status_history_id);


--
-- Name: cases cases_alert_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cases
    ADD CONSTRAINT cases_alert_id_key UNIQUE (alert_id);


--
-- Name: cases cases_case_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cases
    ADD CONSTRAINT cases_case_number_key UNIQUE (case_number);


--
-- Name: cases cases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cases
    ADD CONSTRAINT cases_pkey PRIMARY KEY (case_id);


--
-- Name: cash_balance_snapshots cash_balance_snapshots_ingestion_event_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_balance_snapshots
    ADD CONSTRAINT cash_balance_snapshots_ingestion_event_id_key UNIQUE (ingestion_event_id);


--
-- Name: cash_balance_snapshots cash_balance_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_balance_snapshots
    ADD CONSTRAINT cash_balance_snapshots_pkey PRIMARY KEY (cash_balance_snapshot_id);


--
-- Name: data_quality_assessments data_quality_assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_assessments
    ADD CONSTRAINT data_quality_assessments_pkey PRIMARY KEY (data_quality_assessment_id);


--
-- Name: data_quality_issues data_quality_issues_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_issues
    ADD CONSTRAINT data_quality_issues_pkey PRIMARY KEY (data_quality_issue_id);


--
-- Name: explanation_templates explanation_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.explanation_templates
    ADD CONSTRAINT explanation_templates_pkey PRIMARY KEY (explanation_template_id);


--
-- Name: fault_injections fault_injections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fault_injections
    ADD CONSTRAINT fault_injections_pkey PRIMARY KEY (fault_injection_id);


--
-- Name: ground_truth_labels ground_truth_labels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ground_truth_labels
    ADD CONSTRAINT ground_truth_labels_pkey PRIMARY KEY (ground_truth_label_id);


--
-- Name: ingestion_batches ingestion_batches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_batches
    ADD CONSTRAINT ingestion_batches_pkey PRIMARY KEY (ingestion_batch_id);


--
-- Name: ingestion_events ingestion_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_events
    ADD CONSTRAINT ingestion_events_pkey PRIMARY KEY (ingestion_event_id);


--
-- Name: liquidity_projection_quality_assessments liquidity_projection_quality_assessments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_projection_quality_assessments
    ADD CONSTRAINT liquidity_projection_quality_assessments_pkey PRIMARY KEY (liquidity_projection_id, data_quality_assessment_id);


--
-- Name: liquidity_projections liquidity_projections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_projections
    ADD CONSTRAINT liquidity_projections_pkey PRIMARY KEY (liquidity_projection_id);


--
-- Name: liquidity_signals liquidity_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_signals
    ADD CONSTRAINT liquidity_signals_pkey PRIMARY KEY (liquidity_signal_id);


--
-- Name: metric_results metric_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metric_results
    ADD CONSTRAINT metric_results_pkey PRIMARY KEY (metric_result_id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);


--
-- Name: outlet_provider_accounts outlet_provider_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.outlet_provider_accounts
    ADD CONSTRAINT outlet_provider_accounts_pkey PRIMARY KEY (outlet_provider_account_id);


--
-- Name: outlets outlets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.outlets
    ADD CONSTRAINT outlets_pkey PRIMARY KEY (outlet_id);


--
-- Name: outlets outlets_synthetic_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.outlets
    ADD CONSTRAINT outlets_synthetic_code_key UNIQUE (synthetic_code);


--
-- Name: provider_balance_snapshots provider_balance_snapshots_ingestion_event_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_balance_snapshots
    ADD CONSTRAINT provider_balance_snapshots_ingestion_event_id_key UNIQUE (ingestion_event_id);


--
-- Name: provider_balance_snapshots provider_balance_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_balance_snapshots
    ADD CONSTRAINT provider_balance_snapshots_pkey PRIMARY KEY (provider_balance_snapshot_id);


--
-- Name: providers providers_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.providers
    ADD CONSTRAINT providers_code_key UNIQUE (code);


--
-- Name: providers providers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.providers
    ADD CONSTRAINT providers_pkey PRIMARY KEY (provider_id);


--
-- Name: routing_rules routing_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routing_rules
    ADD CONSTRAINT routing_rules_pkey PRIMARY KEY (routing_rule_id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- Name: simulation_runs simulation_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.simulation_runs
    ADD CONSTRAINT simulation_runs_pkey PRIMARY KEY (simulation_run_id);


--
-- Name: simulation_scenarios simulation_scenarios_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.simulation_scenarios
    ADD CONSTRAINT simulation_scenarios_code_key UNIQUE (code);


--
-- Name: simulation_scenarios simulation_scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.simulation_scenarios
    ADD CONSTRAINT simulation_scenarios_pkey PRIMARY KEY (scenario_id);


--
-- Name: transactions transactions_ingestion_event_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_ingestion_event_id_key UNIQUE (ingestion_event_id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: ingestion_batches uq_batch_provider_ref; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_batches
    ADD CONSTRAINT uq_batch_provider_ref UNIQUE (provider_id, source_batch_ref);


--
-- Name: ingestion_events uq_event_batch_ref; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_events
    ADD CONSTRAINT uq_event_batch_ref UNIQUE (ingestion_batch_id, source_event_ref);


--
-- Name: alert_explanations uq_explanation_alert_locale; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_explanations
    ADD CONSTRAINT uq_explanation_alert_locale UNIQUE (alert_id, locale);


--
-- Name: outlet_provider_accounts uq_opa_outlet_provider; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.outlet_provider_accounts
    ADD CONSTRAINT uq_opa_outlet_provider UNIQUE (outlet_id, provider_id);


--
-- Name: outlet_provider_accounts uq_opa_provider_ref; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.outlet_provider_accounts
    ADD CONSTRAINT uq_opa_provider_ref UNIQUE (provider_id, synthetic_account_ref);


--
-- Name: explanation_templates uq_template_key_locale_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.explanation_templates
    ADD CONSTRAINT uq_template_key_locale_version UNIQUE (template_key, locale, version);


--
-- Name: transactions uq_txn_provider_ref; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT uq_txn_provider_ref UNIQUE (provider_id, synthetic_transaction_ref);


--
-- Name: user_access_scopes uq_uas_assignment; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_access_scopes
    ADD CONSTRAINT uq_uas_assignment UNIQUE NULLS NOT DISTINCT (user_id, role, provider_id, area_id, outlet_id);


--
-- Name: user_access_scopes user_access_scopes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_access_scopes
    ADD CONSTRAINT user_access_scopes_pkey PRIMARY KEY (user_access_scope_id);


--
-- Name: validation_runs validation_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.validation_runs
    ADD CONSTRAINT validation_runs_pkey PRIMARY KEY (validation_run_id);


--
-- Name: ix_af_outlet_provider_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_af_outlet_provider_time ON public.anomaly_flags USING btree (outlet_id, provider_id, window_end DESC);


--
-- Name: ix_alerts_queue; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_alerts_queue ON public.alerts USING btree (outlet_id, provider_id, state, severity, detected_at DESC);


--
-- Name: ix_audit_case_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_audit_case_time ON public.audit_events USING btree (case_id, occurred_at);


--
-- Name: ix_batch_outlet_provider_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_batch_outlet_provider_time ON public.ingestion_batches USING btree (outlet_id, provider_id, received_at DESC);


--
-- Name: ix_cases_outlet_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cases_outlet_status ON public.cases USING btree (outlet_id, status, updated_at DESC);


--
-- Name: ix_cases_provider_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cases_provider_status ON public.cases USING btree (provider_id, status, updated_at DESC);


--
-- Name: ix_cash_outlet_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cash_outlet_time ON public.cash_balance_snapshots USING btree (outlet_id, observed_at DESC, received_at DESC);


--
-- Name: ix_dqa_outlet_provider_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_dqa_outlet_provider_time ON public.data_quality_assessments USING btree (outlet_id, provider_id, assessed_at DESC);


--
-- Name: ix_lp_outlet_reserve_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_lp_outlet_reserve_time ON public.liquidity_projections USING btree (outlet_id, reserve_type, provider_id, as_of_at DESC);


--
-- Name: ix_notifications_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_notifications_recipient ON public.notifications USING btree (recipient_user_id, status, queued_at DESC);


--
-- Name: ix_pbs_account_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pbs_account_time ON public.provider_balance_snapshots USING btree (outlet_provider_account_id, observed_at DESC, received_at DESC);


--
-- Name: ix_txn_outlet_provider_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_txn_outlet_provider_time ON public.transactions USING btree (outlet_id, provider_id, occurred_at DESC);


--
-- Name: ix_txn_provider_party_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_txn_provider_party_time ON public.transactions USING btree (provider_id, synthetic_party_ref, occurred_at DESC);


--
-- Name: uq_alerts_active_dedup; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_alerts_active_dedup ON public.alerts USING btree (deduplication_key) WHERE ((state)::text = 'active'::text);


--
-- Name: alert_anomaly_flags trg_aaf_no_suppressed_link; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_aaf_no_suppressed_link BEFORE INSERT ON public.alert_anomaly_flags FOR EACH ROW EXECUTE FUNCTION public.enforce_no_suppressed_anomaly_link();


--
-- Name: anomaly_evidence_items trg_aei_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_aei_append_only BEFORE DELETE OR UPDATE ON public.anomaly_evidence_items FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: anomaly_flags trg_af_account_consistency; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_af_account_consistency BEFORE INSERT ON public.anomaly_flags FOR EACH ROW EXECUTE FUNCTION public.enforce_account_consistency();


--
-- Name: anomaly_flags trg_af_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_af_append_only BEFORE DELETE OR UPDATE ON public.anomaly_flags FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: anomaly_flag_transactions trg_aft_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_aft_append_only BEFORE DELETE OR UPDATE ON public.anomaly_flag_transactions FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: anomaly_flag_transactions trg_aft_same_provider; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_aft_same_provider BEFORE INSERT ON public.anomaly_flag_transactions FOR EACH ROW EXECUTE FUNCTION public.enforce_flag_txn_same_provider();


--
-- Name: alerts trg_alert_has_source; Type: TRIGGER; Schema: public; Owner: -
--

CREATE CONSTRAINT TRIGGER trg_alert_has_source AFTER INSERT OR UPDATE ON public.alerts DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.enforce_alert_has_source();


--
-- Name: alerts trg_alert_immutability; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_alert_immutability BEFORE DELETE OR UPDATE ON public.alerts FOR EACH ROW EXECUTE FUNCTION public.enforce_alert_immutability();


--
-- Name: anomaly_rules trg_anomaly_rules_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_anomaly_rules_updated_at BEFORE UPDATE ON public.anomaly_rules FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: app_users trg_app_users_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_app_users_updated_at BEFORE UPDATE ON public.app_users FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: areas trg_areas_prevent_cycle; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_areas_prevent_cycle BEFORE INSERT OR UPDATE OF parent_area_id ON public.areas FOR EACH ROW EXECUTE FUNCTION public.areas_prevent_cycle();


--
-- Name: audit_events trg_audit_events_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_audit_events_append_only BEFORE DELETE OR UPDATE ON public.audit_events FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: case_assignments trg_case_assignments_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_case_assignments_append_only BEFORE DELETE OR UPDATE ON public.case_assignments FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: case_notes trg_case_notes_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_case_notes_append_only BEFORE DELETE OR UPDATE ON public.case_notes FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: cases trg_case_scope_matches_alert; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_case_scope_matches_alert BEFORE INSERT OR UPDATE ON public.cases FOR EACH ROW EXECUTE FUNCTION public.enforce_case_scope_matches_alert();


--
-- Name: case_status_history trg_case_status_history_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_case_status_history_append_only BEFORE DELETE OR UPDATE ON public.case_status_history FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: cases trg_case_transition; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_case_transition BEFORE UPDATE ON public.cases FOR EACH ROW EXECUTE FUNCTION public.enforce_case_transition();


--
-- Name: cases trg_cases_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_cases_updated_at BEFORE UPDATE ON public.cases FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: cash_balance_snapshots trg_cash_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_cash_append_only BEFORE DELETE OR UPDATE ON public.cash_balance_snapshots FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: cash_balance_snapshots trg_cash_reject_rejected_event; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_cash_reject_rejected_event BEFORE INSERT ON public.cash_balance_snapshots FOR EACH ROW EXECUTE FUNCTION public.reject_ledger_from_rejected_event();


--
-- Name: data_quality_assessments trg_dqa_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_dqa_append_only BEFORE DELETE OR UPDATE ON public.data_quality_assessments FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: alert_explanations trg_explanation_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_explanation_append_only BEFORE DELETE OR UPDATE ON public.alert_explanations FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: alert_explanations trg_explanation_benign_context; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_explanation_benign_context BEFORE INSERT ON public.alert_explanations FOR EACH ROW EXECUTE FUNCTION public.enforce_explanation_benign_context();


--
-- Name: liquidity_projections trg_lp_account_consistency; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_lp_account_consistency BEFORE INSERT ON public.liquidity_projections FOR EACH ROW EXECUTE FUNCTION public.enforce_projection_account();


--
-- Name: liquidity_projections trg_lp_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_lp_append_only BEFORE DELETE OR UPDATE ON public.liquidity_projections FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: outlet_provider_accounts trg_opa_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_opa_updated_at BEFORE UPDATE ON public.outlet_provider_accounts FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: outlets trg_outlets_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_outlets_updated_at BEFORE UPDATE ON public.outlets FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: provider_balance_snapshots trg_pbs_account_consistency; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_pbs_account_consistency BEFORE INSERT ON public.provider_balance_snapshots FOR EACH ROW EXECUTE FUNCTION public.enforce_account_consistency();


--
-- Name: provider_balance_snapshots trg_pbs_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_pbs_append_only BEFORE DELETE OR UPDATE ON public.provider_balance_snapshots FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: provider_balance_snapshots trg_pbs_reject_rejected_event; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_pbs_reject_rejected_event BEFORE INSERT ON public.provider_balance_snapshots FOR EACH ROW EXECUTE FUNCTION public.reject_ledger_from_rejected_event();


--
-- Name: routing_rules trg_routing_rules_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_routing_rules_updated_at BEFORE UPDATE ON public.routing_rules FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: simulation_scenarios trg_scenarios_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_scenarios_updated_at BEFORE UPDATE ON public.simulation_scenarios FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: transactions trg_txn_account_consistency; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_txn_account_consistency BEFORE INSERT ON public.transactions FOR EACH ROW EXECUTE FUNCTION public.enforce_account_consistency();


--
-- Name: transactions trg_txn_append_only; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_txn_append_only BEFORE DELETE OR UPDATE ON public.transactions FOR EACH ROW EXECUTE FUNCTION public.reject_mutation();


--
-- Name: transactions trg_txn_reject_rejected_event; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_txn_reject_rejected_event BEFORE INSERT ON public.transactions FOR EACH ROW EXECUTE FUNCTION public.reject_ledger_from_rejected_event();


--
-- Name: alert_anomaly_flags alert_anomaly_flags_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_anomaly_flags
    ADD CONSTRAINT alert_anomaly_flags_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES public.alerts(alert_id);


--
-- Name: alert_anomaly_flags alert_anomaly_flags_anomaly_flag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_anomaly_flags
    ADD CONSTRAINT alert_anomaly_flags_anomaly_flag_id_fkey FOREIGN KEY (anomaly_flag_id) REFERENCES public.anomaly_flags(anomaly_flag_id);


--
-- Name: alert_explanations alert_explanations_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_explanations
    ADD CONSTRAINT alert_explanations_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES public.alerts(alert_id);


--
-- Name: alert_explanations alert_explanations_explanation_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_explanations
    ADD CONSTRAINT alert_explanations_explanation_template_id_fkey FOREIGN KEY (explanation_template_id) REFERENCES public.explanation_templates(explanation_template_id);


--
-- Name: alert_liquidity_projections alert_liquidity_projections_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_liquidity_projections
    ADD CONSTRAINT alert_liquidity_projections_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES public.alerts(alert_id);


--
-- Name: alert_liquidity_projections alert_liquidity_projections_liquidity_projection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_liquidity_projections
    ADD CONSTRAINT alert_liquidity_projections_liquidity_projection_id_fkey FOREIGN KEY (liquidity_projection_id) REFERENCES public.liquidity_projections(liquidity_projection_id);


--
-- Name: alert_quality_assessments alert_quality_assessments_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_quality_assessments
    ADD CONSTRAINT alert_quality_assessments_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES public.alerts(alert_id);


--
-- Name: alert_quality_assessments alert_quality_assessments_data_quality_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alert_quality_assessments
    ADD CONSTRAINT alert_quality_assessments_data_quality_assessment_id_fkey FOREIGN KEY (data_quality_assessment_id) REFERENCES public.data_quality_assessments(data_quality_assessment_id);


--
-- Name: alerts alerts_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: alerts alerts_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: alerts alerts_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.simulation_runs(simulation_run_id);


--
-- Name: alerts alerts_supersedes_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_supersedes_alert_id_fkey FOREIGN KEY (supersedes_alert_id) REFERENCES public.alerts(alert_id);


--
-- Name: analytics_runs analytics_runs_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analytics_runs
    ADD CONSTRAINT analytics_runs_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.simulation_runs(simulation_run_id);


--
-- Name: anomaly_evidence_items anomaly_evidence_items_anomaly_flag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_evidence_items
    ADD CONSTRAINT anomaly_evidence_items_anomaly_flag_id_fkey FOREIGN KEY (anomaly_flag_id) REFERENCES public.anomaly_flags(anomaly_flag_id);


--
-- Name: anomaly_flag_transactions anomaly_flag_transactions_anomaly_flag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flag_transactions
    ADD CONSTRAINT anomaly_flag_transactions_anomaly_flag_id_fkey FOREIGN KEY (anomaly_flag_id) REFERENCES public.anomaly_flags(anomaly_flag_id);


--
-- Name: anomaly_flag_transactions anomaly_flag_transactions_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flag_transactions
    ADD CONSTRAINT anomaly_flag_transactions_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES public.transactions(transaction_id);


--
-- Name: anomaly_flags anomaly_flags_analytics_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flags
    ADD CONSTRAINT anomaly_flags_analytics_run_id_fkey FOREIGN KEY (analytics_run_id) REFERENCES public.analytics_runs(analytics_run_id);


--
-- Name: anomaly_flags anomaly_flags_anomaly_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flags
    ADD CONSTRAINT anomaly_flags_anomaly_rule_id_fkey FOREIGN KEY (anomaly_rule_id) REFERENCES public.anomaly_rules(anomaly_rule_id);


--
-- Name: anomaly_flags anomaly_flags_data_quality_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flags
    ADD CONSTRAINT anomaly_flags_data_quality_assessment_id_fkey FOREIGN KEY (data_quality_assessment_id) REFERENCES public.data_quality_assessments(data_quality_assessment_id);


--
-- Name: anomaly_flags anomaly_flags_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flags
    ADD CONSTRAINT anomaly_flags_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: anomaly_flags anomaly_flags_outlet_provider_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flags
    ADD CONSTRAINT anomaly_flags_outlet_provider_account_id_fkey FOREIGN KEY (outlet_provider_account_id) REFERENCES public.outlet_provider_accounts(outlet_provider_account_id);


--
-- Name: anomaly_flags anomaly_flags_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.anomaly_flags
    ADD CONSTRAINT anomaly_flags_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: app_users app_users_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_users
    ADD CONSTRAINT app_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id);


--
-- Name: areas areas_parent_area_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.areas
    ADD CONSTRAINT areas_parent_area_id_fkey FOREIGN KEY (parent_area_id) REFERENCES public.areas(area_id);


--
-- Name: audit_events audit_events_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.app_users(user_id);


--
-- Name: audit_events audit_events_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES public.alerts(alert_id);


--
-- Name: audit_events audit_events_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_case_id_fkey FOREIGN KEY (case_id) REFERENCES public.cases(case_id);


--
-- Name: audit_events audit_events_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: audit_events audit_events_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_events
    ADD CONSTRAINT audit_events_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: case_assignments case_assignments_assigned_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_assignments
    ADD CONSTRAINT case_assignments_assigned_by_user_id_fkey FOREIGN KEY (assigned_by_user_id) REFERENCES public.app_users(user_id);


--
-- Name: case_assignments case_assignments_assigned_to_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_assignments
    ADD CONSTRAINT case_assignments_assigned_to_user_id_fkey FOREIGN KEY (assigned_to_user_id) REFERENCES public.app_users(user_id);


--
-- Name: case_assignments case_assignments_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_assignments
    ADD CONSTRAINT case_assignments_case_id_fkey FOREIGN KEY (case_id) REFERENCES public.cases(case_id);


--
-- Name: case_assignments case_assignments_routing_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_assignments
    ADD CONSTRAINT case_assignments_routing_rule_id_fkey FOREIGN KEY (routing_rule_id) REFERENCES public.routing_rules(routing_rule_id);


--
-- Name: case_notes case_notes_author_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_notes
    ADD CONSTRAINT case_notes_author_user_id_fkey FOREIGN KEY (author_user_id) REFERENCES public.app_users(user_id);


--
-- Name: case_notes case_notes_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_notes
    ADD CONSTRAINT case_notes_case_id_fkey FOREIGN KEY (case_id) REFERENCES public.cases(case_id);


--
-- Name: case_reviews case_reviews_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_reviews
    ADD CONSTRAINT case_reviews_case_id_fkey FOREIGN KEY (case_id) REFERENCES public.cases(case_id);


--
-- Name: case_reviews case_reviews_reviewed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_reviews
    ADD CONSTRAINT case_reviews_reviewed_by_user_id_fkey FOREIGN KEY (reviewed_by_user_id) REFERENCES public.app_users(user_id);


--
-- Name: case_status_history case_status_history_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_status_history
    ADD CONSTRAINT case_status_history_case_id_fkey FOREIGN KEY (case_id) REFERENCES public.cases(case_id);


--
-- Name: case_status_history case_status_history_changed_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.case_status_history
    ADD CONSTRAINT case_status_history_changed_by_user_id_fkey FOREIGN KEY (changed_by_user_id) REFERENCES public.app_users(user_id);


--
-- Name: cases cases_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cases
    ADD CONSTRAINT cases_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES public.alerts(alert_id);


--
-- Name: cases cases_current_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cases
    ADD CONSTRAINT cases_current_owner_user_id_fkey FOREIGN KEY (current_owner_user_id) REFERENCES public.app_users(user_id);


--
-- Name: cases cases_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cases
    ADD CONSTRAINT cases_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: cases cases_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cases
    ADD CONSTRAINT cases_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: cases cases_routing_rule_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cases
    ADD CONSTRAINT cases_routing_rule_id_fkey FOREIGN KEY (routing_rule_id) REFERENCES public.routing_rules(routing_rule_id);


--
-- Name: cash_balance_snapshots cash_balance_snapshots_ingestion_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_balance_snapshots
    ADD CONSTRAINT cash_balance_snapshots_ingestion_event_id_fkey FOREIGN KEY (ingestion_event_id) REFERENCES public.ingestion_events(ingestion_event_id);


--
-- Name: cash_balance_snapshots cash_balance_snapshots_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_balance_snapshots
    ADD CONSTRAINT cash_balance_snapshots_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: cash_balance_snapshots cash_balance_snapshots_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cash_balance_snapshots
    ADD CONSTRAINT cash_balance_snapshots_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.simulation_runs(simulation_run_id);


--
-- Name: data_quality_assessments data_quality_assessments_ingestion_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_assessments
    ADD CONSTRAINT data_quality_assessments_ingestion_batch_id_fkey FOREIGN KEY (ingestion_batch_id) REFERENCES public.ingestion_batches(ingestion_batch_id);


--
-- Name: data_quality_assessments data_quality_assessments_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_assessments
    ADD CONSTRAINT data_quality_assessments_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: data_quality_assessments data_quality_assessments_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_assessments
    ADD CONSTRAINT data_quality_assessments_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: data_quality_assessments data_quality_assessments_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_assessments
    ADD CONSTRAINT data_quality_assessments_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.simulation_runs(simulation_run_id);


--
-- Name: data_quality_issues data_quality_issues_data_quality_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_quality_issues
    ADD CONSTRAINT data_quality_issues_data_quality_assessment_id_fkey FOREIGN KEY (data_quality_assessment_id) REFERENCES public.data_quality_assessments(data_quality_assessment_id);


--
-- Name: fault_injections fault_injections_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fault_injections
    ADD CONSTRAINT fault_injections_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: fault_injections fault_injections_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fault_injections
    ADD CONSTRAINT fault_injections_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: fault_injections fault_injections_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fault_injections
    ADD CONSTRAINT fault_injections_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.simulation_runs(simulation_run_id);


--
-- Name: ground_truth_labels ground_truth_labels_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ground_truth_labels
    ADD CONSTRAINT ground_truth_labels_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: ground_truth_labels ground_truth_labels_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ground_truth_labels
    ADD CONSTRAINT ground_truth_labels_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: ground_truth_labels ground_truth_labels_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ground_truth_labels
    ADD CONSTRAINT ground_truth_labels_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.simulation_runs(simulation_run_id);


--
-- Name: ground_truth_labels ground_truth_labels_validation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ground_truth_labels
    ADD CONSTRAINT ground_truth_labels_validation_run_id_fkey FOREIGN KEY (validation_run_id) REFERENCES public.validation_runs(validation_run_id);


--
-- Name: ingestion_batches ingestion_batches_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_batches
    ADD CONSTRAINT ingestion_batches_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: ingestion_batches ingestion_batches_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_batches
    ADD CONSTRAINT ingestion_batches_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: ingestion_batches ingestion_batches_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_batches
    ADD CONSTRAINT ingestion_batches_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.simulation_runs(simulation_run_id);


--
-- Name: ingestion_events ingestion_events_ingestion_batch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_events
    ADD CONSTRAINT ingestion_events_ingestion_batch_id_fkey FOREIGN KEY (ingestion_batch_id) REFERENCES public.ingestion_batches(ingestion_batch_id);


--
-- Name: liquidity_projection_quality_assessments liquidity_projection_quality_as_data_quality_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_projection_quality_assessments
    ADD CONSTRAINT liquidity_projection_quality_as_data_quality_assessment_id_fkey FOREIGN KEY (data_quality_assessment_id) REFERENCES public.data_quality_assessments(data_quality_assessment_id);


--
-- Name: liquidity_projection_quality_assessments liquidity_projection_quality_asses_liquidity_projection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_projection_quality_assessments
    ADD CONSTRAINT liquidity_projection_quality_asses_liquidity_projection_id_fkey FOREIGN KEY (liquidity_projection_id) REFERENCES public.liquidity_projections(liquidity_projection_id);


--
-- Name: liquidity_projections liquidity_projections_analytics_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_projections
    ADD CONSTRAINT liquidity_projections_analytics_run_id_fkey FOREIGN KEY (analytics_run_id) REFERENCES public.analytics_runs(analytics_run_id);


--
-- Name: liquidity_projections liquidity_projections_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_projections
    ADD CONSTRAINT liquidity_projections_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: liquidity_projections liquidity_projections_outlet_provider_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_projections
    ADD CONSTRAINT liquidity_projections_outlet_provider_account_id_fkey FOREIGN KEY (outlet_provider_account_id) REFERENCES public.outlet_provider_accounts(outlet_provider_account_id);


--
-- Name: liquidity_projections liquidity_projections_primary_data_quality_assessment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_projections
    ADD CONSTRAINT liquidity_projections_primary_data_quality_assessment_id_fkey FOREIGN KEY (primary_data_quality_assessment_id) REFERENCES public.data_quality_assessments(data_quality_assessment_id);


--
-- Name: liquidity_projections liquidity_projections_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_projections
    ADD CONSTRAINT liquidity_projections_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: liquidity_signals liquidity_signals_liquidity_projection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidity_signals
    ADD CONSTRAINT liquidity_signals_liquidity_projection_id_fkey FOREIGN KEY (liquidity_projection_id) REFERENCES public.liquidity_projections(liquidity_projection_id);


--
-- Name: metric_results metric_results_validation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.metric_results
    ADD CONSTRAINT metric_results_validation_run_id_fkey FOREIGN KEY (validation_run_id) REFERENCES public.validation_runs(validation_run_id);


--
-- Name: notifications notifications_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_case_id_fkey FOREIGN KEY (case_id) REFERENCES public.cases(case_id);


--
-- Name: notifications notifications_recipient_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_recipient_user_id_fkey FOREIGN KEY (recipient_user_id) REFERENCES public.app_users(user_id);


--
-- Name: outlet_provider_accounts outlet_provider_accounts_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.outlet_provider_accounts
    ADD CONSTRAINT outlet_provider_accounts_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: outlet_provider_accounts outlet_provider_accounts_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.outlet_provider_accounts
    ADD CONSTRAINT outlet_provider_accounts_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: outlets outlets_area_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.outlets
    ADD CONSTRAINT outlets_area_id_fkey FOREIGN KEY (area_id) REFERENCES public.areas(area_id);


--
-- Name: provider_balance_snapshots provider_balance_snapshots_ingestion_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_balance_snapshots
    ADD CONSTRAINT provider_balance_snapshots_ingestion_event_id_fkey FOREIGN KEY (ingestion_event_id) REFERENCES public.ingestion_events(ingestion_event_id);


--
-- Name: provider_balance_snapshots provider_balance_snapshots_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_balance_snapshots
    ADD CONSTRAINT provider_balance_snapshots_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: provider_balance_snapshots provider_balance_snapshots_outlet_provider_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_balance_snapshots
    ADD CONSTRAINT provider_balance_snapshots_outlet_provider_account_id_fkey FOREIGN KEY (outlet_provider_account_id) REFERENCES public.outlet_provider_accounts(outlet_provider_account_id);


--
-- Name: provider_balance_snapshots provider_balance_snapshots_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_balance_snapshots
    ADD CONSTRAINT provider_balance_snapshots_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: provider_balance_snapshots provider_balance_snapshots_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.provider_balance_snapshots
    ADD CONSTRAINT provider_balance_snapshots_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.simulation_runs(simulation_run_id);


--
-- Name: routing_rules routing_rules_area_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routing_rules
    ADD CONSTRAINT routing_rules_area_id_fkey FOREIGN KEY (area_id) REFERENCES public.areas(area_id);


--
-- Name: routing_rules routing_rules_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routing_rules
    ADD CONSTRAINT routing_rules_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: simulation_runs simulation_runs_scenario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.simulation_runs
    ADD CONSTRAINT simulation_runs_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES public.simulation_scenarios(scenario_id);


--
-- Name: simulation_runs simulation_runs_started_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.simulation_runs
    ADD CONSTRAINT simulation_runs_started_by_user_id_fkey FOREIGN KEY (started_by_user_id) REFERENCES public.app_users(user_id);


--
-- Name: transactions transactions_ingestion_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_ingestion_event_id_fkey FOREIGN KEY (ingestion_event_id) REFERENCES public.ingestion_events(ingestion_event_id);


--
-- Name: transactions transactions_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: transactions transactions_outlet_provider_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_outlet_provider_account_id_fkey FOREIGN KEY (outlet_provider_account_id) REFERENCES public.outlet_provider_accounts(outlet_provider_account_id);


--
-- Name: transactions transactions_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: transactions transactions_simulation_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_simulation_run_id_fkey FOREIGN KEY (simulation_run_id) REFERENCES public.simulation_runs(simulation_run_id);


--
-- Name: user_access_scopes user_access_scopes_area_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_access_scopes
    ADD CONSTRAINT user_access_scopes_area_id_fkey FOREIGN KEY (area_id) REFERENCES public.areas(area_id);


--
-- Name: user_access_scopes user_access_scopes_outlet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_access_scopes
    ADD CONSTRAINT user_access_scopes_outlet_id_fkey FOREIGN KEY (outlet_id) REFERENCES public.outlets(outlet_id);


--
-- Name: user_access_scopes user_access_scopes_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_access_scopes
    ADD CONSTRAINT user_access_scopes_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(provider_id);


--
-- Name: user_access_scopes user_access_scopes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_access_scopes
    ADD CONSTRAINT user_access_scopes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_users(user_id);


--
-- Name: validation_runs validation_runs_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.validation_runs
    ADD CONSTRAINT validation_runs_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.app_users(user_id);


--
-- Name: alert_anomaly_flags; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.alert_anomaly_flags ENABLE ROW LEVEL SECURITY;

--
-- Name: alert_explanations; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.alert_explanations ENABLE ROW LEVEL SECURITY;

--
-- Name: alert_liquidity_projections; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.alert_liquidity_projections ENABLE ROW LEVEL SECURITY;

--
-- Name: alert_quality_assessments; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.alert_quality_assessments ENABLE ROW LEVEL SECURITY;

--
-- Name: alerts; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;

--
-- Name: analytics_runs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.analytics_runs ENABLE ROW LEVEL SECURITY;

--
-- Name: anomaly_evidence_items; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.anomaly_evidence_items ENABLE ROW LEVEL SECURITY;

--
-- Name: anomaly_flag_transactions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.anomaly_flag_transactions ENABLE ROW LEVEL SECURITY;

--
-- Name: anomaly_flags; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.anomaly_flags ENABLE ROW LEVEL SECURITY;

--
-- Name: app_users; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.app_users ENABLE ROW LEVEL SECURITY;

--
-- Name: audit_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;

--
-- Name: case_assignments; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.case_assignments ENABLE ROW LEVEL SECURITY;

--
-- Name: case_notes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.case_notes ENABLE ROW LEVEL SECURITY;

--
-- Name: case_reviews; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.case_reviews ENABLE ROW LEVEL SECURITY;

--
-- Name: case_status_history; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.case_status_history ENABLE ROW LEVEL SECURITY;

--
-- Name: cases; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;

--
-- Name: cash_balance_snapshots; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.cash_balance_snapshots ENABLE ROW LEVEL SECURITY;

--
-- Name: data_quality_assessments; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.data_quality_assessments ENABLE ROW LEVEL SECURITY;

--
-- Name: data_quality_issues; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.data_quality_issues ENABLE ROW LEVEL SECURITY;

--
-- Name: fault_injections; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.fault_injections ENABLE ROW LEVEL SECURITY;

--
-- Name: ingestion_batches; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.ingestion_batches ENABLE ROW LEVEL SECURITY;

--
-- Name: ingestion_events; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.ingestion_events ENABLE ROW LEVEL SECURITY;

--
-- Name: liquidity_projection_quality_assessments; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.liquidity_projection_quality_assessments ENABLE ROW LEVEL SECURITY;

--
-- Name: liquidity_projections; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.liquidity_projections ENABLE ROW LEVEL SECURITY;

--
-- Name: liquidity_signals; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.liquidity_signals ENABLE ROW LEVEL SECURITY;

--
-- Name: notifications; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

--
-- Name: provider_balance_snapshots; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.provider_balance_snapshots ENABLE ROW LEVEL SECURITY;

--
-- Name: alert_anomaly_flags sel_aaf; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_aaf ON public.alert_anomaly_flags FOR SELECT TO authenticated USING (app.has_alert_access(alert_id));


--
-- Name: anomaly_evidence_items sel_aei; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_aei ON public.anomaly_evidence_items FOR SELECT TO authenticated USING (app.has_flag_access(anomaly_flag_id));


--
-- Name: anomaly_flag_transactions sel_aft; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_aft ON public.anomaly_flag_transactions FOR SELECT TO authenticated USING (app.has_flag_access(anomaly_flag_id));


--
-- Name: alert_explanations sel_alert_explanations; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_alert_explanations ON public.alert_explanations FOR SELECT TO authenticated USING (app.has_alert_access(alert_id));


--
-- Name: alerts sel_alerts; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_alerts ON public.alerts FOR SELECT TO authenticated USING (
CASE
    WHEN (provider_id IS NULL) THEN app.has_outlet_scope(outlet_id)
    ELSE app.has_provider_scope(provider_id, outlet_id)
END);


--
-- Name: alert_liquidity_projections sel_alp; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_alp ON public.alert_liquidity_projections FOR SELECT TO authenticated USING (app.has_alert_access(alert_id));


--
-- Name: analytics_runs sel_analytics_runs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_analytics_runs ON public.analytics_runs FOR SELECT TO authenticated USING (true);


--
-- Name: anomaly_flags sel_anomaly_flags; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_anomaly_flags ON public.anomaly_flags FOR SELECT TO authenticated USING (app.has_provider_scope(provider_id, outlet_id));


--
-- Name: app_users sel_app_users; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_app_users ON public.app_users FOR SELECT TO authenticated USING ((user_id = app.current_user_id()));


--
-- Name: alert_quality_assessments sel_aqa; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_aqa ON public.alert_quality_assessments FOR SELECT TO authenticated USING (app.has_alert_access(alert_id));


--
-- Name: audit_events sel_audit_events; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_audit_events ON public.audit_events FOR SELECT TO authenticated USING ((((provider_id IS NOT NULL) AND app.has_provider_scope(provider_id, outlet_id)) OR ((provider_id IS NULL) AND (outlet_id IS NOT NULL) AND app.has_outlet_scope(outlet_id))));


--
-- Name: case_assignments sel_case_assignments; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_case_assignments ON public.case_assignments FOR SELECT TO authenticated USING (app.has_case_access(case_id));


--
-- Name: case_notes sel_case_notes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_case_notes ON public.case_notes FOR SELECT TO authenticated USING (app.has_case_access(case_id));


--
-- Name: case_reviews sel_case_reviews; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_case_reviews ON public.case_reviews FOR SELECT TO authenticated USING (app.has_case_access(case_id));


--
-- Name: case_status_history sel_case_status_history; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_case_status_history ON public.case_status_history FOR SELECT TO authenticated USING (app.has_case_access(case_id));


--
-- Name: cases sel_cases; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_cases ON public.cases FOR SELECT TO authenticated USING (
CASE
    WHEN (provider_id IS NULL) THEN app.has_outlet_scope(outlet_id)
    ELSE app.has_provider_scope(provider_id, outlet_id)
END);


--
-- Name: cash_balance_snapshots sel_cash; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_cash ON public.cash_balance_snapshots FOR SELECT TO authenticated USING (app.has_outlet_scope(outlet_id));


--
-- Name: data_quality_assessments sel_dqa; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_dqa ON public.data_quality_assessments FOR SELECT TO authenticated USING (app.has_provider_scope(provider_id, outlet_id));


--
-- Name: data_quality_issues sel_dqi; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_dqi ON public.data_quality_issues FOR SELECT TO authenticated USING (app.has_assessment_access(data_quality_assessment_id));


--
-- Name: fault_injections sel_fault_injections; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_fault_injections ON public.fault_injections FOR SELECT TO authenticated USING (
CASE
    WHEN (provider_id IS NULL) THEN app.has_outlet_scope(outlet_id)
    ELSE app.has_provider_scope(provider_id, outlet_id)
END);


--
-- Name: ingestion_batches sel_ingestion_batches; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_ingestion_batches ON public.ingestion_batches FOR SELECT TO authenticated USING (app.has_provider_scope(provider_id, outlet_id));


--
-- Name: ingestion_events sel_ingestion_events; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_ingestion_events ON public.ingestion_events FOR SELECT TO authenticated USING (app.has_batch_access(ingestion_batch_id));


--
-- Name: liquidity_projections sel_lp; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_lp ON public.liquidity_projections FOR SELECT TO authenticated USING (
CASE
    WHEN ((reserve_type)::text = 'shared_cash'::text) THEN app.has_outlet_scope(outlet_id)
    ELSE app.has_provider_scope(provider_id, outlet_id)
END);


--
-- Name: liquidity_projection_quality_assessments sel_lpqa; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_lpqa ON public.liquidity_projection_quality_assessments FOR SELECT TO authenticated USING (app.has_projection_access(liquidity_projection_id));


--
-- Name: liquidity_signals sel_lsig; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_lsig ON public.liquidity_signals FOR SELECT TO authenticated USING (app.has_projection_access(liquidity_projection_id));


--
-- Name: notifications sel_notifications; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_notifications ON public.notifications FOR SELECT TO authenticated USING (((recipient_user_id = app.current_user_id()) OR app.has_case_access(case_id)));


--
-- Name: provider_balance_snapshots sel_pbs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_pbs ON public.provider_balance_snapshots FOR SELECT TO authenticated USING (app.has_provider_scope(provider_id, outlet_id));


--
-- Name: simulation_runs sel_simulation_runs; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_simulation_runs ON public.simulation_runs FOR SELECT TO authenticated USING (true);


--
-- Name: transactions sel_transactions; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_transactions ON public.transactions FOR SELECT TO authenticated USING (app.has_provider_scope(provider_id, outlet_id));


--
-- Name: user_access_scopes sel_user_access_scopes; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY sel_user_access_scopes ON public.user_access_scopes FOR SELECT TO authenticated USING ((user_id = app.current_user_id()));


--
-- Name: simulation_runs; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.simulation_runs ENABLE ROW LEVEL SECURITY;

--
-- Name: transactions; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

--
-- Name: user_access_scopes; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public.user_access_scopes ENABLE ROW LEVEL SECURITY;

--
-- Name: SCHEMA app; Type: ACL; Schema: -; Owner: -
--

GRANT USAGE ON SCHEMA app TO anon;
GRANT USAGE ON SCHEMA app TO authenticated;
GRANT USAGE ON SCHEMA app TO service_role;


--
-- Name: SCHEMA auth; Type: ACL; Schema: -; Owner: -
--

GRANT USAGE ON SCHEMA auth TO anon;
GRANT USAGE ON SCHEMA auth TO authenticated;
GRANT USAGE ON SCHEMA auth TO service_role;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: -
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO service_role;


--
-- Name: FUNCTION current_user_id(); Type: ACL; Schema: app; Owner: -
--

GRANT ALL ON FUNCTION app.current_user_id() TO anon;
GRANT ALL ON FUNCTION app.current_user_id() TO authenticated;
GRANT ALL ON FUNCTION app.current_user_id() TO service_role;


--
-- Name: FUNCTION has_alert_access(p_alert uuid); Type: ACL; Schema: app; Owner: -
--

GRANT ALL ON FUNCTION app.has_alert_access(p_alert uuid) TO anon;
GRANT ALL ON FUNCTION app.has_alert_access(p_alert uuid) TO authenticated;
GRANT ALL ON FUNCTION app.has_alert_access(p_alert uuid) TO service_role;


--
-- Name: FUNCTION has_assessment_access(p_assessment uuid); Type: ACL; Schema: app; Owner: -
--

GRANT ALL ON FUNCTION app.has_assessment_access(p_assessment uuid) TO anon;
GRANT ALL ON FUNCTION app.has_assessment_access(p_assessment uuid) TO authenticated;
GRANT ALL ON FUNCTION app.has_assessment_access(p_assessment uuid) TO service_role;


--
-- Name: FUNCTION has_batch_access(p_batch uuid); Type: ACL; Schema: app; Owner: -
--

GRANT ALL ON FUNCTION app.has_batch_access(p_batch uuid) TO anon;
GRANT ALL ON FUNCTION app.has_batch_access(p_batch uuid) TO authenticated;
GRANT ALL ON FUNCTION app.has_batch_access(p_batch uuid) TO service_role;


--
-- Name: FUNCTION has_case_access(p_case uuid); Type: ACL; Schema: app; Owner: -
--

GRANT ALL ON FUNCTION app.has_case_access(p_case uuid) TO anon;
GRANT ALL ON FUNCTION app.has_case_access(p_case uuid) TO authenticated;
GRANT ALL ON FUNCTION app.has_case_access(p_case uuid) TO service_role;


--
-- Name: FUNCTION has_flag_access(p_flag uuid); Type: ACL; Schema: app; Owner: -
--

GRANT ALL ON FUNCTION app.has_flag_access(p_flag uuid) TO anon;
GRANT ALL ON FUNCTION app.has_flag_access(p_flag uuid) TO authenticated;
GRANT ALL ON FUNCTION app.has_flag_access(p_flag uuid) TO service_role;


--
-- Name: FUNCTION has_outlet_scope(p_outlet uuid); Type: ACL; Schema: app; Owner: -
--

GRANT ALL ON FUNCTION app.has_outlet_scope(p_outlet uuid) TO anon;
GRANT ALL ON FUNCTION app.has_outlet_scope(p_outlet uuid) TO authenticated;
GRANT ALL ON FUNCTION app.has_outlet_scope(p_outlet uuid) TO service_role;


--
-- Name: FUNCTION has_projection_access(p_projection uuid); Type: ACL; Schema: app; Owner: -
--

GRANT ALL ON FUNCTION app.has_projection_access(p_projection uuid) TO anon;
GRANT ALL ON FUNCTION app.has_projection_access(p_projection uuid) TO authenticated;
GRANT ALL ON FUNCTION app.has_projection_access(p_projection uuid) TO service_role;


--
-- Name: FUNCTION has_provider_scope(p_provider uuid, p_outlet uuid); Type: ACL; Schema: app; Owner: -
--

GRANT ALL ON FUNCTION app.has_provider_scope(p_provider uuid, p_outlet uuid) TO anon;
GRANT ALL ON FUNCTION app.has_provider_scope(p_provider uuid, p_outlet uuid) TO authenticated;
GRANT ALL ON FUNCTION app.has_provider_scope(p_provider uuid, p_outlet uuid) TO service_role;


--
-- Name: TABLE alert_anomaly_flags; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.alert_anomaly_flags TO service_role;
GRANT SELECT ON TABLE public.alert_anomaly_flags TO authenticated;


--
-- Name: TABLE alert_explanations; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.alert_explanations TO service_role;
GRANT SELECT ON TABLE public.alert_explanations TO authenticated;


--
-- Name: TABLE alert_liquidity_projections; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.alert_liquidity_projections TO service_role;
GRANT SELECT ON TABLE public.alert_liquidity_projections TO authenticated;


--
-- Name: TABLE alert_quality_assessments; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.alert_quality_assessments TO service_role;
GRANT SELECT ON TABLE public.alert_quality_assessments TO authenticated;


--
-- Name: TABLE alerts; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.alerts TO service_role;
GRANT SELECT ON TABLE public.alerts TO authenticated;


--
-- Name: TABLE analytics_runs; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.analytics_runs TO service_role;
GRANT SELECT ON TABLE public.analytics_runs TO authenticated;


--
-- Name: TABLE anomaly_evidence_items; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.anomaly_evidence_items TO service_role;
GRANT SELECT ON TABLE public.anomaly_evidence_items TO authenticated;


--
-- Name: TABLE anomaly_flag_transactions; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.anomaly_flag_transactions TO service_role;
GRANT SELECT ON TABLE public.anomaly_flag_transactions TO authenticated;


--
-- Name: TABLE anomaly_flags; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.anomaly_flags TO service_role;
GRANT SELECT ON TABLE public.anomaly_flags TO authenticated;


--
-- Name: TABLE anomaly_rules; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.anomaly_rules TO service_role;
GRANT SELECT ON TABLE public.anomaly_rules TO authenticated;
GRANT SELECT ON TABLE public.anomaly_rules TO anon;


--
-- Name: TABLE app_users; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.app_users TO service_role;
GRANT SELECT ON TABLE public.app_users TO authenticated;


--
-- Name: TABLE areas; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.areas TO service_role;
GRANT SELECT ON TABLE public.areas TO authenticated;
GRANT SELECT ON TABLE public.areas TO anon;


--
-- Name: TABLE audit_events; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.audit_events TO service_role;
GRANT SELECT ON TABLE public.audit_events TO authenticated;


--
-- Name: TABLE case_assignments; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.case_assignments TO service_role;
GRANT SELECT ON TABLE public.case_assignments TO authenticated;


--
-- Name: TABLE case_notes; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.case_notes TO service_role;
GRANT SELECT ON TABLE public.case_notes TO authenticated;


--
-- Name: TABLE case_reviews; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.case_reviews TO service_role;
GRANT SELECT ON TABLE public.case_reviews TO authenticated;


--
-- Name: TABLE case_status_history; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.case_status_history TO service_role;
GRANT SELECT ON TABLE public.case_status_history TO authenticated;


--
-- Name: TABLE cases; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.cases TO service_role;
GRANT SELECT ON TABLE public.cases TO authenticated;


--
-- Name: TABLE cash_balance_snapshots; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.cash_balance_snapshots TO service_role;
GRANT SELECT ON TABLE public.cash_balance_snapshots TO authenticated;


--
-- Name: TABLE data_quality_assessments; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.data_quality_assessments TO service_role;
GRANT SELECT ON TABLE public.data_quality_assessments TO authenticated;


--
-- Name: TABLE data_quality_issues; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.data_quality_issues TO service_role;
GRANT SELECT ON TABLE public.data_quality_issues TO authenticated;


--
-- Name: TABLE explanation_templates; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.explanation_templates TO service_role;
GRANT SELECT ON TABLE public.explanation_templates TO authenticated;
GRANT SELECT ON TABLE public.explanation_templates TO anon;


--
-- Name: TABLE fault_injections; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.fault_injections TO service_role;
GRANT SELECT ON TABLE public.fault_injections TO authenticated;


--
-- Name: TABLE ground_truth_labels; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.ground_truth_labels TO service_role;
GRANT SELECT ON TABLE public.ground_truth_labels TO authenticated;


--
-- Name: TABLE ingestion_batches; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.ingestion_batches TO service_role;
GRANT SELECT ON TABLE public.ingestion_batches TO authenticated;


--
-- Name: TABLE ingestion_events; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.ingestion_events TO service_role;
GRANT SELECT ON TABLE public.ingestion_events TO authenticated;


--
-- Name: TABLE liquidity_projection_quality_assessments; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.liquidity_projection_quality_assessments TO service_role;
GRANT SELECT ON TABLE public.liquidity_projection_quality_assessments TO authenticated;


--
-- Name: TABLE liquidity_projections; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.liquidity_projections TO service_role;
GRANT SELECT ON TABLE public.liquidity_projections TO authenticated;


--
-- Name: TABLE liquidity_signals; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.liquidity_signals TO service_role;
GRANT SELECT ON TABLE public.liquidity_signals TO authenticated;


--
-- Name: TABLE metric_results; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.metric_results TO service_role;
GRANT SELECT ON TABLE public.metric_results TO authenticated;


--
-- Name: TABLE notifications; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.notifications TO service_role;
GRANT SELECT ON TABLE public.notifications TO authenticated;


--
-- Name: TABLE outlet_provider_accounts; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.outlet_provider_accounts TO service_role;
GRANT SELECT ON TABLE public.outlet_provider_accounts TO authenticated;


--
-- Name: TABLE outlets; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.outlets TO service_role;
GRANT SELECT ON TABLE public.outlets TO authenticated;


--
-- Name: TABLE provider_balance_snapshots; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.provider_balance_snapshots TO service_role;
GRANT SELECT ON TABLE public.provider_balance_snapshots TO authenticated;


--
-- Name: TABLE providers; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.providers TO service_role;
GRANT SELECT ON TABLE public.providers TO authenticated;
GRANT SELECT ON TABLE public.providers TO anon;


--
-- Name: TABLE routing_rules; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.routing_rules TO service_role;
GRANT SELECT ON TABLE public.routing_rules TO authenticated;
GRANT SELECT ON TABLE public.routing_rules TO anon;


--
-- Name: TABLE schema_migrations; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.schema_migrations TO service_role;
GRANT SELECT ON TABLE public.schema_migrations TO authenticated;


--
-- Name: TABLE simulation_runs; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.simulation_runs TO service_role;
GRANT SELECT ON TABLE public.simulation_runs TO authenticated;


--
-- Name: TABLE simulation_scenarios; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.simulation_scenarios TO service_role;
GRANT SELECT ON TABLE public.simulation_scenarios TO authenticated;
GRANT SELECT ON TABLE public.simulation_scenarios TO anon;


--
-- Name: TABLE transactions; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.transactions TO service_role;
GRANT SELECT ON TABLE public.transactions TO authenticated;


--
-- Name: TABLE user_access_scopes; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.user_access_scopes TO service_role;
GRANT SELECT ON TABLE public.user_access_scopes TO authenticated;


--
-- Name: TABLE v_case_timeline; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.v_case_timeline TO service_role;
GRANT SELECT ON TABLE public.v_case_timeline TO authenticated;


--
-- Name: TABLE v_current_feed_health; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.v_current_feed_health TO service_role;
GRANT SELECT ON TABLE public.v_current_feed_health TO authenticated;


--
-- Name: TABLE v_latest_cash_balance; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.v_latest_cash_balance TO service_role;
GRANT SELECT ON TABLE public.v_latest_cash_balance TO authenticated;


--
-- Name: TABLE v_latest_liquidity_projections; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.v_latest_liquidity_projections TO service_role;
GRANT SELECT ON TABLE public.v_latest_liquidity_projections TO authenticated;


--
-- Name: TABLE v_latest_provider_balances; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.v_latest_provider_balances TO service_role;
GRANT SELECT ON TABLE public.v_latest_provider_balances TO authenticated;


--
-- Name: TABLE v_outlet_dashboard; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.v_outlet_dashboard TO service_role;
GRANT SELECT ON TABLE public.v_outlet_dashboard TO authenticated;


--
-- Name: TABLE validation_runs; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.validation_runs TO service_role;
GRANT SELECT ON TABLE public.validation_runs TO authenticated;


--
-- Name: TABLE v_validation_summary; Type: ACL; Schema: public; Owner: -
--

GRANT ALL ON TABLE public.v_validation_summary TO service_role;
GRANT SELECT ON TABLE public.v_validation_summary TO authenticated;


--
-- PostgreSQL database dump complete
--

