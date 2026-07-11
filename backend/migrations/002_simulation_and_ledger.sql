-- 002_simulation_and_ledger.sql
-- Owner: Member 1
-- Source of truth: docs/schema.md Section 7 (simulation/ingestion) and
-- Section 8 (ledger/transactions).
--
-- Decision records (deviations/interpretations, documented per task Section 12):
-- 1. `simulation_runs.started_by_user_id` and (in 005) `validation_runs.created_by_user_id`
--    are plain nullable uuid columns WITHOUT a foreign key to `app_users` in this
--    migration, because `app_users` is owned by Member 2 (auth) and does not exist
--    yet. TODO(owner=Member2): add the FK once `app_users` exists.
-- 2. `ingestion_batches.provider_id` is required (schema.md lists no "nullable" on
--    this column), so the demo's shared-cash balance snapshots use
--    `source_kind IN ('seed','derived')` and are written directly (no
--    ingestion_batch/ingestion_event required for cash), rather than inventing an
--    unmodeled "cash provider". This matches `cash_balance_snapshots.ingestion_event_id`
--    being nullable in schema.md Section 8.2.

-- ---------------------------------------------------------------------------
-- simulation_scenarios
-- ---------------------------------------------------------------------------
CREATE TABLE simulation_scenarios (
    scenario_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code            text NOT NULL UNIQUE CHECK (code IN ('normal', 'scenario_a', 'scenario_b', 'scenario_c', 'scenario_d')),
    name            text NOT NULL,
    description     text NOT NULL,
    default_seed    bigint NOT NULL,
    default_config  jsonb NOT NULL DEFAULT '{}'::jsonb,
    validation_split text NOT NULL CHECK (validation_split IN ('tuning', 'held_out', 'demo')),
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE simulation_scenarios IS 'Normal operation plus Scenarios A-D (schema.md Section 7.1). No real provider integration.';

-- ---------------------------------------------------------------------------
-- simulation_runs
-- ---------------------------------------------------------------------------
CREATE TABLE simulation_runs (
    simulation_run_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id          uuid NOT NULL REFERENCES simulation_scenarios (scenario_id),
    seed                 bigint NOT NULL,
    config_snapshot      jsonb NOT NULL,
    status               text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'completed', 'failed', 'reset')),
    started_by_user_id   uuid NULL, -- TODO(owner=Member2): FK -> app_users once it exists
    started_at           timestamptz NULL,
    completed_at         timestamptz NULL,
    error_summary        text NULL
);

COMMENT ON TABLE simulation_runs IS 'One deterministic, seeded, reproducible simulation execution.';

CREATE INDEX idx_simulation_runs_scenario ON simulation_runs (scenario_id);

-- ---------------------------------------------------------------------------
-- fault_injections
-- ---------------------------------------------------------------------------
CREATE TABLE fault_injections (
    fault_injection_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_run_id     uuid NOT NULL REFERENCES simulation_runs (simulation_run_id),
    outlet_id              uuid NOT NULL REFERENCES outlets (outlet_id),
    provider_id             uuid NULL REFERENCES providers (provider_id), -- required at app layer for provider-feed faults
    fault_type               text NOT NULL CHECK (fault_type IN ('delay', 'missing_feed', 'missing_field', 'conflicting_balance', 'malformed_payload')),
    parameters                jsonb NOT NULL DEFAULT '{}'::jsonb,
    scheduled_at               timestamptz NOT NULL,
    applied_at                  timestamptz NULL,
    ended_at                     timestamptz NULL,
    is_enabled                   boolean NOT NULL DEFAULT true
);

COMMENT ON TABLE fault_injections IS 'Configurable fault injection (delay/missing/conflicting) for live Scenario C demonstration.';

CREATE INDEX idx_fault_injections_run ON fault_injections (simulation_run_id);
CREATE INDEX idx_fault_injections_outlet_provider ON fault_injections (outlet_id, provider_id);

-- ---------------------------------------------------------------------------
-- ingestion_batches
-- ---------------------------------------------------------------------------
CREATE TABLE ingestion_batches (
    ingestion_batch_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_run_id        uuid NOT NULL REFERENCES simulation_runs (simulation_run_id),
    outlet_id                 uuid NOT NULL REFERENCES outlets (outlet_id),
    provider_id                uuid NOT NULL REFERENCES providers (provider_id),
    source_batch_ref            text NOT NULL,
    source_generated_at          timestamptz NULL, -- nullable when intentionally missing (fault injection)
    received_at                   timestamptz NOT NULL DEFAULT now(),
    expected_event_count           integer NOT NULL DEFAULT 0 CHECK (expected_event_count >= 0),
    received_event_count            integer NOT NULL DEFAULT 0 CHECK (received_event_count >= 0),
    rejected_event_count             integer NOT NULL DEFAULT 0 CHECK (rejected_event_count >= 0),
    normalization_status              text NOT NULL CHECK (normalization_status IN ('pending', 'normalized', 'rejected')),
    created_at                         timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ingestion_batches_provider_ref_unique UNIQUE (provider_id, source_batch_ref)
);

