-- member_2_identity_access/001_identity_access.sql
-- Owner: Member 2.
-- Source of truth: docs/schema.md Sections 4 (app_role, locale_code), 6.5-6.6.
--
-- STATUS: PHASE-1 SCAFFOLD — NOT APPLIED. This file lives in a subdirectory so
-- backend/migrations/run_migrations.py (which globs only top-level *.sql) does
-- NOT auto-apply it. It is promoted into the numbered pipeline in Phase 2, at
-- which point it must run AFTER 001_foundation.sql (it FKs providers/areas/
-- outlets) and BEFORE the workflow migration (workflow FKs app_users).
--
-- Ownership note / defect for Member 1: schema.md Section 20 originally placed
-- users/scopes in migration 001 (foundation). 001_foundation.sql implemented
-- only 6.1-6.4, so Member 2 owns these two identity/access tables here. See
-- docs/coordination-security/unresolved-dependencies.md.
--
-- Coordination-only enums are implemented as text + CHECK constraints (schema.md
-- Section 4: "Constrained text is easier to evolve during the hackathon"),
-- matching the convention in 001_foundation.sql.

-- ---------------------------------------------------------------------------
-- app_users — application profile for a (demo/Supabase) auth identity.
-- ---------------------------------------------------------------------------
CREATE TABLE app_users (
    -- In Supabase this is PK + FK -> auth.users.id. For portable local runs it
    -- defaults to a generated uuid; add the auth.users FK when wiring Supabase.
    user_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name     text NOT NULL,                 -- synthetic demo identity only
    preferred_locale text NOT NULL DEFAULT 'en'
                       CHECK (preferred_locale IN ('en', 'bn', 'bn_latn')),
    is_demo_user     boolean NOT NULL DEFAULT true,
    is_active        boolean NOT NULL DEFAULT true,
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE app_users IS
    'Application profile for a demo/Supabase auth identity. NEVER stores password hashes, tokens, PINs, OTPs, or credentials.';

-- ---------------------------------------------------------------------------
-- user_access_scopes — source of truth for provider-boundary checks.
-- A missing provider scope is NOT a wildcard (enforced in the application
-- policy layer; RLS reinforces it in the security migration).
-- ---------------------------------------------------------------------------
CREATE TABLE user_access_scopes (
    user_access_scope_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              uuid NOT NULL REFERENCES app_users (user_id) ON DELETE CASCADE,
    role                 text NOT NULL
                           CHECK (role IN ('agent', 'field_officer', 'area_manager',
                                           'provider_ops', 'risk_analyst', 'management', 'admin')),
    provider_id          uuid NULL REFERENCES providers (provider_id),
    area_id              uuid NULL REFERENCES areas (area_id),
    outlet_id            uuid NULL REFERENCES outlets (outlet_id),
    created_at           timestamptz NOT NULL DEFAULT now(),

    -- Prevent duplicate assignments (schema.md 6.6). NULLS NOT DISTINCT so two
    -- rows that differ only by a NULL scope column still collide.
    CONSTRAINT user_access_scopes_unique
        UNIQUE NULLS NOT DISTINCT (user_id, role, provider_id, area_id, outlet_id),

    -- Minimum-scope shape per role (schema.md 6.6). Application policy performs
    -- the full evaluation; these CHECKs stop obviously malformed rows.
    CONSTRAINT user_access_scopes_agent_needs_outlet
        CHECK (role <> 'agent' OR outlet_id IS NOT NULL),
    CONSTRAINT user_access_scopes_provider_roles_need_provider
        CHECK (role NOT IN ('provider_ops', 'risk_analyst') OR provider_id IS NOT NULL),
    CONSTRAINT user_access_scopes_area_roles_need_area
        CHECK (role NOT IN ('field_officer', 'area_manager') OR area_id IS NOT NULL)
);

COMMENT ON TABLE user_access_scopes IS
    'Role/provider/area/outlet grants. A missing provider scope is never a cross-provider wildcard.';

CREATE INDEX idx_user_access_scopes_user ON user_access_scopes (user_id);
CREATE INDEX idx_user_access_scopes_provider ON user_access_scopes (provider_id);
CREATE INDEX idx_user_access_scopes_area ON user_access_scopes (area_id);
CREATE INDEX idx_user_access_scopes_outlet ON user_access_scopes (outlet_id);
