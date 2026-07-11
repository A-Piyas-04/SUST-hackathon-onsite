-- member_2_workflow/002_security.sql
-- Owner: Member 2.
-- Source of truth: docs/schema.md Sections 13, 15 and member-2 plan Section 7.
--
-- STATUS: PHASE-1 SCAFFOLD — NOT APPLIED. Corresponds to reserved slot
-- 006_security.sql. Promoted LAST in the pipeline (after all tables + views).
-- RLS is defense-in-depth: the application service enforces authorization even
-- if these policies are also enabled (schema.md Section 15).
--
-- This file is illustrative of the controls Member 2 will apply in Phase 4. It
-- assumes an application DB role named `app_rw` and a request-scoped provider
-- context set via a GUC (e.g. SET app.provider_ids = '...'). Adjust to the
-- final Supabase auth wiring before applying.

-- ---------------------------------------------------------------------------
-- 1. Append-only protection: audit + history tables get INSERT/SELECT only.
-- ---------------------------------------------------------------------------
-- REVOKE UPDATE, DELETE ON audit_events        FROM app_rw;
-- REVOKE UPDATE, DELETE ON case_status_history FROM app_rw;
-- REVOKE UPDATE, DELETE ON case_assignments    FROM app_rw;
-- REVOKE UPDATE, DELETE ON case_notes          FROM app_rw;
-- REVOKE TRUNCATE       ON audit_events         FROM app_rw;

-- Belt-and-braces triggers so an accidental grant cannot allow mutation.
CREATE OR REPLACE FUNCTION coordination_forbid_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Table % is append-only; % is not permitted.', TG_TABLE_NAME, TG_OP;
END;
$$;

-- CREATE TRIGGER trg_audit_events_append_only
--     BEFORE UPDATE OR DELETE ON audit_events
--     FOR EACH ROW EXECUTE FUNCTION coordination_forbid_mutation();
-- CREATE TRIGGER trg_case_status_history_append_only
--     BEFORE UPDATE OR DELETE ON case_status_history
--     FOR EACH ROW EXECUTE FUNCTION coordination_forbid_mutation();
-- CREATE TRIGGER trg_case_notes_append_only
--     BEFORE UPDATE OR DELETE ON case_notes
--     FOR EACH ROW EXECUTE FUNCTION coordination_forbid_mutation();
-- CREATE TRIGGER trg_case_assignments_append_only
--     BEFORE UPDATE OR DELETE ON case_assignments
--     FOR EACH ROW EXECUTE FUNCTION coordination_forbid_mutation();

-- ---------------------------------------------------------------------------
-- 2. Alert immutability: analytical content is frozen after publication; only
--    state / supersedes_alert_id may change (schema.md 10.1, invariant 13).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION coordination_alerts_immutable()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF (NEW.alert_type, NEW.severity, NEW.outlet_id, NEW.provider_id,
        NEW.deduplication_key, NEW.structured_payload, NEW.detected_at, NEW.requires_case)
       IS DISTINCT FROM
       (OLD.alert_type, OLD.severity, OLD.outlet_id, OLD.provider_id,
        OLD.deduplication_key, OLD.structured_payload, OLD.detected_at, OLD.requires_case)
    THEN
        RAISE EXCEPTION 'Published alert analytical content is immutable; only state/supersedes_alert_id may change.';
    END IF;
    RETURN NEW;
END;
$$;

-- CREATE TRIGGER trg_alerts_immutable
--     BEFORE UPDATE ON alerts
--     FOR EACH ROW EXECUTE FUNCTION coordination_alerts_immutable();

-- Rendered explanation snapshots are fully immutable.
-- CREATE TRIGGER trg_alert_explanations_immutable
--     BEFORE UPDATE OR DELETE ON alert_explanations
--     FOR EACH ROW EXECUTE FUNCTION coordination_forbid_mutation();

-- ---------------------------------------------------------------------------
-- 3. Row Level Security: provider-boundary isolation (defense in depth).
--    A missing provider scope is NEVER a wildcard.
-- ---------------------------------------------------------------------------
-- ALTER TABLE alerts        ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE cases         ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE case_notes    ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE audit_events  ENABLE ROW LEVEL SECURITY;

-- Example provider-confidential read policy (illustrative):
-- CREATE POLICY alerts_provider_isolation ON alerts
--     FOR SELECT TO app_rw
--     USING (
--         provider_id IS NULL  -- shared-cash rows use outlet/area scope, checked in app layer
--         OR provider_id = ANY (current_setting('app.provider_ids', true)::uuid[])
--     );

-- NOTE: unauthorized cross-provider access must surface as the SAME safe 404 as
-- a missing record. RLS returning zero rows achieves this at the DB layer; the
-- application service maps "no row" to the frozen NOT_FOUND shape so existence
-- is never disclosed.
