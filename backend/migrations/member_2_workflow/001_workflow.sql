-- member_2_workflow/001_workflow.sql
-- Owner: Member 2.
-- Source of truth: docs/schema.md Section 10 (alerts, source links, templates,
-- renders, routing, cases, assignments, status history, notes, notifications,
-- reviews, audit) and Section 4 enums.
--
-- STATUS: PHASE-1 SCAFFOLD — NOT APPLIED. Subdirectory keeps it out of the
-- top-level runner. Promoted into the numbered pipeline in Phase 3; must run
-- AFTER 001_foundation.sql, 003_intelligence.sql (it FKs liquidity_projections,
-- anomaly_flags, data_quality_assessments), and member_2_identity_access
-- (it FKs app_users). Corresponds to reserved slot 004_coordination.sql.
--
-- No table here models transfer/conversion/settlement/refill/reversal/block/
-- freeze/credentials (schema.md invariant 13.5). Analytical content on `alerts`
-- is immutable after publication (invariant 13; enforced by trigger in the
-- security migration).

-- ===========================================================================
-- alerts + source links (immutable analytical content)
-- ===========================================================================
CREATE TABLE alerts (
    alert_id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_run_id  uuid NOT NULL REFERENCES simulation_runs (simulation_run_id),
    outlet_id          uuid NOT NULL REFERENCES outlets (outlet_id),
    provider_id        uuid NULL REFERENCES providers (provider_id),  -- null only for shared-cash alert
    alert_type         text NOT NULL CHECK (alert_type IN ('liquidity', 'anomaly', 'combined', 'data_quality')),
    severity           text NOT NULL CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    state              text NOT NULL DEFAULT 'active' CHECK (state IN ('active', 'superseded', 'closed')),
    deduplication_key  text NOT NULL,
    title_key          text NULL,
    structured_payload jsonb NOT NULL,              -- situation/evidence/uncertainty/next-step variables
    requires_case      boolean NOT NULL,
    detected_at        timestamptz NOT NULL,
    created_at         timestamptz NOT NULL DEFAULT now(),
    supersedes_alert_id uuid NULL REFERENCES alerts (alert_id)
);

-- Only one ACTIVE alert per condition/window/scope.
CREATE UNIQUE INDEX uq_alerts_active_dedup ON alerts (deduplication_key) WHERE state = 'active';
CREATE INDEX idx_alerts_scope ON alerts (outlet_id, provider_id, state, severity, detected_at DESC);

COMMENT ON TABLE alerts IS
    'Immutable analytical/advisory output. type/severity/scope/payload/detected_at/source links are frozen at publication; only state/supersedes_alert_id change, and every change is audited.';

CREATE TABLE alert_liquidity_projections (
    alert_id               uuid NOT NULL REFERENCES alerts (alert_id) ON DELETE RESTRICT,
    liquidity_projection_id uuid NOT NULL REFERENCES liquidity_projections (liquidity_projection_id),
    PRIMARY KEY (alert_id, liquidity_projection_id)
);

CREATE TABLE alert_anomaly_flags (
    alert_id       uuid NOT NULL REFERENCES alerts (alert_id) ON DELETE RESTRICT,
    anomaly_flag_id uuid NOT NULL REFERENCES anomaly_flags (anomaly_flag_id),
    PRIMARY KEY (alert_id, anomaly_flag_id)
);

CREATE TABLE alert_quality_assessments (
    alert_id                   uuid NOT NULL REFERENCES alerts (alert_id) ON DELETE RESTRICT,
    data_quality_assessment_id uuid NOT NULL REFERENCES data_quality_assessments (data_quality_assessment_id),
    PRIMARY KEY (alert_id, data_quality_assessment_id)
);

-- ===========================================================================
-- explanation templates + immutable render snapshots
-- ===========================================================================
CREATE TABLE explanation_templates (
    explanation_template_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    template_key       text NOT NULL,
    locale             text NOT NULL CHECK (locale IN ('en', 'bn', 'bn_latn')),
    version            integer NOT NULL CHECK (version > 0),
    alert_type         text NOT NULL CHECK (alert_type IN ('liquidity', 'anomaly', 'combined', 'data_quality')),
    situation_template text NOT NULL,
    evidence_template  text NOT NULL,
    uncertainty_template text NOT NULL,
    next_step_template text NOT NULL,               -- human/advisory action only
    benign_context_template text NULL,
    is_active          boolean NOT NULL DEFAULT true,
    created_at         timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT explanation_templates_unique UNIQUE (template_key, locale, version)
);

