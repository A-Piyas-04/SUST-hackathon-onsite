# Member 2 migration scaffolds (Phase 1 — NOT applied)

These SQL files are **Phase-1 scaffolds**. They are intentionally placed in
subdirectories (`member_2_identity_access/`, `member_2_workflow/`) so that
`migrations/run_migrations.py` — which discovers only **top-level** `NNN*.sql`
files — does **not** auto-apply them. Nothing here has been run against a
database; no DB functionality is claimed.

## Ownership & ordering

| File | Owner | Purpose | Reserved numbered slot | Runs after |
|---|---|---|---|---|
| `member_2_identity_access/001_identity_access.sql` | Member 2 | `app_users`, `user_access_scopes` (+ role/locale CHECKs) | (new — see note) | `001_foundation.sql` |
| `member_2_workflow/001_workflow.sql` | Member 2 | alerts, source links, templates, renders, routing, cases, assignments, status history, notes, notifications, reviews, audit | `004_coordination.sql` | `003_intelligence.sql` + identity/access |
| `member_2_workflow/002_security.sql` | Member 2 | RLS, grants, append-only + immutability triggers | `006_security.sql` | all tables + views |

**Note for Member 1:** `schema.md` §20 placed users/scopes in migration `001`
(foundation), but `001_foundation.sql` implemented only §6.1–6.4. Member 2 owns
the identity/access migration here. In Phase 2 we will agree whether to (a)
promote `identity_access` into the numbered pipeline as a new slot between
`001` and `002`, or (b) fold it into `001_foundation.sql`. Until then it must
apply **before** the workflow migration (workflow FKs `app_users`).

## Promotion plan

- Phase 2: apply `member_2_identity_access/001_identity_access.sql` (seed demo
  identities/scopes) by copying it into the numbered pipeline.
- Phase 3: apply `member_2_workflow/001_workflow.sql` (content of reserved
  `004_coordination.sql`).
- Phase 4: apply `member_2_workflow/002_security.sql` (content of reserved
  `006_security.sql`), enabling RLS/grants/triggers.

The reserved top-level placeholders `004_coordination.sql` and
`006_security.sql` remain single-line no-ops until their respective promotion
phase, so the numbered pipeline stays runnable for Member 1 throughout Phase 1.
