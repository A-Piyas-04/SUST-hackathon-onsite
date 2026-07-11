# ADR 0004 — RLS identity/claims shim and guarded Supabase roles

- **Status:** Accepted
- **Phase:** 1
- **Relates to:** `docs/schema.md` §15 (RLS & authorization matrix), §13.16–18

## Context

`schema.md` §15 requires Row Level Security that scopes provider-confidential rows to
the caller's active `user_access_scopes`. On Supabase, the caller identity comes from
`auth.uid()` and JWT claims exposed as `current_setting('request.jwt.claims')`, and the
roles `anon`, `authenticated`, `service_role` exist. On plain PostgreSQL (Phase-1 local
verification) none of these exist, so the same policies must still compile and be
testable.

## Decision

1. **Guarded roles.** Migration `006` creates `anon`, `authenticated`, `service_role`
   **only if absent** (`DO $$ ... pg_roles ... $$`). On Supabase they already exist and
   are left as-is.
2. **Identity resolution helper.** `app.current_user_id()` returns, in order:
   `auth.uid()` when it resolves (Supabase), else the UUID in
   `current_setting('request.jwt.claims', true)::json->>'sub'`, else the session GUC
   `current_setting('app.current_user_id', true)`. This lets tests set identity with
   `SET LOCAL request.jwt.claims` / `SET LOCAL app.current_user_id` on both platforms.
3. **Scope helpers.** `app.user_has_provider(uuid)`, `app.user_has_outlet(uuid)`,
   `app.user_has_area(uuid)` read `user_access_scopes` for `app.current_user_id()` and
   back the RLS `USING`/`WITH CHECK` predicates. A `NULL`/absent provider scope grants
   **no** provider-wide access (never a wildcard).

## Consequences

- **Compatibility:** Policies are identical on Supabase and plain PG; the JWT-claim
  contract that Phase 2 must send is documented in `006` header and the backend README.
- **Security/safety:** Missing scope = deny; `service_role` bypasses RLS (Supabase
  `BYPASSRLS`), matching the "writes go through authorized backend service functions"
  rule (§13.18). Tests assert cross-provider reads return **zero rows**.
- **Testability:** RLS is exercised with real role switches (`SET LOCAL ROLE authenticated`)
  and claim GUCs — RLS is **not** weakened to simplify testing.
- **Rollback:** Helper functions/roles are additive; on plain PG they drop with the dev
  database, on Supabase role creation is skipped entirely.
