# ADR 0001 — Enumerations implemented as CHECK-constrained DOMAINs

- **Status:** Accepted
- **Phase:** 1 (Authoritative Schema Implementation)
- **Relates to:** `docs/schema.md` §4 (Enumerations), §3 (conventions)

## Context

`schema.md` §4 lists ~25 enumerations and states they "should be PostgreSQL enums
or constrained text columns. **Constrained text is easier to evolve during the
hackathon.**" Native `CREATE TYPE ... AS ENUM` cannot remove or reorder values and
`ADD VALUE` cannot run inside a transaction block, which complicates forward-only,
transactional migrations.

## Decision

Implement every enumeration as a **`DOMAIN` over `text` with a `CHECK (VALUE IN (...))`**
constraint (e.g. `CREATE DOMAIN provider_code AS text CHECK (VALUE IN ('bkash','nagad','rocket'))`),
plus a reusable `score_unit AS numeric(5,4) CHECK (0 <= VALUE <= 1)` domain for the
`0..1` score convention. Columns reference the domain by name, centralising the
allowed value set in one place.

## Consequences

- **Compatibility:** Fully compatible with `schema.md` (constrained text is an
  explicitly sanctioned option). Column types read as the domain name; API/ORM layers
  see `text`. No behavioural change versus native enums for valid data.
- **Security/safety:** Invalid enum values are rejected at write time exactly like
  native enums; no weakening of guardrails.
- **Evolution:** Adding/removing a value is a single forward migration that
  `ALTER DOMAIN ... DROP/ADD CONSTRAINT` — runs transactionally, no enum-value locks.
- **Rollback:** Dropping a domain requires dropping dependent columns first; because
  domains are additive in `001`, rollback = drop the migration's objects (dev only,
  forward-only policy still applies in shared environments).

## Not a schema deviation

This selects one of the two options `schema.md` already offers, so no change to
`schema.md`'s contract is required.
