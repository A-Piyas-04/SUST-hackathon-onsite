-- =============================================================================
-- Migration 002 — Simulation, Ingestion, and Ledger
-- Source of truth: docs/schema.md §7 (simulation/ingestion), §8 (ledger),
--                  §13 (integrity invariants 1-7).
-- Introduces the append-only guard, provider/outlet<->account consistency, and
-- rejected-ingestion protections reused by later migrations.
-- =============================================================================

-- --- Shared guard: append-only tables reject UPDATE/DELETE (docs §3, §8, §13.3)
CREATE OR REPLACE FUNCTION reject_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'append-only table %.% forbids %',
    TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP
    USING ERRCODE = 'restrict_violation';
  RETURN NULL;
END
$$;

-- --- Shared guard: denormalized provider_id/outlet_id must match the account
-- (docs/schema.md §13.1-2). Reused by provider_balance_snapshots, transactions
-- and (in 003) anomaly_flags.
CREATE OR REPLACE FUNCTION enforce_account_consistency() RETURNS trigger
LANGUAGE plpgsql AS $$
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

-- --- Shared guard: a rejected ingestion event cannot become trusted ledger data
-- (docs/schema.md §7.5, §13.6)
CREATE OR REPLACE FUNCTION reject_ledger_from_rejected_event() RETURNS trigger
LANGUAGE plpgsql AS $$
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

