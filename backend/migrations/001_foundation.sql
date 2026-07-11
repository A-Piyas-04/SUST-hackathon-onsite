-- 001_foundation.sql
-- Owner: Member 1
-- Source of truth: docs/schema.md Section 6.1-6.4 ("MVP foundation" tables).
-- Enums are implemented as text + CHECK constraints (schema.md Section 4:
-- "Constrained text is easier to evolve during the hackathon"), not native
-- Postgres ENUM types. Only enums needed by Member 1's own tables are here;
-- app_role and other coordination-only enums belong to Member 2's
-- 004_coordination.sql / 006_security.sql.
--
-- Decision record: none — this migration follows schema.md exactly with no
-- deviation.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------------
-- areas
-- ---------------------------------------------------------------------------
CREATE TABLE areas (
    area_id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_area_id  uuid NULL REFERENCES areas (area_id) ON DELETE RESTRICT,
    code            text NOT NULL UNIQUE,
    name            text NOT NULL,
    level           text NOT NULL CHECK (level IN ('territory', 'area', 'thana', 'district', 'region')),
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT areas_no_self_parent CHECK (parent_area_id IS NULL OR parent_area_id <> area_id)
);
-- Note: direct self-reference is blocked above; deeper cycles are prevented at
-- the application/service layer (no recursive-cycle trigger in the MVP).

COMMENT ON TABLE areas IS 'Territory/area/thana/district/region hierarchy for outlet filtering and routing scope. Synthetic/general location only.';

-- ---------------------------------------------------------------------------
-- providers
-- ---------------------------------------------------------------------------
CREATE TABLE providers (
    provider_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code            text NOT NULL UNIQUE CHECK (code IN ('bkash', 'nagad', 'rocket')),
    display_name    text NOT NULL,
    display_color   text NULL,
    is_simulated    boolean NOT NULL DEFAULT true CHECK (is_simulated = true),
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE providers IS 'Logically separate simulated financial-service providers. Never merged/converted with each other or with shared cash.';

INSERT INTO providers (code, display_name, display_color) VALUES
    ('bkash', 'bKash', '#e2136e'),
    ('nagad', 'Nagad', '#f7941d'),
    ('rocket', 'Rocket', '#8a1c7c');

-- ---------------------------------------------------------------------------
-- outlets
-- ---------------------------------------------------------------------------
CREATE TABLE outlets (
    outlet_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    synthetic_code  text NOT NULL UNIQUE,
    display_name    text NOT NULL,
    area_id         uuid NULL REFERENCES areas (area_id),
    currency_code   char(3) NOT NULL DEFAULT 'BDT' CHECK (currency_code = 'BDT'),
    latitude        numeric(9, 6) NULL,
    longitude       numeric(9, 6) NULL,
    is_synthetic    boolean NOT NULL DEFAULT true CHECK (is_synthetic = true),
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE outlets IS 'Operational agent/outlet entity. synthetic_code/display_name must never be a real agent identifier.';
COMMENT ON COLUMN outlets.latitude IS 'Synthetic coordinates only, for the optional stretch nearby-agent view.';

-- ---------------------------------------------------------------------------
-- outlet_provider_accounts
-- ---------------------------------------------------------------------------
CREATE TABLE outlet_provider_accounts (
    outlet_provider_account_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    outlet_id               uuid NOT NULL REFERENCES outlets (outlet_id),
    provider_id             uuid NOT NULL REFERENCES providers (provider_id),
    synthetic_account_ref    text NOT NULL,
    is_active                boolean NOT NULL DEFAULT true,
    created_at               timestamptz NOT NULL DEFAULT now(),
    updated_at               timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT outlet_provider_accounts_outlet_provider_unique UNIQUE (outlet_id, provider_id),
    CONSTRAINT outlet_provider_accounts_provider_ref_unique UNIQUE (provider_id, synthetic_account_ref)
);

COMMENT ON TABLE outlet_provider_accounts IS 'A provider-specific e-money position for an outlet. Represents accounting separation, never interoperability/conversion.';

CREATE INDEX idx_outlet_provider_accounts_outlet ON outlet_provider_accounts (outlet_id);
CREATE INDEX idx_outlets_area ON outlets (area_id);
CREATE INDEX idx_areas_parent ON areas (parent_area_id);