COMMENT ON TABLE ingestion_batches IS 'One simulated provider delivery or heartbeat window.';

CREATE INDEX idx_ingestion_batches_outlet_provider_received ON ingestion_batches (outlet_id, provider_id, received_at DESC);

-- ---------------------------------------------------------------------------
-- ingestion_events
-- ---------------------------------------------------------------------------
CREATE TABLE ingestion_events (
    ingestion_event_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_batch_id     uuid NOT NULL REFERENCES ingestion_batches (ingestion_batch_id),
    event_type              text NOT NULL CHECK (event_type IN ('transaction', 'provider_balance', 'cash_balance', 'heartbeat')),
    source_event_ref         text NOT NULL,
    source_observed_at        timestamptz NULL, -- nullable for malformed test input
    received_at                timestamptz NOT NULL DEFAULT now(),
    safe_payload                 jsonb NOT NULL,
    normalization_status          text NOT NULL CHECK (normalization_status IN ('pending', 'normalized', 'rejected')),
    rejection_code                 text NULL,
    rejection_detail                 text NULL,
    created_at                        timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ingestion_events_batch_ref_unique UNIQUE (ingestion_batch_id, source_event_ref)
);

COMMENT ON TABLE ingestion_events IS 'Safe synthetic source payload and normalization evidence. Rejected events must never produce ledger records (enforced by trigger below).';

CREATE INDEX idx_ingestion_events_batch ON ingestion_events (ingestion_batch_id);

-- ---------------------------------------------------------------------------
-- transactions (append-only)
-- ---------------------------------------------------------------------------
CREATE TABLE transactions (
    transaction_id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_event_id              uuid NOT NULL UNIQUE REFERENCES ingestion_events (ingestion_event_id),
    simulation_run_id                 uuid NOT NULL REFERENCES simulation_runs (simulation_run_id),
    outlet_provider_account_id          uuid NOT NULL REFERENCES outlet_provider_accounts (outlet_provider_account_id),
    provider_id                           uuid NOT NULL REFERENCES providers (provider_id),
    outlet_id                               uuid NOT NULL REFERENCES outlets (outlet_id),
    synthetic_transaction_ref                 text NOT NULL,
    synthetic_party_ref                         text NOT NULL,
    transaction_type                              text NOT NULL CHECK (transaction_type IN ('cash_in', 'cash_out', 'payment', 'refund', 'adjustment')),
    status                                          text NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'reversed')),
    amount                                            numeric(18, 2) NOT NULL CHECK (amount > 0),
    currency_code                                       char(3) NOT NULL DEFAULT 'BDT' CHECK (currency_code = 'BDT'),
    occurred_at                                           timestamptz NOT NULL,
    received_at                                             timestamptz NOT NULL DEFAULT now(),
    created_at                                                timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT transactions_provider_ref_unique UNIQUE (provider_id, synthetic_transaction_ref)
);

COMMENT ON TABLE transactions IS 'Append-only synthetic transaction observation. Positive amount required; type/status describe simulated source data only and authorize no real action (schema.md Section 4).';

CREATE INDEX idx_transactions_outlet_provider_occurred ON transactions (outlet_id, provider_id, occurred_at DESC);
CREATE INDEX idx_transactions_provider_party_occurred ON transactions (provider_id, synthetic_party_ref, occurred_at DESC);