-- =============================================================================
-- 7.1 simulation_scenarios
-- =============================================================================
CREATE TABLE simulation_scenarios (
  scenario_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code             text NOT NULL UNIQUE
                     CHECK (code IN ('normal','scenario_a','scenario_b','scenario_c','scenario_d')),
  name             text NOT NULL,
  description      text NOT NULL,
  default_seed     bigint NOT NULL,
  default_config   jsonb NOT NULL DEFAULT '{}'::jsonb,
  validation_split validation_split NOT NULL,
  is_active        boolean NOT NULL DEFAULT true,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_scenarios_updated_at
  BEFORE UPDATE ON simulation_scenarios FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- =============================================================================
-- 7.2 simulation_runs
-- =============================================================================
CREATE TABLE simulation_runs (
  simulation_run_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scenario_id        uuid NOT NULL REFERENCES simulation_scenarios(scenario_id),
  seed               bigint NOT NULL,
  config_snapshot    jsonb NOT NULL,
  status             text NOT NULL DEFAULT 'queued'
                       CHECK (status IN ('queued','running','completed','failed','reset')),
  started_by_user_id uuid REFERENCES app_users(user_id),
  started_at         timestamptz NOT NULL DEFAULT now(),
  completed_at       timestamptz,
  error_summary      text
);

-- =============================================================================
-- 7.3 fault_injections
-- =============================================================================
CREATE TABLE fault_injections (
  fault_injection_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  simulation_run_id  uuid NOT NULL REFERENCES simulation_runs(simulation_run_id),
  outlet_id          uuid NOT NULL REFERENCES outlets(outlet_id),
  provider_id        uuid REFERENCES providers(provider_id),
  fault_type         fault_type NOT NULL,
  parameters         jsonb NOT NULL DEFAULT '{}'::jsonb,
  scheduled_at       timestamptz NOT NULL DEFAULT now(),
  applied_at         timestamptz,
  ended_at           timestamptz,
  is_enabled         boolean NOT NULL DEFAULT true
);

-- =============================================================================
-- 7.4 ingestion_batches
-- =============================================================================
CREATE TABLE ingestion_batches (
  ingestion_batch_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  simulation_run_id    uuid NOT NULL REFERENCES simulation_runs(simulation_run_id),
  outlet_id            uuid NOT NULL REFERENCES outlets(outlet_id),
  provider_id          uuid NOT NULL REFERENCES providers(provider_id),
  source_batch_ref     text NOT NULL,
  source_generated_at  timestamptz,
  received_at          timestamptz NOT NULL,
  expected_event_count integer NOT NULL DEFAULT 0 CHECK (expected_event_count >= 0),
  received_event_count integer NOT NULL DEFAULT 0 CHECK (received_event_count >= 0),
  rejected_event_count integer NOT NULL DEFAULT 0 CHECK (rejected_event_count >= 0),
  normalization_status normalization_status NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_batch_provider_ref UNIQUE (provider_id, source_batch_ref)
);

-- =============================================================================
-- 7.5 ingestion_events (retains safe synthetic payload + normalization evidence)
-- =============================================================================
CREATE TABLE ingestion_events (
  ingestion_event_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ingestion_batch_id   uuid NOT NULL REFERENCES ingestion_batches(ingestion_batch_id),
  event_type           feed_event_type NOT NULL,
  source_event_ref     text NOT NULL,
  source_observed_at   timestamptz,
  received_at          timestamptz NOT NULL,
  safe_payload         jsonb NOT NULL DEFAULT '{}'::jsonb,
  normalization_status normalization_status NOT NULL,
  rejection_code       text,
  rejection_detail     text,
  created_at           timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_event_batch_ref UNIQUE (ingestion_batch_id, source_event_ref)
);

-- =============================================================================
-- 8.1 transactions — append-only ledger
-- =============================================================================
CREATE TABLE transactions (
  transaction_id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ingestion_event_id         uuid NOT NULL UNIQUE REFERENCES ingestion_events(ingestion_event_id),
  simulation_run_id          uuid NOT NULL REFERENCES simulation_runs(simulation_run_id),
  outlet_provider_account_id uuid NOT NULL REFERENCES outlet_provider_accounts(outlet_provider_account_id),
  provider_id                uuid NOT NULL REFERENCES providers(provider_id),
  outlet_id                  uuid NOT NULL REFERENCES outlets(outlet_id),
  synthetic_transaction_ref  text NOT NULL,
  synthetic_party_ref        text NOT NULL,
  transaction_type           transaction_type NOT NULL,
  status                     transaction_status NOT NULL,
  amount                     numeric(18,2) NOT NULL CHECK (amount > 0),
  currency_code              currency_bdt NOT NULL DEFAULT 'BDT',
  occurred_at                timestamptz NOT NULL,
  received_at                timestamptz NOT NULL,
  created_at                 timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_txn_provider_ref UNIQUE (provider_id, synthetic_transaction_ref)
);
CREATE TRIGGER trg_txn_account_consistency
  BEFORE INSERT ON transactions FOR EACH ROW EXECUTE FUNCTION enforce_account_consistency();
CREATE TRIGGER trg_txn_reject_rejected_event
  BEFORE INSERT ON transactions FOR EACH ROW EXECUTE FUNCTION reject_ledger_from_rejected_event();
CREATE TRIGGER trg_txn_append_only
  BEFORE UPDATE OR DELETE ON transactions FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 8.2 cash_balance_snapshots — the ONLY shared physical-cash balance (NO provider_id)
-- =============================================================================
CREATE TABLE cash_balance_snapshots (
  cash_balance_snapshot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ingestion_event_id       uuid UNIQUE REFERENCES ingestion_events(ingestion_event_id),
  simulation_run_id        uuid NOT NULL REFERENCES simulation_runs(simulation_run_id),
  outlet_id                uuid NOT NULL REFERENCES outlets(outlet_id),
  balance                  numeric(18,2) NOT NULL CHECK (balance >= 0),
  currency_code            currency_bdt NOT NULL DEFAULT 'BDT',
  observed_at              timestamptz NOT NULL,
  received_at              timestamptz NOT NULL,
  source_kind              text NOT NULL CHECK (source_kind IN ('feed','derived','seed')),
  created_at               timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_cash_reject_rejected_event
  BEFORE INSERT ON cash_balance_snapshots FOR EACH ROW EXECUTE FUNCTION reject_ledger_from_rejected_event();
CREATE TRIGGER trg_cash_append_only
  BEFORE UPDATE OR DELETE ON cash_balance_snapshots FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- =============================================================================
-- 8.3 provider_balance_snapshots — append-only; conflicting snapshots may coexist
-- (NO unique on (account, observed_at) — docs/schema.md §8.3, §13.7)
-- =============================================================================
CREATE TABLE provider_balance_snapshots (
  provider_balance_snapshot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ingestion_event_id           uuid UNIQUE REFERENCES ingestion_events(ingestion_event_id),
  simulation_run_id            uuid NOT NULL REFERENCES simulation_runs(simulation_run_id),
  outlet_provider_account_id   uuid NOT NULL REFERENCES outlet_provider_accounts(outlet_provider_account_id),
  provider_id                  uuid NOT NULL REFERENCES providers(provider_id),
  outlet_id                    uuid NOT NULL REFERENCES outlets(outlet_id),
  balance                      numeric(18,2) NOT NULL CHECK (balance >= 0),
  currency_code                currency_bdt NOT NULL DEFAULT 'BDT',
  observed_at                  timestamptz NOT NULL,
  received_at                  timestamptz NOT NULL,
  source_kind                  text NOT NULL CHECK (source_kind IN ('feed','derived','seed')),
  created_at                   timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_pbs_account_consistency
  BEFORE INSERT ON provider_balance_snapshots FOR EACH ROW EXECUTE FUNCTION enforce_account_consistency();
CREATE TRIGGER trg_pbs_reject_rejected_event
  BEFORE INSERT ON provider_balance_snapshots FOR EACH ROW EXECUTE FUNCTION reject_ledger_from_rejected_event();
CREATE TRIGGER trg_pbs_append_only
  BEFORE UPDATE OR DELETE ON provider_balance_snapshots FOR EACH ROW EXECUTE FUNCTION reject_mutation();

-- Indexes for these tables are created in migration 005 (docs/schema.md §14).
