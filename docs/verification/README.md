# Phase 1 — Verification Artifacts

Evidence that the authoritative schema (`docs/schema.md`) applies cleanly, seeds,
enforces its invariants, and isolates providers via RLS.

**Verification platform:** local PostgreSQL 17.5, using the identical
forward-only migration chain intended for Supabase. The chain creates guarded
`auth.users` and role shims (ADR 0002 / 0004) so it applies on both plain
PostgreSQL and Supabase. Supabase deployment verification runs when project
credentials are provided in `backend/.env` (see the backend README) — until then
it is reported as **blocked**, never claimed.

## Files

| File | What it shows |
|---|---|
| `migration_log.txt` | Clean reset → apply `001`–`006` → seed → **idempotent re-apply/re-seed**. |
| `migration_checksums.txt` | Recorded `version / name / sha256 checksum / applied_at` from `schema_migrations`. |
| `test_report.txt` | Full pytest run: **53 passed** (constraints, append-only, quality, coordination, RLS, views). |
| `rls_provider_ab_report.txt` | Provider A/B denial: bKash sees only bKash, Nagad only Nagad, no-scope user sees 0 rows, unauthorized mutation → permission denied. |
| `schema.sql` | `pg_dump --schema-only` snapshot (tables, constraints, triggers, indexes, views, GRANTs, RLS policies). No credentials. |

## Object counts (clean DB)

- 42 tables (41 schema + `schema_migrations`), 7 views, 75 indexes,
  30 RLS-enabled tables with 30 policies, 35 user triggers, 26 enum domains.

## Reproduce

```bash
cd backend
cp .env.example .env            # set DIRECT_DATABASE_URL (Supabase or local)
make migrate && make seed       # one clean-DB path to the full MVP schema
make verify                     # run the schema/RLS/view test suite
make dump                       # regenerate docs/verification/schema.sql
```