CREATE TABLE alert_explanations (
    alert_explanation_id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id                uuid NOT NULL REFERENCES alerts (alert_id),
    explanation_template_id uuid NOT NULL REFERENCES explanation_templates (explanation_template_id),
    locale                  text NOT NULL CHECK (locale IN ('en', 'bn', 'bn_latn')),
    situation_text          text NOT NULL,
    evidence_text           text NOT NULL,
    uncertainty_text        text NOT NULL,
    next_step_text          text NOT NULL,
    benign_context_text     text NULL,              -- required for anomaly/combined (enforced in service)
    rendered_at             timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT alert_explanations_unique UNIQUE (alert_id, locale)
);

COMMENT ON TABLE alert_explanations IS
    'Immutable localized render snapshot. Required coverage: en for all alerts; bn or bn_latn for the demo alert.';

-- ===========================================================================
-- routing rules
-- ===========================================================================
CREATE TABLE routing_rules (
    routing_rule_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name             text NOT NULL,
    provider_id      uuid NULL REFERENCES providers (provider_id),  -- null == fallback/shared cash
    area_id          uuid NULL REFERENCES areas (area_id),
    alert_type       text NULL CHECK (alert_type IS NULL OR alert_type IN ('liquidity', 'anomaly', 'combined', 'data_quality')),
    minimum_severity text NOT NULL CHECK (minimum_severity IN ('info', 'low', 'medium', 'high', 'critical')),
    target_role      text NOT NULL
                       CHECK (target_role IN ('agent', 'field_officer', 'area_manager',
                                              'provider_ops', 'risk_analyst', 'management', 'admin')),
    priority         integer NOT NULL,              -- lower wins
    is_active        boolean NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);

-- ===========================================================================
-- cases (mutable current workflow state) + append-only history tables
-- ===========================================================================
CREATE TABLE cases (
    case_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number          text NOT NULL UNIQUE,      -- human-readable synthetic id
    alert_id             uuid NOT NULL UNIQUE REFERENCES alerts (alert_id),
    outlet_id            uuid NOT NULL REFERENCES outlets (outlet_id),
    provider_id          uuid NULL REFERENCES providers (provider_id),
    routing_rule_id      uuid NULL REFERENCES routing_rules (routing_rule_id),
    status               text NOT NULL DEFAULT 'open'
                           CHECK (status IN ('open', 'acknowledged', 'escalated', 'resolved')),
    current_owner_user_id uuid NULL REFERENCES app_users (user_id),
    current_owner_role   text NOT NULL
                           CHECK (current_owner_role IN ('agent', 'field_officer', 'area_manager',
                                                         'provider_ops', 'risk_analyst', 'management', 'admin')),
    recommended_next_step text NOT NULL,            -- advisory/human action only
    opened_at            timestamptz NOT NULL DEFAULT now(),
    acknowledged_at      timestamptz NULL,
    escalated_at         timestamptz NULL,
    resolved_at          timestamptz NULL,
    resolution_summary   text NULL,
    version              integer NOT NULL DEFAULT 1,  -- optimistic-lock counter
    updated_at           timestamptz NOT NULL DEFAULT now(),

    -- A resolved case must carry a summary + timestamp (schema.md invariant 15).
    CONSTRAINT cases_resolved_requires_summary
        CHECK (status <> 'resolved' OR (resolution_summary IS NOT NULL AND resolved_at IS NOT NULL))
);

CREATE INDEX idx_cases_provider_status ON cases (provider_id, status, updated_at DESC);
CREATE INDEX idx_cases_outlet_status ON cases (outlet_id, status, updated_at DESC);

