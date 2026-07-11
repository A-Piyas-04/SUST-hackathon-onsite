# Backend — Phase 1 Database Schema

Authoritative PostgreSQL / Supabase schema for the **Multi-Provider Agent
Liquidity & Coordination Platform**. Phase 1 delivers the complete migration
chain, reference/demo seeds, a checksum-tracked migration runner, and an
executable schema/RLS/view test suite. **No application routes/services/engines
are implemented in this phase** (see `docs/16-hour-hackathon-phase-distribution.md`).

The authoritative contract is [`docs/schema.md`](../docs/schema.md). Deviations
are recorded as ADRs in [`docs/adr/`](../docs/adr).

## Layout

```
backend/
  migrations/
    001_foundation_and_identity.sql      006_security_immutability_rls.sql
    002_simulation_ingestion_ledger.sql  run_migrations.py   (apply/reset/seed/verify/dump/status)
    003_quality_and_intelligence.sql
    004_alerts_and_coordination.sql
    005_validation_indexes_views.sql
  seeds/reference_seed.sql               # deterministic, idempotent (ADR 0003)
  tests/                                 # pytest: constraints, append-only, RLS, views
  Makefile  .env.example
```

## Configuration (env only — never commit secrets)

Copy `backend/.env.example` to `backend/.env` and fill values. The runner reads
**`DIRECT_DATABASE_URL`** first (preferred for migrations and RLS session tests)
and falls back to **`DATABASE_URL`** (pooler). `.env` is git-ignored; the
`SUPABASE_SERVICE_ROLE_KEY` must never reach any frontend.

- **Supabase:** set `DIRECT_DATABASE_URL` to the project's direct connection
  (`db.<ref>.supabase.co:5432`, `sslmode=require`).
- **Local Postgres:** point `DIRECT_DATABASE_URL` at a local server, e.g.
  `postgresql://postgres:postgres@localhost:5433/liquidity_platform`. The chain
  creates guarded `auth.users` / role shims so it also applies on plain Postgres
  (ADR 0002 / 0004). Start a local DB with `docker compose up -d postgres`.

## Commands

Prerequisite: `pip install -r requirements.txt` (into the venv). Then either use
`make <target>` or call the runner directly:

| Purpose | `make` | Direct command |
|---|---|---|
| Apply migrations | `make migrate` | `python migrations/run_migrations.py apply` |
| Reset dev DB (guarded) | `make reset` | `APP_ENV=development python migrations/run_migrations.py reset` |
| Apply reference seeds | `make seed` | `python migrations/run_migrations.py seed` |
| Run schema tests | `make verify` | `python migrations/run_migrations.py verify` |
| Schema-only snapshot | `make dump` | `python migrations/run_migrations.py dump` |
| Migration status | `make status` | `python migrations/run_migrations.py status` |

A clean database reaches the full MVP schema with: `make migrate && make seed`.

The runner records each migration's `version`, `name`, `sha256 checksum` and
`applied_at` in `schema_migrations`, re-applies nothing on re-run, and **refuses
to run a migration whose file changed after it was applied** (add a new forward
migration instead — never edit an applied one).

## Row Level Security — request context expected by Phase 2

Policies resolve the caller via `app.current_user_id()`:

1. Supabase: the JWT `sub` claim (through `auth.uid()`), matching `app_users.user_id`.
2. Local/tests: `SET LOCAL request.jwt.claims = '{"sub":"<uuid>"}'` (and
   `SET LOCAL ROLE authenticated`), or `SET LOCAL app.current_user_id = '<uuid>'`.

Access is granted from `user_access_scopes`: provider-confidential rows require a
matching `provider_id` scope (area-limited when the scope sets an area) or an
agent/outlet scope; shared-cash rows use outlet/area scope. A missing provider
scope is **never** a wildcard. `service_role` bypasses RLS for backend service
writes; `anon` sees only non-confidential reference data.

## Test suite

`make verify` runs `backend/tests` (pytest). Coverage: migration chain +
object existence + idempotency + checksums; reserve/provider separation; append-
only & immutability; quality/intelligence constraints; alert/case coordination;
provider A/B RLS isolation; and view compilation/behaviour.