-- ---------------------------------------------------------------------------
-- cash_balance_snapshots (append-only) — no provider_id, ever
-- ---------------------------------------------------------------------------
CREATE TABLE cash_balance_snapshots (
    cash_balance_snapshot_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_event_id           uuid NULL UNIQUE REFERENCES ingestion_events (ingestion_event_id),
    simulation_run_id              uuid NOT NULL REFERENCES simulation_runs (simulation_run_id),
    outlet_id                        uuid NOT NULL REFERENCES outlets (outlet_id),
    balance                            numeric(18, 2) NOT NULL CHECK (balance >= 0),
    currency_code                        char(3) NOT NULL DEFAULT 'BDT' CHECK (currency_code = 'BDT'),
    observed_at                            timestamptz NOT NULL,
    received_at                              timestamptz NOT NULL DEFAULT now(),
    source_kind                                text NOT NULL CHECK (source_kind IN ('feed', 'derived', 'seed')),
    created_at                                   timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE cash_balance_snapshots IS 'The only persisted shared physical-cash balance. Intentionally has no provider_id column — never blend cash with provider e-money.';

CREATE INDEX idx_cash_balance_snapshots_outlet_observed ON cash_balance_snapshots (outlet_id, observed_at DESC, received_at DESC);

-- ---------------------------------------------------------------------------
-- provider_balance_snapshots (append-only) — conflicting rows allowed
-- ---------------------------------------------------------------------------
CREATE TABLE provider_balance_snapshots (
    provider_balance_snapshot_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_event_id                uuid NULL UNIQUE REFERENCES ingestion_events (ingestion_event_id),
    simulation_run_id                    uuid NOT NULL REFERENCES simulation_runs (simulation_run_id),
    outlet_provider_account_id             uuid NOT NULL REFERENCES outlet_provider_accounts (outlet_provider_account_id),
    provider_id                              uuid NOT NULL REFERENCES providers (provider_id),
    outlet_id                                  uuid NOT NULL REFERENCES outlets (outlet_id),
    balance                                      numeric(18, 2) NOT NULL CHECK (balance >= 0),
    currency_code                                  char(3) NOT NULL DEFAULT 'BDT' CHECK (currency_code = 'BDT'),
    observed_at                                      timestamptz NOT NULL,
    received_at                                        timestamptz NOT NULL DEFAULT now(),
    source_kind                                          text NOT NULL CHECK (source_kind IN ('feed', 'derived', 'seed')),
    created_at                                             timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE provider_balance_snapshots IS 'Intentionally allows conflicting rows at the same observed_at (Scenario C). Do not add a unique (account, observed_at) constraint.';

CREATE INDEX idx_provider_balance_snapshots_account_observed ON provider_balance_snapshots (outlet_provider_account_id, observed_at DESC, received_at DESC);

-- ---------------------------------------------------------------------------
-- Integrity triggers (schema.md Section 13, invariants #2 and #6)
-- ---------------------------------------------------------------------------

-- Invariant #6: rejected/pending ingestion events cannot produce ledger rows.
CREATE OR REPLACE FUNCTION enforce_normalized_ingestion_event() RETURNS trigger AS $$
DECLARE
    v_status text;
BEGIN
    IF NEW.ingestion_event_id IS NOT NULL THEN
        SELECT normalization_status INTO v_status
        FROM ingestion_events
        WHERE ingestion_event_id = NEW.ingestion_event_id;

        IF v_status IS DISTINCT FROM 'normalized' THEN
            RAISE EXCEPTION 'ingestion_event_id % is not normalized (status=%); rejected/pending events cannot create ledger rows', NEW.ingestion_event_id, v_status;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_transactions_require_normalized
    BEFORE INSERT ON transactions
    FOR EACH ROW EXECUTE FUNCTION enforce_normalized_ingestion_event();

CREATE TRIGGER trg_cash_balance_snapshots_require_normalized
    BEFORE INSERT ON cash_balance_snapshots
    FOR EACH ROW EXECUTE FUNCTION enforce_normalized_ingestion_event();

CREATE TRIGGER trg_provider_balance_snapshots_require_normalized
    BEFORE INSERT ON provider_balance_snapshots
    FOR EACH ROW EXECUTE FUNCTION enforce_normalized_ingestion_event();

-- Invariant #2: a provider-scoped row's provider_id/outlet_id must match its
-- outlet_provider_account.
CREATE OR REPLACE FUNCTION enforce_account_scope_match() RETURNS trigger AS $$
DECLARE
    v_outlet_id uuid;
    v_provider_id uuid;
BEGIN
    SELECT outlet_id, provider_id INTO v_outlet_id, v_provider_id
    FROM outlet_provider_accounts
    WHERE outlet_provider_account_id = NEW.outlet_provider_account_id;

    IF v_outlet_id IS NULL THEN
        RAISE EXCEPTION 'outlet_provider_account_id % does not exist', NEW.outlet_provider_account_id;
    END IF;

    IF NEW.outlet_id IS DISTINCT FROM v_outlet_id OR NEW.provider_id IS DISTINCT FROM v_provider_id THEN
        RAISE EXCEPTION 'outlet_id/provider_id (%,%) must match outlet_provider_account_id % (expected outlet_id=%, provider_id=%)',
            NEW.outlet_id, NEW.provider_id, NEW.outlet_provider_account_id, v_outlet_id, v_provider_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_transactions_account_scope_match
    BEFORE INSERT ON transactions
    FOR EACH ROW EXECUTE FUNCTION enforce_account_scope_match();

CREATE TRIGGER trg_provider_balance_snapshots_account_scope_match
    BEFORE INSERT ON provider_balance_snapshots
    FOR EACH ROW EXECUTE FUNCTION enforce_account_scope_match();
