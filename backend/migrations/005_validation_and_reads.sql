-- 005_validation_and_reads.sql
-- Owner: Member 1
-- Source of truth: docs/schema.md Section 11 (validation tables) and
-- Section 12 (required database views).
--
-- Decision record: `validation_runs.created_by_user_id` is a plain nullable
-- uuid column WITHOUT a foreign key to `app_users` for the same reason as
-- `simulation_runs.started_by_user_id` in 002 (app_users is Member 2's table).
-- `v_case_timeline` is intentionally left as a stub comment only — it unions
-- Member 2's alert/case/note/notification/audit tables (migration 004), which
-- do not exist yet.

-- ---------------------------------------------------------------------------
-- validation_runs
-- ---------------------------------------------------------------------------
CREATE TABLE validation_runs (
    validation_run_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  text NOT NULL,
    dataset_split           text NOT NULL CHECK (dataset_split IN ('tuning', 'held_out', 'demo')),
    engine_version            text NOT NULL,
    configuration               jsonb NOT NULL DEFAULT '{}'::jsonb,
    started_at                    timestamptz NOT NULL DEFAULT now(),
    completed_at                     timestamptz NULL,
    status                             text NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    created_by_user_id                   uuid NULL -- TODO(owner=Member2): FK -> app_users once it exists
);

COMMENT ON TABLE validation_runs IS 'Reported analytical results (metric_results) should be filtered to dataset_split = held_out for validation-evidence claims (schema.md 11.1).';

-- ---------------------------------------------------------------------------
-- ground_truth_labels
-- ---------------------------------------------------------------------------
CREATE TABLE ground_truth_labels (
    ground_truth_label_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_run_id          uuid NOT NULL REFERENCES validation_runs (validation_run_id),
    simulation_run_id             uuid NOT NULL REFERENCES simulation_runs (simulation_run_id),
    outlet_id                        uuid NOT NULL REFERENCES outlets (outlet_id),
    provider_id                         uuid NULL REFERENCES providers (provider_id),
    label_type                            text NOT NULL CHECK (label_type IN ('shortage', 'anomaly', 'normal', 'data_quality_incident')),
    expected_value                          jsonb NOT NULL,
    window_start                              timestamptz NOT NULL,
    window_end                                   timestamptz NOT NULL,
    created_at                                     timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ground_truth_labels_window_valid CHECK (window_end >= window_start)
);

CREATE INDEX idx_ground_truth_labels_validation_run ON ground_truth_labels (validation_run_id);

-- ---------------------------------------------------------------------------
-- metric_results
-- ---------------------------------------------------------------------------
CREATE TABLE metric_results (
    metric_result_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_run_id     uuid NOT NULL REFERENCES validation_runs (validation_run_id),
    metric_code              text NOT NULL,
    category                    text NOT NULL CHECK (category IN ('analytics', 'performance', 'reliability', 'explainability')),
    value                          numeric NOT NULL,
    unit                             text NOT NULL,
    sample_size                        integer NOT NULL CHECK (sample_size > 0),
    method                                text NOT NULL,
    limitations                             text NOT NULL,
    details                                    jsonb NOT NULL DEFAULT '{}'::jsonb,
    computed_at                                   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_metric_results_validation_run ON metric_results (validation_run_id);

-- Bootstrap seed so /metrics and /api/v1/validation/results return a
-- schema-valid, honestly-labeled placeholder immediately (real measurements
-- land in Phase 7). See app/member1/adapters/validation_payload.py.
INSERT INTO validation_runs (name, dataset_split, engine_version, status, completed_at)
VALUES ('bootstrap_placeholder', 'demo', '0.1.0-scaffold', 'completed', now());

INSERT INTO metric_results (validation_run_id, metric_code, category, value, unit, sample_size, method, limitations)
SELECT
    validation_run_id,
    'api_p95_latency_ms',
    'performance',
    0,
    'ms',
    1,
    'Placeholder scaffold value; not yet measured.',
    'Phase 1 scaffold only — replace with a real measured p95 latency in Phase 7 before reporting.'
FROM validation_runs WHERE name = 'bootstrap_placeholder';

-- ---------------------------------------------------------------------------
-- Views (schema.md Section 12)
-- ---------------------------------------------------------------------------

CREATE VIEW v_latest_cash_balance AS
SELECT DISTINCT ON (outlet_id)
    outlet_id,
    cash_balance_snapshot_id,
    balance,
    currency_code,
    observed_at,
    received_at,
    source_kind
FROM cash_balance_snapshots
ORDER BY outlet_id, observed_at DESC, received_at DESC;

COMMENT ON VIEW v_latest_cash_balance IS 'Latest valid cash snapshot per outlet. Has no provider balance columns.';

CREATE VIEW v_latest_provider_balances AS
WITH latest_ts AS (
    SELECT outlet_provider_account_id, MAX(observed_at) AS latest_observed_at
    FROM provider_balance_snapshots
    GROUP BY outlet_provider_account_id
),
latest_candidates AS (
    SELECT pbs.outlet_provider_account_id, pbs.balance, pbs.observed_at, pbs.received_at, pbs.provider_balance_snapshot_id
    FROM provider_balance_snapshots pbs
    JOIN latest_ts lt USING (outlet_provider_account_id)
    WHERE pbs.observed_at = lt.latest_observed_at
),
candidate_agg AS (
    SELECT
        outlet_provider_account_id,
        COUNT(*) AS candidate_count,
        COUNT(DISTINCT balance) AS distinct_balance_count,
        MAX(observed_at) AS observed_at,
        (ARRAY_AGG(balance ORDER BY received_at DESC))[1] AS single_balance,
        (ARRAY_AGG(received_at ORDER BY received_at DESC))[1] AS single_received_at,
        jsonb_agg(
            jsonb_build_object(
                'balance', balance,
                'received_at', received_at,
                'provider_balance_snapshot_id', provider_balance_snapshot_id
            ) ORDER BY received_at DESC
        ) AS all_candidates
    FROM latest_candidates
    GROUP BY outlet_provider_account_id
),
last_trusted AS (
    SELECT DISTINCT ON (pbs.outlet_provider_account_id)
        pbs.outlet_provider_account_id,
        pbs.balance AS last_trusted_balance,
        pbs.observed_at AS last_trusted_at
    FROM provider_balance_snapshots pbs
    JOIN latest_ts lt USING (outlet_provider_account_id)
    WHERE pbs.observed_at < lt.latest_observed_at
    ORDER BY pbs.outlet_provider_account_id, pbs.observed_at DESC, pbs.received_at DESC
)
SELECT
    opa.outlet_provider_account_id,
    opa.outlet_id,
    opa.provider_id,
    ca.observed_at,
    (ca.distinct_balance_count > 1) AS is_conflicted,
    CASE WHEN ca.distinct_balance_count = 1 THEN ca.single_balance ELSE NULL END AS balance,
    CASE WHEN ca.distinct_balance_count = 1 THEN ca.single_received_at ELSE NULL END AS received_at,
    CASE WHEN ca.distinct_balance_count > 1 THEN ca.all_candidates ELSE NULL END AS conflicting_candidates,
    lt2.last_trusted_balance,
    lt2.last_trusted_at
FROM outlet_provider_accounts opa
JOIN candidate_agg ca USING (outlet_provider_account_id)
LEFT JOIN last_trusted lt2 USING (outlet_provider_account_id);

COMMENT ON VIEW v_latest_provider_balances IS 'One row per outlet-provider account. Conflicting feeds surface is_conflicted=true with all candidates + last trusted value instead of silently picking one (schema.md 12).';

CREATE VIEW v_current_feed_health AS
WITH latest AS (
    SELECT DISTINCT ON (outlet_id, provider_id)
        data_quality_assessment_id,
        outlet_id,
        provider_id,
        status,
        confidence_modifier,
        sample_count,
        latest_source_at,
        assessed_at,
        summary
    FROM data_quality_assessments
    ORDER BY outlet_id, provider_id, assessed_at DESC
)
SELECT
    l.*,
    (
        SELECT jsonb_agg(jsonb_build_object('issue_type', dqi.issue_type, 'severity', dqi.severity, 'field_name', dqi.field_name))
        FROM data_quality_issues dqi
        WHERE dqi.data_quality_assessment_id = l.data_quality_assessment_id
    ) AS issues
FROM latest l;

COMMENT ON VIEW v_current_feed_health IS 'Latest quality assessment per outlet/provider with status, confidence modifier, and issue summary.';

CREATE VIEW v_latest_liquidity_projections AS
SELECT DISTINCT ON (outlet_id, reserve_type, COALESCE(outlet_provider_account_id, '00000000-0000-0000-0000-000000000000'::uuid))
    liquidity_projection_id,
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
    non_actionable_reason
FROM liquidity_projections
ORDER BY outlet_id, reserve_type, COALESCE(outlet_provider_account_id, '00000000-0000-0000-0000-000000000000'::uuid), as_of_at DESC;

COMMENT ON VIEW v_latest_liquidity_projections IS 'Latest projection per outlet and reserve identity (shared_cash or one provider account).';

CREATE VIEW v_outlet_dashboard AS
WITH shared_cash AS (
    SELECT outlet_id, balance, currency_code, observed_at, received_at
    FROM v_latest_cash_balance
),
shared_cash_projection AS (
    SELECT outlet_id, projected_shortage_at, confidence_score, confidence_level
    FROM v_latest_liquidity_projections
    WHERE reserve_type = 'shared_cash'
),
provider_rows AS (
    SELECT
        opa.outlet_id,
        opa.outlet_provider_account_id,
        p.code AS provider_code,
        p.display_name AS provider_display_name,
        lpb.balance,
        lpb.is_conflicted,
        lpb.observed_at,
        fh.status AS feed_status,
        fh.confidence_modifier,
        lp.projected_shortage_at,
        lp.confidence_score,
        lp.confidence_level
    FROM outlet_provider_accounts opa
    JOIN providers p ON p.provider_id = opa.provider_id
    LEFT JOIN v_latest_provider_balances lpb ON lpb.outlet_provider_account_id = opa.outlet_provider_account_id
    LEFT JOIN v_current_feed_health fh ON fh.outlet_id = opa.outlet_id AND fh.provider_id = opa.provider_id
    LEFT JOIN v_latest_liquidity_projections lp
        ON lp.outlet_provider_account_id = opa.outlet_provider_account_id
       AND lp.reserve_type = 'provider_e_money'
),
provider_agg AS (
    SELECT
        outlet_id,
        jsonb_agg(
            jsonb_build_object(
                'provider_code', provider_code,
                'provider_display_name', provider_display_name,
                'balance', balance,
                'is_conflicted', is_conflicted,
                'observed_at', observed_at,
                'feed_status', feed_status,
                'confidence_modifier', confidence_modifier,
                'projected_shortage_at', projected_shortage_at,
                'confidence_score', confidence_score,
                'confidence_level', confidence_level
            ) ORDER BY provider_code
        ) AS providers
    FROM provider_rows
    GROUP BY outlet_id
)
SELECT
    o.outlet_id,
    o.synthetic_code,
    o.display_name,
    o.area_id,
    o.currency_code,
    sc.balance AS shared_cash_balance,
    sc.currency_code AS shared_cash_currency_code,
    sc.observed_at AS shared_cash_observed_at,
    scp.projected_shortage_at AS shared_cash_projected_shortage_at,
    scp.confidence_score AS shared_cash_confidence_score,
    scp.confidence_level AS shared_cash_confidence_level,
    COALESCE(pa.providers, '[]'::jsonb) AS providers,
    now() AS generated_at
FROM outlets o
LEFT JOIN shared_cash sc ON sc.outlet_id = o.outlet_id
LEFT JOIN shared_cash_projection scp ON scp.outlet_id = o.outlet_id
LEFT JOIN provider_agg pa ON pa.outlet_id = o.outlet_id;

COMMENT ON VIEW v_outlet_dashboard IS 'Read model: outlet metadata, one shared-cash object, separate provider-balance array, feed health, forecasts. NEVER exposes a combined/total balance column. Active alerts are joined in the API layer (empty array until Member 2''s alerts table exists) rather than in this view.';

-- TODO: joint view, Phase 3+ — v_case_timeline unions Member 2's alert/case/
-- note/notification/audit tables (migration 004) with this migration's
-- analytics tables. Not implemented in Phase 1.

CREATE VIEW v_validation_summary AS
SELECT
    mr.metric_result_id,
    mr.validation_run_id,
    mr.metric_code,
    mr.category,
    mr.value,
    mr.unit,
    mr.sample_size,
    mr.method,
    mr.limitations,
    mr.details,
    mr.computed_at,
    vr.name AS validation_run_name,
    vr.dataset_split,
    vr.engine_version
FROM metric_results mr
JOIN validation_runs vr ON vr.validation_run_id = mr.validation_run_id
WHERE vr.status = 'completed'
ORDER BY mr.computed_at DESC;

COMMENT ON VIEW v_validation_summary IS 'Latest completed metric results with sample size, method, and limitations for the metrics panel/presentation.';
