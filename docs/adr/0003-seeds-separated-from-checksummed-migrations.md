# ADR 0003 — Reference/demo seeds separated from checksummed DDL migrations

- **Status:** Accepted
- **Phase:** 1
- **Relates to:** `docs/schema.md` §1.2, §1.3, §20; task §10

## Context

`schema.md` requires forward-only, checksum-tracked migrations that must never be
edited after being applied (§1.2), and separately requires reproducible reference
seeds (providers, scenarios, the active anomaly rule, explanation templates, routing
rules, demo roles/scopes — §1.3, §20.1). Embedding seed `INSERT`s inside the DDL
migrations couples mutable reference data to immutable checksums: any later wording
change to a template or routing rule would either require editing an applied migration
(forbidden) or a churn of no-op migrations.

## Decision

Keep migrations `001`–`006` **pure DDL** (tables, constraints, triggers, indexes,
views, grants, RLS). Place all reference/demo data in a single deterministic,
idempotent `backend/seeds/reference_seed.sql`, applied by the runner's `seed` command
and safe to re-run (`ON CONFLICT DO NOTHING`, fixed UUIDs). The seed file is sectioned
to mirror the migration it supports (001 identity, 002 scenarios, 003 anomaly rule,
004 templates/routing).

## Consequences

- **Compatibility:** Satisfies both `schema.md` requirements; the "reference seeds
  create exactly the intended …" gate (§1.3) is met by the seed command, and the
  "fresh DB applies 001–006 without manual SQL" gate is met by the migration command.
- **Determinism/idempotency:** Fixed UUIDs + `ON CONFLICT DO NOTHING` make `seed`
  rerunnable without duplicates and without destroying data.
- **Security/safety:** No behavioural change to guardrails; seeds contain synthetic
  data only and are validated by tests.
- **Rollback:** Reference data can be corrected by editing the seed file and re-running
  `seed` (no migration checksum impact), or superseded by a forward migration when a
  structural change is required.
