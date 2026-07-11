# ADR 0002 — `auth.users` shim and demo-identity seeding

- **Status:** Accepted
- **Phase:** 1
- **Relates to:** `docs/schema.md` §6.5 (`app_users`), §6.6 (`user_access_scopes`)

## Context

`schema.md` §6.5 defines `app_users.user_id` as "**PK and FK → `auth.users.id`**".
`auth.users` is provided by Supabase GoTrue and exists on any Supabase project, but
does **not** exist on a plain PostgreSQL instance used for local Phase-1 verification.
Additionally, Phase 1 has no running auth service, so demo identities cannot be created
through a real sign-up flow, yet RLS tests require seeded users with provider/outlet/area
scopes.

## Decision

1. **Guarded shim.** Migration `001` creates the `auth` schema and a **minimal
   `auth.users` table only if it does not already exist**
   (`CREATE SCHEMA IF NOT EXISTS auth`; create table guarded by a catalog check).
   On Supabase the real `auth.users` is detected and left untouched; on plain
   PostgreSQL a minimal `auth.users(id uuid primary key, email text, created_at timestamptz)`
   is created so the `app_users` foreign key resolves.
2. **`auth.uid()` shim.** A guarded `auth.uid()` function is created only if absent,
   so RLS helper functions compile on plain PostgreSQL (see ADR 0004).
3. **Demo-identity seeding.** The reference seed inserts synthetic demo rows into
   `auth.users` (fixed deterministic UUIDs, synthetic emails such as
   `agent.demo@example.test`, no passwords/PINs/OTPs) and the matching `app_users`
   and `user_access_scopes` rows, all idempotent via `ON CONFLICT DO NOTHING`.

## Consequences

- **Compatibility:** `app_users.user_id → auth.users.id` FK is preserved exactly as
  specified; the contract in `schema.md` is unchanged. On Supabase the shim is inert.
- **Security/safety:** Seeded `auth.users` rows contain only synthetic, non-sensitive
  fields; no credential columns are populated. `app_users` never duplicates passwords,
  tokens, PINs, or OTPs (per §6.5).
- **Supabase note:** Inserting demo rows directly into `auth.users` is acceptable for a
  synthetic demo project. If a target Supabase project restricts direct `auth.users`
  writes, seed those identities through the Supabase admin API in Phase 2 instead; the
  schema is unaffected.
- **Rollback:** The shim objects are created only when absent; on plain PG they are
  dropped with the dev database. No effect on Supabase.