CREATE TABLE case_assignments (
    case_assignment_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id            uuid NOT NULL REFERENCES cases (case_id),
    assigned_to_user_id uuid NULL REFERENCES app_users (user_id),
    assigned_to_role   text NOT NULL
                         CHECK (assigned_to_role IN ('agent', 'field_officer', 'area_manager',
                                                     'provider_ops', 'risk_analyst', 'management', 'admin')),
    assigned_by_user_id uuid NULL REFERENCES app_users (user_id),  -- null for routing engine
    reason             text NOT NULL CHECK (reason IN ('initial_route', 'manual_assign', 'reassign', 'escalation')),
    routing_rule_id    uuid NULL REFERENCES routing_rules (routing_rule_id),
    comment            text NULL,
    assigned_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE case_status_history (
    case_status_history_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id            uuid NOT NULL REFERENCES cases (case_id),
    from_status        text NULL CHECK (from_status IS NULL OR from_status IN ('open', 'acknowledged', 'escalated', 'resolved')),
    to_status          text NOT NULL CHECK (to_status IN ('open', 'acknowledged', 'escalated', 'resolved')),
    changed_by_user_id uuid NULL REFERENCES app_users (user_id),
    reason             text NULL,
    changed_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE case_notes (
    case_note_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id        uuid NOT NULL REFERENCES cases (case_id),
    author_user_id uuid NOT NULL REFERENCES app_users (user_id),
    note_text      text NOT NULL,                   -- no secrets/real identities/fraud verdict
    note_type      text NOT NULL DEFAULT 'general'
                     CHECK (note_type IN ('general', 'contact_attempt', 'evidence', 'resolution')),
    created_at     timestamptz NOT NULL DEFAULT now()
);

-- ===========================================================================
-- notifications + reviews
-- ===========================================================================
CREATE TABLE notifications (
    notification_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id           uuid NOT NULL REFERENCES cases (case_id),
    recipient_user_id uuid NULL REFERENCES app_users (user_id),
    recipient_role    text NOT NULL
                        CHECK (recipient_role IN ('agent', 'field_officer', 'area_manager',
                                                  'provider_ops', 'risk_analyst', 'management', 'admin')),
    channel           text NOT NULL DEFAULT 'in_app' CHECK (channel IN ('in_app', 'webhook', 'email_stub')),
    status            text NOT NULL CHECK (status IN ('queued', 'delivered', 'read', 'failed')),
    payload           jsonb NOT NULL,               -- case id, localized title, safe summary; no cross-provider confidential data
    queued_at         timestamptz NOT NULL DEFAULT now(),
    delivered_at      timestamptz NULL,
    read_at           timestamptz NULL,
    failure_reason    text NULL
);

CREATE INDEX idx_notifications_recipient ON notifications (recipient_user_id, status, queued_at DESC);

CREATE TABLE case_reviews (
    case_review_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id            uuid NOT NULL UNIQUE REFERENCES cases (case_id),
    reviewed_by_user_id uuid NOT NULL REFERENCES app_users (user_id),
    -- Never a fraud verdict — no such value exists in the enum.
    disposition        text NOT NULL
                         CHECK (disposition IN ('benign_operational', 'requires_follow_up',
                                                'data_quality_issue', 'confirmed_unusual', 'inconclusive')),
    was_false_positive boolean NULL,
    review_summary     text NOT NULL,
    reviewed_at        timestamptz NOT NULL DEFAULT now()
);

-- ===========================================================================
-- audit events (strictly append-only; enforced by security migration)
-- ===========================================================================
CREATE TABLE audit_events (
    audit_event_id  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id         uuid NULL REFERENCES cases (case_id),
    alert_id        uuid NULL REFERENCES alerts (alert_id),
    provider_id     uuid NULL REFERENCES providers (provider_id),
    outlet_id       uuid NULL REFERENCES outlets (outlet_id),
    actor_user_id   uuid NULL REFERENCES app_users (user_id),
    actor_type      text NOT NULL CHECK (actor_type IN ('user', 'routing_engine', 'analytics_engine', 'system')),
    action          text NOT NULL,                  -- stable action code
    entity_type     text NOT NULL,
    entity_id       uuid NULL,
    previous_values jsonb NULL,                      -- minimal safe diff; never credentials/raw private data
    new_values      jsonb NULL,
    request_id      text NULL,                       -- correlation id
    occurred_at     timestamptz NOT NULL DEFAULT now(),
    hash            text NULL                        -- optional tamper-evidence checksum
);

CREATE INDEX idx_audit_events_case ON audit_events (case_id, occurred_at);
CREATE INDEX idx_audit_events_alert ON audit_events (alert_id, occurred_at);

COMMENT ON TABLE audit_events IS
    'Strictly append-only. Application roles get INSERT/SELECT only; UPDATE/DELETE are denied in the security migration. Written in the same transaction as the workflow mutation.';
