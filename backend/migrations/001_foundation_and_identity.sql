-- =============================================================================
-- Migration 001 — Foundation and Identity
-- Source of truth: docs/schema.md §3 (conventions), §4 (enumerations),
--                  §6 (reference/outlet/authorization tables), §20.1.
-- Forward-only. Pure DDL (reference/demo data lives in backend/seeds/*, ADR 0003).
-- Enumerations are CHECK-constrained DOMAINs over text (ADR 0001).
-- auth.users / auth.uid() are shimmed only when absent so the chain also applies
-- on plain PostgreSQL; Supabase provides the real objects (ADR 0002 / 0004).
-- =============================================================================

-- --- Extensions --------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- gen_random_uuid()

-- --- Guarded Supabase auth shim (no-op on Supabase) --------------------------
CREATE SCHEMA IF NOT EXISTS auth;

DO $do$
BEGIN
  IF to_regclass('auth.users') IS NULL THEN
    CREATE TABLE auth.users (
      id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      email      text,
      created_at timestamptz NOT NULL DEFAULT now()
    );
  END IF;
END
$do$;

DO $do$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'auth' AND p.proname = 'uid'
  ) THEN
    EXECUTE $fn$
      CREATE FUNCTION auth.uid() RETURNS uuid
      LANGUAGE sql STABLE AS $body$
        SELECT nullif(
          current_setting('request.jwt.claims', true)::json ->> 'sub', ''
        )::uuid
      $body$
    $fn$;
  END IF;
END
$do$;

-- =============================================================================
-- Enumerations as constrained-text DOMAINs (docs/schema.md §4, ADR 0001)
-- =============================================================================
CREATE DOMAIN provider_code        AS text CHECK (VALUE IN ('bkash','nagad','rocket'));
CREATE DOMAIN app_role             AS text CHECK (VALUE IN ('agent','field_officer','area_manager','provider_ops','risk_analyst','management','admin'));
CREATE DOMAIN transaction_type     AS text CHECK (VALUE IN ('cash_in','cash_out','payment','refund','adjustment'));
CREATE DOMAIN transaction_status   AS text CHECK (VALUE IN ('pending','completed','failed','reversed'));
CREATE DOMAIN feed_event_type      AS text CHECK (VALUE IN ('transaction','provider_balance','cash_balance','heartbeat'));
CREATE DOMAIN normalization_status AS text CHECK (VALUE IN ('pending','normalized','rejected'));
CREATE DOMAIN feed_health_status   AS text CHECK (VALUE IN ('fresh','stale','missing','conflicting'));
CREATE DOMAIN quality_issue_type   AS text CHECK (VALUE IN ('late_arrival','missing_feed','missing_field','conflicting_snapshot','impossible_transition','insufficient_samples','malformed_payload'));
CREATE DOMAIN reserve_type         AS text CHECK (VALUE IN ('shared_cash','provider_e_money'));
CREATE DOMAIN confidence_level     AS text CHECK (VALUE IN ('high','medium','low','unavailable'));
CREATE DOMAIN analytics_engine     AS text CHECK (VALUE IN ('liquidity','anomaly','data_quality'));
CREATE DOMAIN anomaly_pattern      AS text CHECK (VALUE IN ('near_identical_amounts','velocity_spike','transaction_splitting','circular_activity','balance_inconsistency','time_anomaly','failure_rate'));
CREATE DOMAIN anomaly_disposition  AS text CHECK (VALUE IN ('requires_review','suppressed_data_quality','dismissed_benign','confirmed_unusual','inconclusive'));
CREATE DOMAIN review_outcome       AS text CHECK (VALUE IN ('benign_operational','requires_follow_up','data_quality_issue','confirmed_unusual','inconclusive'));
CREATE DOMAIN alert_type           AS text CHECK (VALUE IN ('liquidity','anomaly','combined','data_quality'));
CREATE DOMAIN severity             AS text CHECK (VALUE IN ('info','low','medium','high','critical'));
CREATE DOMAIN alert_state          AS text CHECK (VALUE IN ('active','superseded','closed'));
CREATE DOMAIN case_status          AS text CHECK (VALUE IN ('open','acknowledged','escalated','resolved'));
CREATE DOMAIN assignment_reason    AS text CHECK (VALUE IN ('initial_route','manual_assign','reassign','escalation'));
CREATE DOMAIN notification_channel AS text CHECK (VALUE IN ('in_app','webhook','email_stub'));
CREATE DOMAIN notification_status  AS text CHECK (VALUE IN ('queued','delivered','read','failed'));
CREATE DOMAIN locale_code          AS text CHECK (VALUE IN ('en','bn','bn_latn'));
CREATE DOMAIN fault_type           AS text CHECK (VALUE IN ('delay','missing_feed','missing_field','conflicting_balance','malformed_payload'));
CREATE DOMAIN validation_split     AS text CHECK (VALUE IN ('tuning','held_out','demo'));
CREATE DOMAIN area_level           AS text CHECK (VALUE IN ('territory','area','thana','district','region'));

-- Score convention: numeric(5,4) constrained to 0..1 (docs/schema.md §3)
CREATE DOMAIN score_unit           AS numeric(5,4) CHECK (VALUE >= 0 AND VALUE <= 1);
-- Currency convention: MVP allows only BDT (docs/schema.md §3)
CREATE DOMAIN currency_bdt         AS char(3) CHECK (VALUE = 'BDT');

-- =============================================================================
-- Shared utility: updated_at touch trigger (docs/schema.md §3, mutation audit)
-- =============================================================================
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END
$$;

-- =============================================================================
-- 6.1 areas — MVP foundation (self-referential hierarchy, cycles restricted)
-- =============================================================================
CREATE TABLE areas (
  area_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_area_id uuid REFERENCES areas(area_id),
  code           text NOT NULL UNIQUE,
  name           text NOT NULL,
  level          area_level NOT NULL,
  is_active      boolean NOT NULL DEFAULT true,
  created_at     timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT areas_no_self_parent CHECK (parent_area_id IS NULL OR parent_area_id <> area_id)
);

-- Prevent hierarchy cycles (docs/schema.md §6.1 "restrict cycles").
CREATE OR REPLACE FUNCTION areas_prevent_cycle() RETURNS trigger
LANGUAGE plpgsql AS $$
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

CREATE TRIGGER trg_areas_prevent_cycle
  BEFORE INSERT OR UPDATE OF parent_area_id ON areas
  FOR EACH ROW EXECUTE FUNCTION areas_prevent_cycle();

-- =============================================================================
-- 6.2 providers — MVP foundation (seed exactly bkash/nagad/rocket)
-- =============================================================================
CREATE TABLE providers (
  provider_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code          provider_code NOT NULL UNIQUE,
  display_name  text NOT NULL,
  display_color text,
  is_simulated  boolean NOT NULL DEFAULT true,
  is_active     boolean NOT NULL DEFAULT true,
  created_at    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT providers_must_be_simulated CHECK (is_simulated)
);

-- =============================================================================
-- 6.3 outlets — MVP foundation (synthetic operational entity)
-- =============================================================================
CREATE TABLE outlets (
  outlet_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  synthetic_code text NOT NULL UNIQUE,
  display_name   text NOT NULL,
  area_id        uuid NOT NULL REFERENCES areas(area_id),
  currency_code  currency_bdt NOT NULL DEFAULT 'BDT',
  latitude       numeric(9,6),
  longitude      numeric(9,6),
  is_synthetic   boolean NOT NULL DEFAULT true,
  is_active      boolean NOT NULL DEFAULT true,
  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT outlets_must_be_synthetic CHECK (is_synthetic)
);

CREATE TRIGGER trg_outlets_updated_at
  BEFORE UPDATE ON outlets FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 6.4 outlet_provider_accounts — MVP foundation (per-provider e-money position)
-- =============================================================================
CREATE TABLE outlet_provider_accounts (
  outlet_provider_account_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  outlet_id             uuid NOT NULL REFERENCES outlets(outlet_id),
  provider_id           uuid NOT NULL REFERENCES providers(provider_id),
  synthetic_account_ref text NOT NULL,
  is_active             boolean NOT NULL DEFAULT true,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_opa_outlet_provider UNIQUE (outlet_id, provider_id),
  CONSTRAINT uq_opa_provider_ref    UNIQUE (provider_id, synthetic_account_ref)
);

CREATE TRIGGER trg_opa_updated_at
  BEFORE UPDATE ON outlet_provider_accounts FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 6.5 app_users — application profile for a Supabase Auth identity
-- (no password/token/PIN/OTP columns — docs/schema.md §6.5)
-- =============================================================================
CREATE TABLE app_users (
  user_id          uuid PRIMARY KEY REFERENCES auth.users(id),
  display_name     text,
  preferred_locale locale_code NOT NULL DEFAULT 'en',
  is_demo_user     boolean NOT NULL DEFAULT true,
  is_active        boolean NOT NULL DEFAULT true,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TRIGGER trg_app_users_updated_at
  BEFORE UPDATE ON app_users FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 6.6 user_access_scopes — source of truth for provider-boundary checks
-- Role-shape rules enforced as a row CHECK; a missing provider scope is NEVER a
-- wildcard (RLS in 006 treats absence as deny).
-- =============================================================================
CREATE TABLE user_access_scopes (
  user_access_scope_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES app_users(user_id),
  role        app_role NOT NULL,
  provider_id uuid REFERENCES providers(provider_id),
  area_id     uuid REFERENCES areas(area_id),
  outlet_id   uuid REFERENCES outlets(outlet_id),
  created_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uas_role_shape CHECK (
    (role <> 'agent'                                OR outlet_id   IS NOT NULL) AND
    (role NOT IN ('provider_ops','risk_analyst')    OR provider_id IS NOT NULL) AND
    (role NOT IN ('field_officer','area_manager')   OR area_id     IS NOT NULL)
  ),
  CONSTRAINT uq_uas_assignment
    UNIQUE NULLS NOT DISTINCT (user_id, role, provider_id, area_id, outlet_id)
);
