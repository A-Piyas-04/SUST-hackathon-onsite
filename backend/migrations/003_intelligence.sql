-- 003_intelligence.sql
-- Owner: Member 1 (schema/persistence). Member 3 owns the real forecast/anomaly
-- formulas that eventually populate these tables via the ResultEnvelope adapter
-- (app/member1/adapters/result_envelope.py) — this migration only defines the
-- storage shape, matching docs/schema.md Section 9 exactly.
--
-- Decision record: anomaly_flags.plausible_benign_explanation is required
-- whenever disposition <> 'suppressed_data_quality' (schema.md invariant #9
-- says "when actionable"; suppressed-for-data-quality is the one disposition
-- that is explicitly non-actionable per invariant #10).

-- ---------------------------------------------------------------------------
-- data_quality_assessments (append-only)
-- ---------------------------------------------------------------------------
CREATE TABLE data_quality_assessments (
    data_quality_assessment_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_run_id              uuid NOT NULL REFERENCES simulation_runs (simulation_run_id),
    ingestion_batch_id               uuid NULL REFERENCES ingestion_batches (ingestion_batch_id),
    outlet_id                          uuid NOT NULL REFERENCES outlets (outlet_id),
    provider_id                          uuid NOT NULL REFERENCES providers (provider_id),
    status                                 text NOT NULL CHECK (status IN ('fresh', 'stale', 'missing', 'conflicting')),
    confidence_modifier                      numeric(5, 4) NOT NULL CHECK (confidence_modifier >= 0 AND confidence_modifier <= 1),
    sample_count                               integer NOT NULL DEFAULT 0 CHECK (sample_count >= 0),
    latest_source_at                             timestamptz NULL, -- nullable for missing-feed assessment
    assessed_at                                    timestamptz NOT NULL DEFAULT now(),
    engine_version                                   text NOT NULL,
    summary                                            text NOT NULL,
    created_at                                           timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE data_quality_assessments IS 'fresh/stale/missing/conflicting feed-health evaluation feeding both the Liquidity and Anomaly engines confidence modifiers.';

CREATE INDEX idx_data_quality_assessments_outlet_provider_assessed ON data_quality_assessments (outlet_id, provider_id, assessed_at DESC);

-- ---------------------------------------------------------------------------
-- data_quality_issues
-- ---------------------------------------------------------------------------
CREATE TABLE data_quality_issues (
    data_quality_issue_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    data_quality_assessment_id uuid NOT NULL REFERENCES data_quality_assessments (data_quality_assessment_id),
    issue_type                   text NOT NULL CHECK (issue_type IN ('late_arrival', 'missing_feed', 'missing_field', 'conflicting_snapshot', 'impossible_transition', 'insufficient_samples', 'malformed_payload')),
    severity                       text NOT NULL CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    field_name                      text NULL,
    evidence                          jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at                          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_data_quality_issues_assessment ON data_quality_issues (data_quality_assessment_id);

-- ---------------------------------------------------------------------------
-- analytics_runs — common reproducibility envelope
-- ---------------------------------------------------------------------------
CREATE TABLE analytics_runs (
    analytics_run_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_run_id    uuid NOT NULL REFERENCES simulation_runs (simulation_run_id),
    engine                 text NOT NULL CHECK (engine IN ('liquidity', 'anomaly', 'data_quality')),
    engine_version            text NOT NULL,
    configuration               jsonb NOT NULL DEFAULT '{}'::jsonb,
    input_window_start            timestamptz NOT NULL,
    input_window_end                timestamptz NOT NULL,
    status                             text NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    started_at                           timestamptz NOT NULL DEFAULT now(),
    completed_at                           timestamptz NULL,
    error_summary                            text NULL,

    CONSTRAINT analytics_runs_window_valid CHECK (input_window_end >= input_window_start)
);

COMMENT ON TABLE analytics_runs IS 'Reproducibility envelope shared by liquidity/anomaly/data_quality engine executions (mirrors the ResultEnvelope adapter contract).';

CREATE INDEX idx_analytics_runs_simulation_run ON analytics_runs (simulation_run_id);

-- ---------------------------------------------------------------------------
-- liquidity_projections (append-only)
-- ---------------------------------------------------------------------------
CREATE TABLE liquidity_projections (
    liquidity_projection_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    analytics_run_id            uuid NOT NULL REFERENCES analytics_runs (analytics_run_id),
    outlet_id                     uuid NOT NULL REFERENCES outlets (outlet_id),
    reserve_type                    text NOT NULL CHECK (reserve_type IN ('shared_cash', 'provider_e_money')),
    outlet_provider_account_id        uuid NULL REFERENCES outlet_provider_accounts (outlet_provider_account_id),
    provider_id                         uuid NULL REFERENCES providers (provider_id),
    primary_data_quality_assessment_id     uuid NULL REFERENCES data_quality_assessments (data_quality_assessment_id),
    as_of_at                                 timestamptz NOT NULL,
    current_balance                            numeric(18, 2) NOT NULL CHECK (current_balance >= 0),
    burn_rate_per_hour                            numeric(18, 4) NOT NULL,
    projected_shortage_at                            timestamptz NULL,
    lower_bound_at                                     timestamptz NULL,
    upper_bound_at                                        timestamptz NULL,
    confidence_score                                        numeric(5, 4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    confidence_level                                           text NOT NULL CHECK (confidence_level IN ('high', 'medium', 'low', 'unavailable')),
    sample_count                                                  integer NOT NULL DEFAULT 0 CHECK (sample_count >= 0),
    is_actionable                                                    boolean NOT NULL,
    non_actionable_reason                                               text NULL,
    created_at                                                            timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT liquidity_projections_reserve_scope_match CHECK (
        (reserve_type = 'shared_cash' AND outlet_provider_account_id IS NULL AND provider_id IS NULL)
        OR
        (reserve_type = 'provider_e_money' AND outlet_provider_account_id IS NOT NULL AND provider_id IS NOT NULL)
    ),
    CONSTRAINT liquidity_projections_non_actionable_reason_required CHECK (
        is_actionable = true OR non_actionable_reason IS NOT NULL
    ),
    CONSTRAINT liquidity_projections_flat_or_replenishing_no_shortage CHECK (
        burn_rate_per_hour > 0 OR (projected_shortage_at IS NULL AND lower_bound_at IS NULL AND upper_bound_at IS NULL)
    )
);

COMMENT ON TABLE liquidity_projections IS 'Per-provider and shared-cash shortage projection with confidence. burn_rate_per_hour <= 0 means flat/replenishing (schema.md 9.4).';

CREATE INDEX idx_liquidity_projections_outlet_reserve_provider_asof ON liquidity_projections (outlet_id, reserve_type, provider_id, as_of_at DESC);

CREATE OR REPLACE FUNCTION enforce_liquidity_projection_scope() RETURNS trigger AS $$
DECLARE
    v_outlet_id uuid;
    v_provider_id uuid;
BEGIN
    IF NEW.outlet_provider_account_id IS NOT NULL THEN
        SELECT outlet_id, provider_id INTO v_outlet_id, v_provider_id
        FROM outlet_provider_accounts
        WHERE outlet_provider_account_id = NEW.outlet_provider_account_id;

        IF v_outlet_id IS NULL THEN
            RAISE EXCEPTION 'outlet_provider_account_id % does not exist', NEW.outlet_provider_account_id;
        END IF;

        IF NEW.outlet_id IS DISTINCT FROM v_outlet_id OR NEW.provider_id IS DISTINCT FROM v_provider_id THEN
            RAISE EXCEPTION 'liquidity_projections outlet_id/provider_id must match outlet_provider_account_id %', NEW.outlet_provider_account_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_liquidity_projections_scope_match
    BEFORE INSERT ON liquidity_projections
    FOR EACH ROW EXECUTE FUNCTION enforce_liquidity_projection_scope();

-- ---------------------------------------------------------------------------
-- liquidity_projection_quality_assessments (join)
-- ---------------------------------------------------------------------------
CREATE TABLE liquidity_projection_quality_assessments (
    liquidity_projection_id     uuid NOT NULL REFERENCES liquidity_projections (liquidity_projection_id),
    data_quality_assessment_id    uuid NOT NULL REFERENCES data_quality_assessments (data_quality_assessment_id),

    PRIMARY KEY (liquidity_projection_id, data_quality_assessment_id)
);

-- ---------------------------------------------------------------------------
-- liquidity_signals
-- ---------------------------------------------------------------------------
CREATE TABLE liquidity_signals (
    liquidity_signal_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    liquidity_projection_id uuid NOT NULL REFERENCES liquidity_projections (liquidity_projection_id),
    signal_code                text NOT NULL,
    label                         text NOT NULL,
    numeric_value                   numeric NULL,
    unit                              text NULL,
    direction                          text NOT NULL CHECK (direction IN ('increases_pressure', 'reduces_pressure', 'reduces_confidence')),
    details                               jsonb NOT NULL DEFAULT '{}'::jsonb,
    display_order                          integer NOT NULL DEFAULT 0 CHECK (display_order >= 0)
);

CREATE INDEX idx_liquidity_signals_projection ON liquidity_signals (liquidity_projection_id);

-- ---------------------------------------------------------------------------
-- anomaly_rules
-- ---------------------------------------------------------------------------
CREATE TABLE anomaly_rules (
    anomaly_rule_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                text NOT NULL UNIQUE,
    pattern               text NOT NULL CHECK (pattern IN ('near_identical_amounts', 'velocity_spike', 'transaction_splitting', 'circular_activity', 'balance_inconsistency', 'time_anomaly', 'failure_rate')),
    version                 text NOT NULL,
    name                      text NOT NULL,
    description                 text NOT NULL,
    configuration                 jsonb NOT NULL DEFAULT '{}'::jsonb,
    is_active                       boolean NOT NULL DEFAULT true,
    created_at                        timestamptz NOT NULL DEFAULT now(),
    updated_at                           timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE anomaly_rules IS 'MVP activates only near_identical_amounts; other pattern values are extension points (schema.md 9.7).';

INSERT INTO anomaly_rules (code, pattern, version, name, description, configuration, is_active) VALUES (
    'near_identical_amounts_v1',
    'near_identical_amounts',
    '1',
    'Near-identical repeated amounts',
    'Flags multiple transactions within a short window whose amounts fall within a tight tolerance band of each other, especially from a small set of accounts. Requires review; not a fraud determination and may reflect normal round-number demand (e.g. pre-Eid withdrawals).',
    '{"time_window_minutes": 15, "amount_tolerance_pct": 2, "min_transaction_count": 4, "max_distinct_accounts": 4}'::jsonb,
    true
);

-- ---------------------------------------------------------------------------
-- anomaly_flags (append-only)
-- ---------------------------------------------------------------------------
CREATE TABLE anomaly_flags (
    anomaly_flag_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    analytics_run_id    uuid NOT NULL REFERENCES analytics_runs (analytics_run_id),
    anomaly_rule_id       uuid NOT NULL REFERENCES anomaly_rules (anomaly_rule_id),
    outlet_id               uuid NOT NULL REFERENCES outlets (outlet_id),
    provider_id                uuid NOT NULL REFERENCES providers (provider_id),
    outlet_provider_account_id   uuid NOT NULL REFERENCES outlet_provider_accounts (outlet_provider_account_id),
    data_quality_assessment_id     uuid NOT NULL REFERENCES data_quality_assessments (data_quality_assessment_id),
    window_start                     timestamptz NOT NULL,
    window_end                          timestamptz NOT NULL,
    confidence_score                       numeric(5, 4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    confidence_level                          text NOT NULL CHECK (confidence_level IN ('high', 'medium', 'low', 'unavailable')),
    disposition                                  text NOT NULL CHECK (disposition IN ('requires_review', 'suppressed_data_quality', 'dismissed_benign', 'confirmed_unusual', 'inconclusive')),
    reason_code                                     text NULL,
    evidence_summary                                  text NOT NULL,
    plausible_benign_explanation                        text NULL,
    suppression_reason                                     text NULL,
    created_at                                                timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT anomaly_flags_window_valid CHECK (window_end >= window_start),
    CONSTRAINT anomaly_flags_suppression_reason_required CHECK (
        disposition <> 'suppressed_data_quality' OR suppression_reason IS NOT NULL
    ),
    CONSTRAINT anomaly_flags_benign_explanation_required_when_actionable CHECK (
        disposition = 'suppressed_data_quality' OR plausible_benign_explanation IS NOT NULL
    )
);

COMMENT ON TABLE anomaly_flags IS 'A suppressed result (disposition=suppressed_data_quality) is retained for audit/evaluation but cannot create an anomaly alert (schema.md invariant #10).';

CREATE INDEX idx_anomaly_flags_outlet_provider_window_end ON anomaly_flags (outlet_id, provider_id, window_end DESC);

CREATE TRIGGER trg_anomaly_flags_account_scope_match
    BEFORE INSERT ON anomaly_flags
    FOR EACH ROW EXECUTE FUNCTION enforce_account_scope_match();

-- ---------------------------------------------------------------------------
-- anomaly_evidence_items
-- ---------------------------------------------------------------------------
CREATE TABLE anomaly_evidence_items (
    anomaly_evidence_item_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    anomaly_flag_id              uuid NOT NULL REFERENCES anomaly_flags (anomaly_flag_id),
    evidence_type                   text NOT NULL,
    label                              text NOT NULL,
    value                                jsonb NOT NULL,
    display_order                          integer NOT NULL DEFAULT 0 CHECK (display_order >= 0),
    created_at                                timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_anomaly_evidence_items_flag ON anomaly_evidence_items (anomaly_flag_id);

-- ---------------------------------------------------------------------------
-- anomaly_flag_transactions (join) — exact raw synthetic evidence trail
-- ---------------------------------------------------------------------------
CREATE TABLE anomaly_flag_transactions (
    anomaly_flag_id   uuid NOT NULL REFERENCES anomaly_flags (anomaly_flag_id),
    transaction_id      uuid NOT NULL REFERENCES transactions (transaction_id),

    PRIMARY KEY (anomaly_flag_id, transaction_id)
);
