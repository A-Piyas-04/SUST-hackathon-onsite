# Phase-by-Phase Implementation Prompt Book

**Project:** Multi-Provider Agent Liquidity & Coordination Platform  
**Event:** Codex Community Hackathon — bKash presents SUST CSE Carnival 2026  
**Source plan:** Latest solo project phase distribution  
**Purpose:** Copy-ready implementation prompts for every project phase

---


## Project-wide non-negotiable rules

- Shared physical cash and provider e-money are separate reserves. Never blend, convert, or transfer them.
- bKash, Nagad, and Rocket remain logically separate simulated providers.
- Use synthetic data only.
- Never use real provider APIs, customer identities, wallet numbers, balances, PINs, OTPs, passwords, credentials, or private keys.
- The product is advisory only. It must not move money, refill wallets, reverse transactions, block users, freeze funds, accuse anyone, or make a final fraud decision.
- Use wording such as **unusual activity**, **requires review**, **possible liquidity pressure**, **estimated**, **potential inconsistency**, and **human review recommended**.
- Alerts preserve immutable analytical evidence. Cases contain the mutable human workflow.
- Degraded data must lower confidence, widen uncertainty, become non-actionable, or suppress anomaly alertability.
- Provider A users must not read or mutate Provider B confidential records.
- Every important action must be attributable and auditable.
- Keep the architecture a modular monolith. Do not introduce unnecessary microservices or distributed infrastructure.
- Do not begin stretch features until the complete integrated MVP gate passes.

---

# Phase 1 — Authoritative Schema Implementation

**Recommended target:** Claude Code with Claude Opus 4.8

## Features in this phase

- Complete PostgreSQL/Supabase schema
- Six ordered migrations
- Tables, constraints, indexes, triggers, views, grants, and RLS
- Reference/demo seeds
- Append-only and immutable evidence protections
- Provider/outlet/area authorization boundaries
- Migration history and checksum verification

## Deliverables

- `001_foundation_and_identity.sql`
- `002_simulation_ingestion_ledger.sql`
- `003_quality_and_intelligence.sql`
- `004_alerts_and_coordination.sql`
- `005_validation_indexes_views.sql`
- `006_security_immutability_rls.sql`
- Migration runner and history/checksum tracking
- Reference seed script
- Schema, constraint, trigger, view, and RLS tests
- Schema dump or metadata snapshot
- ADR for every justified deviation from `schema.md`

## Prompt

```text
You are a senior PostgreSQL database architect and Supabase security engineer
working through Claude Code with Claude Opus 4.8.

Implement Phase 1 — Authoritative Schema Implementation for the
Multi-Provider Agent Liquidity & Coordination Platform.

This is an implementation task. Inspect the repository, compare the current
physical database and migrations with schema.md, complete the schema, connect
to Supabase through environment variables, run all schema tests, and leave a
verified clean-database migration chain.

Do not implement backend routes, services, analytics algorithms, or frontend
features during this phase.

1. INSPECT FIRST

Read completely:

- Problem_Statement.md
- System-Design.md
- schema.md
- the latest phase-distribution document
- checklist.md
- all current migrations, seeds, ADRs, verification reports, scripts, package
  files, and environment examples

Inspect the actual repository and current database state. Do not assume the
project is empty. Preserve correct existing work and repair only verified gaps.

Treat schema.md as the semantic authority and the applied numbered migrations
as the physical authority. If they disagree:

- document the mismatch;
- do not edit an already applied/checksummed migration;
- create a new forward-only migration when required;
- update schema.md, tests, views, contracts, and ADRs together;
- preserve compatibility, provider separation, RLS, append-only behavior, and
  safety rules.

2. SUPABASE ENVIRONMENT SETUP

Use environment variables only. Create or verify `.env.example` with
placeholders such as:

SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL=postgresql://postgres.YOUR_PROJECT_REF:YOUR_PASSWORD@YOUR_POOLER_HOST:5432/postgres?sslmode=require
DIRECT_DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres?sslmode=require
SUPABASE_PROJECT_REF=YOUR_PROJECT_REF
SUPABASE_DB_PASSWORD=YOUR_DATABASE_PASSWORD

Rules:

- Never commit `.env`.
- Ensure `.env` is ignored.
- Never print credentials or complete connection strings.
- Use `DIRECT_DATABASE_URL` for migrations when available.
- Permit a documented safe fallback to `DATABASE_URL` when direct connectivity
  is unavailable.
- Never expose the service-role key to frontend code.
- Validate required variables and fail with a clear safe message.

Provide verified commands for migration apply, seed, schema tests, safe
development reset, and schema dump/metadata snapshot.

3. REQUIRED MIGRATION CHAIN

Create or complete these six forward-only migrations in order:

001_foundation_and_identity.sql
002_simulation_ingestion_ledger.sql
003_quality_and_intelligence.sql
004_alerts_and_coordination.sql
005_validation_indexes_views.sql
006_security_immutability_rls.sql

No migration may remain an empty placeholder.

4. MIGRATION 001

Implement the schema.md contract for:

- extensions and constrained enum/domain strategy;
- areas;
- providers;
- outlets;
- outlet_provider_accounts;
- app_users;
- user_access_scopes;
- UUID, UTC timestamp, numeric money, active-state, hierarchy, uniqueness, and
  scope-shape constraints;
- synthetic bKash, Nagad, Rocket, areas, outlets, demo identities, and scopes.

A missing provider scope must never mean unrestricted access.

5. MIGRATION 002

Implement:

- simulation scenarios and runs;
- fault injections;
- ingestion batches and events;
- transactions;
- shared-cash snapshots;
- provider-balance snapshots;
- append-only protections;
- provider/account/outlet consistency;
- rejected-event isolation;
- deterministic synthetic references;
- preservation of conflicting snapshots.

Shared cash must have no provider account. Provider e-money must always match
one provider-specific outlet account.

6. MIGRATION 003

Implement:

- data-quality assessments and issues;
- analytics runs;
- liquidity projections;
- liquidity signals and quality links;
- anomaly rules;
- anomaly flags;
- evidence items and linked transactions;
- active near-identical-amount rule seed;
- confidence, sample-count, reserve, account, evidence, suppression, and benign
  context constraints.

The schema must not contain a final fraud verdict.

7. MIGRATION 004

Implement:

- immutable alerts;
- typed source-link tables;
- explanation templates and immutable render snapshots;
- routing rules;
- cases;
- assignments;
- status history;
- notes;
- reviews;
- notifications;
- audit events.

Seed English and at least one Bangla or Banglish demo template.

Cases must own mutable workflow state. Alerts must preserve analytical content.
No entity may authorize money movement, conversion, refill, reversal, blocking,
freezing, accusation, or punishment.

8. MIGRATION 005

Implement:

- validation runs;
- ground-truth labels;
- metric results;
- all required indexes;
- latest cash view;
- latest provider-balance view;
- current feed-health view;
- latest liquidity-projection view;
- outlet dashboard view;
- case timeline view;
- validation summary view.

The dashboard must return one separate shared-cash structure and separate
provider structures. It must never expose a blended monetary total.

9. MIGRATION 006

Implement minimum grants, roles, triggers, and RLS for:

- provider scope;
- outlet scope;
- area scope;
- management read-only/aggregate behavior;
- append-only transactions, snapshots, evidence, status history, and audit;
- immutable published alerts;
- case scope and transition consistency;
- denial of unauthorized update/delete.

Test bKash, Nagad, and Rocket isolation with separate simulated claims or
database roles. A missing provider scope is not a wildcard.

Document the JWT claims or session settings later application code must provide
to RLS.

10. MIGRATION TOOLING

The runner must:

- read connection values from environment variables;
- apply migrations in numeric order;
- record migration name, checksum, and timestamp;
- reject changed checksums;
- use transactions where PostgreSQL permits;
- fail safely on partial execution;
- support clean-database application;
- re-run without duplicating completed migrations.

The seed command must be deterministic and safe to rerun. Never truncate an
existing database implicitly.

11. TESTS

Create and run tests for:

- clean migration chain;
- re-run/checksum behavior;
- required object existence;
- shared-cash/provider-e-money XOR;
- provider/account/outlet consistency;
- append-only transactions and snapshots;
- conflicting snapshots;
- rejected ingestion isolation;
- confidence/sample/reserve rules;
- suppressed anomaly restrictions;
- alert source-link rules;
- case workflow constraints;
- audit immutability;
- every required view;
- bKash/Nagad/Rocket RLS read and write denial;
- absence of a blended balance.

12. CHECKLIST AND DOCUMENTATION

Update checklist.md only for verified schema work. Do not mark APIs, engines,
frontend, or scenarios complete.

Record:

- migration versions and checksums;
- clean apply log;
- schema dump/metadata path;
- test commands and exact results;
- every schema deviation and ADR;
- Supabase verification status.

If Supabase is inaccessible, test against local PostgreSQL and report:
“Local schema verification passed; Supabase deployment verification remains
blocked.”

13. EXIT GATE

Do not declare Phase 1 complete unless:

- all six migrations are complete;
- one command builds the full MVP schema on a fresh database;
- `.env.example` contains placeholders only;
- migration history/checksums work;
- seeds apply;
- critical constraints, triggers, views, grants, and RLS exist;
- provider isolation passes;
- append-only and immutability tests pass;
- views preserve separate reserves;
- schema dump/metadata exists;
- no old migration was edited;
- every claim has test evidence.

At completion, report repository analysis, files changed, each migration,
Supabase/local verification, all commands and results, exit-gate status, and
remaining blockers. Never expose credentials.
```

---

# Phase 2 — Application Foundation and Contracts

**Recommended target:** Claude Code with Claude Opus 4.8

## Features in this phase

- Runnable modular-monolith backend
- Configuration and environment validation
- Async database/session/transaction layer
- App factory, startup/shutdown, and CORS
- Request IDs, structured logs, and safe errors
- Authentication dependency interface
- Versioned domain/API seam contracts
- OpenAPI baseline
- Test harness and minimal frontend shell

## Deliverables

- Backend project foundation
- `.env.example`
- Database readiness health check
- Migration/seed/test/server/OpenAPI commands
- `ResultEnvelope` and `AlertCandidate` v1 contracts
- Positive and negative fixtures
- Contract and infrastructure tests
- Generated OpenAPI
- Minimal frontend project scaffold

## Prompt

```text
You are a senior backend architect and application-platform engineer working
through Claude Code with Claude Opus 4.8.

Implement Phase 2 — Application Foundation and Contracts for the
Multi-Provider Agent Liquidity & Coordination Platform.

Prerequisite: Phase 1 must already pass on a fresh PostgreSQL/Supabase database.

Do not implement synthetic data generation, ingestion business logic,
analytics engines, alerts/cases, or feature UI in this phase.

1. AUDIT THE CURRENT REPOSITORY

Read the problem statement, system design, schema.md, latest phase plan,
checklist, migrations, seeds, ADRs, existing backend/frontend code, package
files, environment examples, and tests.

Determine what is already complete. Reuse correct code. Do not replace working
infrastructure merely because the original plan assumed an empty repository.

Run the current test suite and record the baseline before editing.

2. BACKEND STRUCTURE

Create or normalize a modular-monolith structure with clear internal modules
for:

- configuration;
- database;
- shared errors and middleware;
- auth interface;
- reference data;
- simulation/ingestion/ledger;
- quality/intelligence;
- alerts/cases/security;
- validation/observability.

Do not introduce microservices, Kafka, Redis, or multiple backend frameworks.

Use the repository’s established language and framework. If FastAPI/Pydantic is
already selected, preserve that stack and current compatible versions.

3. ENVIRONMENT AND CONFIGURATION

Create or verify `.env.example` with placeholders only.

Support at minimum:

- application environment;
- API host/port;
- frontend origin/CORS;
- DATABASE_URL;
- DIRECT_DATABASE_URL where required;
- Supabase URL and keys only where actually used;
- JWT/demo-auth configuration placeholders;
- structured logging level;
- demo/synthetic mode flags.

Use typed configuration with startup validation. Never print secrets. Ensure
`.env` and local overrides are ignored.

4. DATABASE FOUNDATION

Implement:

- async connection/session handling;
- transaction boundaries;
- startup readiness check;
- graceful shutdown;
- safe retry policy where appropriate;
- migration and seed command integration;
- no global mutable session;
- no direct frontend access to service-role credentials.

Add `/health` with liveness and database readiness but no confidential details.

5. REQUEST AND ERROR INFRASTRUCTURE

Implement:

- request/correlation ID middleware;
- structured request/error logs;
- safe global error mapping;
- consistent error shape:
  `{ "error": { "code", "message", "request_id", "details" } }`;
- handling for 400, 401, 403/404 non-leakage, 409, 412, 422, 429, 500, and
  explicitly unimplemented 501 routes;
- CORS restricted to configured frontend origins.

Never log tokens, credentials, raw private payloads, or another provider’s
confidential data.

6. AUTHENTICATION INTERFACE

Define the dependency/interface future confidential routes must use.

Requirements:

- no confidential route may bypass it;
- it must expose authenticated user ID, active roles, provider scopes, area
  scopes, outlet scopes, locale, and request ID;
- a missing scope is not a wildcard;
- implementation may remain a safe demo/test adapter in Phase 2;
- do not create an admin shortcut that bypasses normal policy.

7. VERSIONED CONTRACTS

Create versioned Pydantic/domain contracts for:

- normalized transaction input;
- normalized cash/provider balance input;
- data-quality assessment and issues;
- liquidity projection and signals;
- anomaly flag and evidence;
- ResultEnvelope;
- AlertCandidate;
- validation metric payload;
- outlet/dashboard response;
- alert response;
- case response;
- safe error response.

Contract rules:

- UTC ISO timestamps;
- decimal money serialized safely;
- confidence score 0–1;
- explicit confidence level;
- provider/account/outlet consistency;
- shared-cash null provider/account;
- provider e-money required provider/account;
- ordered structured evidence;
- actionable anomaly requires plausible benign explanation;
- suppressed anomaly requires suppression reason and is non-alertable;
- AlertCandidate must contain typed persisted source IDs and no case fields;
- no unsafe financial action or definitive fraud language.

8. SEAM CONTRACTS

Preserve these seams explicitly:

normalized input → quality/analytics engine
engine → ResultEnvelope
persisted result → AlertCandidate
candidate → immutable alert
alert → mutable case

Create fixtures showing each seam. Demonstrate that a valid ResultEnvelope can
be transformed into a valid candidate fixture without adding case owner/status
fields or recalculating evidence.

9. ROUTES AND OPENAPI

Register:

- `/health`;
- versioned router groups;
- safe route stubs only where useful for OpenAPI.

A stub must return an explicit 501 and must not pretend the feature works.

Generate OpenAPI from the actual registered application. Add a verified command
to regenerate it and store it in the repository’s documented location.

10. FRONTEND SHELL

Create only a minimal frontend shell:

- project configuration;
- environment example;
- API base URL helper;
- health/readiness page;
- lint/type/build scripts.

Do not implement feature pages in Phase 2.

11. TESTS AND COMMANDS

Create one documented command or script group for:

- environment validation;
- migrations;
- seeds;
- tests;
- server;
- OpenAPI generation;
- frontend lint/type/build.

Test:

- application boot;
- health ready/degraded behavior;
- missing configuration;
- transaction rollback;
- request ID propagation;
- safe errors;
- CORS;
- auth dependency on confidential stubs;
- every contract with positive/negative fixtures;
- ResultEnvelope-to-candidate compatibility;
- OpenAPI generation;
- frontend shell build.

12. EXIT GATE

Do not declare completion unless:

- application boots against the Phase 1 database;
- `/health` verifies DB readiness;
- migrations, seeds, tests, server, and OpenAPI commands are documented and
  pass;
- contracts validate all fixtures;
- ResultEnvelope converts to a valid candidate fixture;
- no confidential route bypasses auth;
- no stub claims unimplemented behavior;
- no secrets are committed.

Report files changed, architecture decisions, exact commands/results, generated
OpenAPI path, contract versions, schema/migration version, and remaining
blockers.
```

---

# Phase 3 — Synthetic Ecosystem, Ingestion and Ledger

**Recommended target:** Codex with GPT-5.6 Sol

## Features in this phase

- Deterministic Bangladesh-context synthetic ecosystem
- Normal operation and Scenarios A–D
- Tuning, held-out, and demo data splits
- Delay, missing, malformed, and conflicting faults
- Ingestion validation and normalization
- Append-only ledger and balance snapshots
- Separated dashboard reads
- Simulation, ingestion, ledger, and initial quality APIs
- Moderate database population

## Deliverables

- Deterministic generator and manifests
- Synthetic dataset artifacts
- Scenario/fault configuration
- Ingestion and normalization services
- Ledger repositories and read models
- Moderate data seed/data migration
- Reference, simulation, ingestion, dashboard, transaction, balance, and initial quality APIs
- Seed/reset/fault commands
- Integration tests and database verification report

## Prompt

```text
You are a senior data engineer, backend engineer, and synthetic-simulation
designer working through Codex with GPT-5.6 Sol.

Implement Phase 3 — Synthetic Ecosystem, Ingestion and Ledger.

Prerequisite: Phase 2 application, database, configuration, and contracts must
pass.

This phase must produce deterministic provider data, ingest it safely, persist
append-only observations, expose separated ledger/dashboard reads, and populate
the development database with a moderate Bangladesh-context dataset.

Do not implement the final data-quality, liquidity, or anomaly algorithms in
this phase. Initial quality endpoints may expose clearly labeled foundational
ingestion-derived status only.

1. AUDIT FIRST

Inspect:

- schema.md and applied migrations;
- current live/development database metadata and row counts;
- existing generator, seeds, fixtures, evidence, ingestion, ledger, routes,
  contracts, tests, and OpenAPI;
- current data volume and scenario coverage;
- physical differences from schema.md.

Never begin with INSERT statements. First create a database-audit report and
determine the actual insertion order, constraints, append-only triggers, RLS,
and existing data that must be preserved.

If the physical database varies from schema.md, adapt the generator/seed to the
actual compatible schema and document the mismatch. Do not edit old
checksummed migrations or weaken constraints.

2. SYNTHETIC CONTEXT

Use general Bangladesh context with bKash, Nagad, and Rocket.

Use synthetic areas/outlets such as generic Dhaka, Chattogram, Sylhet, or
Rajshahi service areas. Do not use real agent/shop/customer identities,
addresses, phone numbers, wallet numbers, or credentials.

Model synthetic patterns such as:

- normal weekday/weekend demand;
- evening e-commerce payments;
- festival/Eid demand;
- salary-period activity;
- refunds after cancelled synthetic orders;
- failed/pending attempts;
- cash-out pressure;
- cash-in recovery.

Do not claim the distribution reflects real provider market share.

3. DETERMINISTIC SCENARIOS

Implement:

- normal;
- scenario_a;
- scenario_b;
- scenario_c;
- scenario_d.

Each run must store:

- scenario;
- fixed seed;
- immutable config snapshot;
- outlet/provider scope;
- deterministic timestamps;
- expected outcome metadata.

Maintain separate tuning, held-out, and demo seeds. Prevent split leakage.

4. MODERATE DATASET

Generate a moderate dataset suitable for UI and analytical development.

Target ranges, adapting only when actual constraints justify it:

- exactly 3 providers;
- 4–5 synthetic outlets across 3–4 areas;
- all three providers per outlet when supported;
- 7–10 simulated days;
- approximately 3,000–5,000 transactions;
- transaction activity at every outlet/provider;
- all supported transaction types;
- completed as the majority plus meaningful pending, failed, and reversed
  observations;
- dozens of cash/provider balance observations per reserve;
- approximately 10 simulation runs, including all scenarios with distinct
  seeds.

Use exact decimal BDT values and UTC timestamptz.

5. GENERATE ARTIFACTS BEFORE APPLYING

Create deterministic generated artifacts and a manifest before writing the
database loader.

Use repository conventions, for example:

data/generated/moderate_demo/
  manifest.json
  areas.csv
  outlets.csv
  outlet_provider_accounts.csv
  simulation_runs.csv
  fault_injections.csv
  ingestion_batches.csv
  ingestion_events.csv
  transactions.csv
  cash_balance_snapshots.csv
  provider_balance_snapshots.csv

Add later-table artifacts only if Phase 3 legitimately seeds foundational
records for future phases. Do not fabricate analytics, alerts, cases, or
metrics before their implementation unless the current repository already has
validated producers and the data is explicitly fixture-only.

The manifest must contain generator version, schema version, master seed,
scenario seeds, date range, row counts, hashes, and assumptions.

6. FAULT INJECTION

Implement deterministic:

- delay;
- missing feed;
- missing field;
- malformed payload;
- conflicting balance.

Conflicting snapshots must coexist. Rejected/malformed events must remain as
ingestion evidence but must not create trusted transaction or balance rows.

7. INGESTION AND NORMALIZATION

Implement:

- provider-specific synthetic payload adapters;
- one normalized internal schema;
- batch/event validation;
- idempotency;
- rejection codes with safe details;
- append-only batch/event storage;
- normalization into transactions and snapshots only when valid;
- provider/account/outlet consistency;
- source and receipt timestamps;
- deterministic run/reset behavior.

Do not lose provider identity during normalization.

8. LEDGER AND READ MODELS

Implement repositories/services for:

- latest shared cash;
- latest separate provider balances;
- transaction history;
- cash history;
- one-provider history;
- conflict candidates;
- separated outlet dashboard data.

Never expose a blended balance or transfer endpoint.

9. APIs

Implement and register the actual Phase 3 endpoints:

- providers;
- areas;
- outlets;
- outlet detail;
- outlet dashboard;
- transactions;
- balance history;
- scenario list;
- simulation run create/status/reset;
- fault create/toggle;
- ingestion batch;
- current/history foundational quality reads.

Use OpenAPI contracts, auth dependency, pagination/filter conventions, request
IDs, safe errors, and provider/outlet/area scopes.

Internal ingestion must be admin/service-only. Do not expose service-role
credentials to the frontend.

10. APPLY THE MODERATE DATASET

After artifacts pass validation, create a versioned, idempotent seed/data
migration following existing repository conventions.

Rules:

- do not edit migrations 001–006;
- default to dry run;
- require an explicit apply flag for remote Supabase;
- preserve unrelated existing data;
- never truncate operational tables;
- never disable RLS, triggers, constraints, or append-only protection;
- use stable IDs and safe conflict handling;
- record seed version, manifest hash, and apply time;
- rollback on failure;
- report inserted/skipped/conflicted counts.

Optionally create an explicit development-only cleanup command that removes
only the generated namespace.

11. VALIDATION

Validate:

- every outlet has activity;
- provider/account/outlet consistency;
- positive decimal amounts;
- UTC timestamps;
- no real-identity-like references;
- deterministic same-seed output;
- different seeds vary values without changing schema;
- all scenarios represented;
- Scenario C faults preserved;
- malformed/rejected events do not affect ledger;
- shared cash/provider e-money remain separate;
- no blended total in APIs/views;
- reset/replay works;
- RLS and append-only protections remain intact.

Run representative API reads after seeding.

12. DOCUMENTATION

Create/update a concise data/simulation development note containing:

- audit results;
- dataset profile;
- seeds;
- distributions;
- Bangladesh-context assumptions;
- scenario definitions;
- faults;
- apply/dry-run/reset commands;
- limitations.

Do not mark analytics, alert, case, or validation features complete merely
because tables exist.

13. EXIT GATE

Do not declare completion unless:

- same seed/config reproduces the semantic dataset;
- all outlets show shared cash plus three separate provider balances;
- faults are reproducible;
- rejected input never updates the ledger;
- dashboard/API never blends balances;
- moderate dataset generation and validation pass;
- seed/data migration is idempotent;
- local/temporary DB apply passes;
- Supabase apply is verified when credentials are available;
- all required Phase 3 APIs and integration tests pass.

Report before/after counts, exact seeds, date range, files changed, commands,
API verification, RLS/append-only results, and blockers.
```

---

# Phase 4 — Data Quality and Intelligence

**Recommended target:** Claude Code with Claude Opus 4.8

## Features in this phase

- Data Quality & Confidence Engine
- Fresh/stale/missing/conflicting classification
- Shared-cash and provider-specific liquidity forecasting
- Near-identical-amount anomaly rule
- Structured evidence and plausible benign context
- Degraded-data confidence reduction and anomaly suppression
- Persisted analytical results
- `ResultEnvelope` and `AlertCandidate` adapter
- Scenario A–C analytics

## Deliverables

- Quality, liquidity, and anomaly engines
- Persisted analytics runs/results/evidence
- Intelligence APIs
- Scenario A/B/C fixtures and expected outputs
- Unit, boundary, property, integration, and serialization tests
- Tuning report without contaminating held-out data

## Prompt

```text
You are a senior analytics engineer, backend engineer, and responsible
decision-support designer working through Claude Code with Claude Opus 4.8.

Implement Phase 4 — Data Quality and Intelligence.

Prerequisite: Phase 3 must provide deterministic normalized data, stable
scenario runs, append-only ledger reads, and separated reserves.

Do not implement alert/case workflow, authentication UI, or the final frontend
in this phase.

1. AUDIT AND FREEZE CONFIGURATION

Inspect current contracts, data, scenarios, physical schema, analytics stubs,
tests, and OpenAPI.

Freeze all configurable thresholds in versioned configuration, not hard-coded
inside engines:

- freshness threshold;
- required fields/feed expectations;
- minimum sample count;
- analysis and forecast windows;
- confidence mapping;
- amount tolerance;
- anomaly window;
- minimum matching count;
- eligible transaction types/statuses;
- degraded-data suppression conditions.

Keep tuning, held-out, and demo data separate. Do not tune on held-out results.

2. PURE ENGINE BOUNDARIES

Engines must accept normalized typed input, not HTTP requests, ORM sessions, or
database clients.

Preserve:

normalized input → quality/analytics engine
engine → ResultEnvelope
persisted result → AlertCandidate

Every output must include engine version, configuration/hash, simulation run,
outlet, provider/account where applicable, input window, as-of time,
confidence, evidence/signals, and creation time.

3. DATA QUALITY ENGINE

Implement classification precedence:

1. conflicting
2. missing
3. stale
4. fresh

Support issues:

- late arrival;
- missing feed;
- missing field;
- conflicting snapshot;
- impossible transition;
- insufficient samples;
- malformed payload.

Output:

- status;
- confidence modifier;
- sample count;
- latest source time;
- issue evidence;
- last trusted value/time where supported;
- safe summary.

Rules:

- missing normally makes downstream output unavailable;
- conflicting data must not silently choose a candidate as truth;
- degraded data never raises confidence;
- preserve conflicting candidates for display/audit.

4. LIQUIDITY ENGINE

Forecast independently:

- shared physical cash;
- each provider e-money reserve.

Use a transparent recent-window depletion/burn-rate method.

Rules:

- no division by zero;
- zero/negative depletion means no shortage time;
- insufficient samples produce non-actionable output;
- degraded but usable data lowers confidence and widens bounds;
- missing/conflicting data becomes unavailable or clearly non-actionable;
- never mix providers.

Output current balance, burn rate, projected shortage, bounds, confidence,
sample count, actionable flag/reason, and ordered signals such as recent
cash-out velocity, rate stability, sample adequacy, and feed freshness.

5. ANOMALY ENGINE

Implement one complete rule: near-identical amounts within one
outlet/provider/window.

Output:

- rule/version;
- exact time window;
- amount cluster;
- transaction count;
- synthetic party count;
- linked transaction IDs;
- confidence;
- disposition;
- reason code;
- structured evidence;
- plausible benign explanation.

Use safe language only.

6. SUPPRESSION

Under configured degraded data:

- retain the computed anomaly evaluation;
- set disposition to suppressed_data_quality;
- include suppression reason and quality reference;
- prevent candidate eligibility as anomaly/combined alert;
- permit a separate data-quality advisory candidate.

Do not discard suppressed results because they are required for evaluation.

7. PERSISTENCE AND APIS

Implement transactional persistence for:

- quality assessments/issues;
- analytics runs;
- projections, signals, and quality links;
- anomaly flags, evidence, and transaction links.

Implement:

- current/history quality reads if not final already;
- liquidity projection read;
- internal liquidity run;
- anomaly list/detail;
- internal anomaly run.

Internal run routes must be service-only. Browser clients must not call them
directly.

8. RESULT AND CANDIDATE ADAPTER

Produce validated ResultEnvelope records and transform persisted, alertable
results into AlertCandidate.

Rules:

- use typed persisted source IDs;
- preserve confidence/evidence;
- do not include case owner/status;
- actionable anomaly/combined candidate requires benign context;
- suppressed anomaly is rejected;
- provider/outlet/source IDs must agree;
- recommended next step remains advisory.

9. TESTS

Test:

- exact freshness boundary;
- missing/conflicting/malformed data;
- minimum sample boundary;
- zero and replenishing balances;
- known shortage;
- shared cash and every provider separately;
- confidence degradation and widened bounds;
- exact amount-tolerance/window/count boundaries;
- known Scenario B positive;
- normal festival/high-demand negative or benign case;
- Scenario C suppression;
- provider isolation;
- decimal/timestamp/evidence ordering round trip;
- deterministic same-seed outputs;
- prohibited language scan.

10. SCENARIO RESULTS

Verify:

- Scenario A identifies the correct reserve and approximate shortage with
  confidence and signals;
- Scenario B produces evidence-backed unusual activity with plausible benign
  context;
- Scenario C lowers/unavailable confidence and suppresses anomaly alertability;
- normal operation does not create obvious false positives.

11. EXIT GATE

Do not declare completion unless engines are reproducible, persisted results
round-trip without changing meaning, candidate mapping preserves evidence,
A/B/C behavior passes, provider balances never mix, and all tests pass.

Report engine/config versions, fixture seeds, tuning-only results, commands,
test counts, API examples, current limitations, and blockers.
```

---

# Phase 5 — Alerts, Cases and Security

**Recommended target:** Claude Code with Claude Opus 4.8

## Features in this phase

- Demo authentication and profiles
- Provider/outlet/area-scoped authorization
- Immutable alerts and typed evidence links
- English and Bangla/Banglish explanation snapshots
- Routing and initial case creation
- Assignment, acknowledgement, escalation, notes, review, and resolution
- Notifications
- Timeline and append-only audit
- Idempotency and optimistic concurrency
- Scenario D API workflow

## Deliverables

- Complete auth/profile API group
- Complete alert/case/notification/audit API group
- Routing and localized explanation services
- Legal workflow implementation
- Application authorization and RLS verification
- Idempotency/concurrency tests
- Scenario D script and evidence

## Prompt

```text
You are a senior backend security engineer, workflow architect, and API
developer working through Claude Code with Claude Opus 4.8.

Implement Phase 5 — Alerts, Cases and Security.

Prerequisite: Phase 4 must produce persisted quality/projection/anomaly results
and valid AlertCandidate objects.

Do not alter Member 3-style analytical evidence, recalculate confidence, or
create financial-action endpoints.

1. INSPECT AND VERIFY CONTRACTS

Read current schema, routes, OpenAPI, ResultEnvelope, AlertCandidate,
authorization/RLS design, explanation templates, workflow constraints, tests,
and scenario fixtures.

Run the baseline tests. Preserve existing correct code.

2. DEMO AUTHENTICATION AND PROFILE

Implement:

- POST /api/v1/auth/demo-login
- GET /api/v1/me
- PATCH /api/v1/me/preferences

Seed synthetic demo users for agent, field officer, area manager, provider
operations, risk analyst, management, and setup/admin as required.

The server chooses roles/scopes. The client must not construct arbitrary
provider, area, or outlet permissions.

Preferences may update locale only.

Never store application password hashes, tokens, PINs, or credentials in
domain tables.

3. APPLICATION AUTHORIZATION

Implement explicit policy evaluation using active role assignments.

Rules:

- agent requires assigned outlet;
- field/area roles require configured area and normally provider;
- provider_ops/risk require provider;
- management defaults to aggregate/read-only;
- missing provider scope is not all providers;
- admin is demo/setup only, not a normal operational shortcut.

Apply authorization to every confidential route and continue using PostgreSQL
RLS as defense in depth.

A forbidden cross-provider lookup must return the same public 404 shape as a
missing record.

Test provider A/B isolation across alerts, cases, notes, evidence,
notifications, and audit.

4. ALERT CANDIDATE CONSUMPTION

Validate:

- candidate version/type/severity;
- provider/outlet/source consistency;
- typed persisted source IDs;
- source alertability;
- deduplication key;
- structured variables;
- benign context for anomaly/combined;
- advisory next step;
- suppressed anomaly rejection.

Do not copy raw transaction arrays when typed source links are enough. Do not
modify confidence or evidence.

5. IMMUTABLE ALERTS

Implement active-alert deduplication and immutable publication.

Persist:

- scope;
- type/severity;
- typed source links;
- structured payload;
- detected time;
- requires-case state;
- explanation snapshots.

After publication, analytical content is immutable. Only allowed lifecycle
metadata may change and must be audited.

6. LOCALIZED EXPLANATIONS

Render and save immutable snapshots for:

- English for every important alert;
- Bangla or Banglish for required demo alerts.

Every render contains:

- situation;
- evidence;
- uncertainty;
- safe next step;
- plausible benign context where applicable.

Use structured variables only. Never use free-form LLM financial advice.

7. ROUTING AND CASE CREATION

Implement routing order:

exact provider+area → provider only → area only → global fallback
then priority.

Open a case only when required.

Store:

- source alert;
- provider/outlet scope;
- recipient role/user;
- current owner;
- recommended safe next step;
- current status;
- version.

8. LEGAL WORKFLOW

Implement explicit action endpoints for:

- assignments/reassignments;
- acknowledge;
- escalate;
- notes;
- review;
- resolve.

Allowed transitions:

- open → acknowledged;
- open → escalated;
- acknowledged → escalated;
- acknowledged → resolved;
- escalated → resolved.

Reject all others. Reopening is outside the MVP.

Escalation requires target and reason. Resolution requires summary and
timestamp. Reviews use benign_operational, requires_follow_up,
data_quality_issue, confirmed_unusual, or inconclusive—never a fraud verdict.

9. IDEMPOTENCY AND CONCURRENCY

Every mutating POST accepts Idempotency-Key.

Requirements:

- same key + same request returns the original logical result;
- same key + different request is rejected;
- duplicate actions do not duplicate cases, assignments, status events, notes,
  notifications, or audits;
- case-changing actions require current version or If-Match;
- stale updates return 409 and change nothing;
- workflow mutation and audit event commit in one transaction.

10. NOTIFICATIONS, TIMELINE, AND AUDIT

Implement:

- notification list/read;
- queued/delivered/read in-app notifications;
- case timeline;
- audit-event reads.

Audit at minimum alert publication/state, case creation/routing, assignment,
acknowledgement, escalation, notes, review, resolution, and notification events.

Audit rows are append-only and cannot be updated/deleted by application roles.

11. ENDPOINTS

Complete the Phase 5 endpoint map exactly. Do not add generic PATCH status or
financial-action routes.

Implement safe error shape, request IDs, locale selection/fallback, filters,
pagination where defined, and proper auth on all confidential endpoints.

12. TESTS

Test:

- valid/invalid login and inactive user;
- profile/scopes/locale;
- own and other provider/outlet/area;
- missing/forbidden same 404 shape;
- candidate scope/source/suppression;
- deduplication including concurrent duplicate;
- immutable alert fields;
- EN and localized render coverage;
- routing precedence;
- case creation/no-case advisory;
- every legal/illegal transition;
- required reason/summary;
- idempotency;
- stale version and simultaneous updates;
- assignments, notes, reviews;
- notifications;
- audit completeness and ordering;
- RLS and application policy;
- Scenario D end to end.

13. EXIT GATE

Do not declare completion unless Scenario D works without direct DB edits,
provider A cannot enumerate/read/mutate provider B records, duplicates and
stale writes fail safely, evidence remains immutable, and timeline/audit is
complete.

Report exact endpoints, seeded demo identities/scopes without secrets,
commands/results, Scenario D script, denial proof, idempotency/concurrency
evidence, known limitations, and blockers.
```

---

# Phase 6 — Integrated API and Thin UI

**Recommended target:** Codex with GPT-5.6 Sol

## Features in this phase

- Unified backend router composition
- Auth on every confidential endpoint
- Complete Scenarios A–D
- Separate frontend Version 2
- Minimal, professional, Apple-inspired visual system
- Dashboard, insights, alert, case, notifications, demo controls, and validation pages
- Loading, empty, degraded, error, forbidden, and conflict states
- End-to-end regression and MVP freeze

## Deliverables

- One-command backend and frontend
- Isolated `frontend-v2/`
- Complete MVP page set
- Typed API integration
- A–D end-to-end flow
- Frozen OpenAPI and release candidate
- E2E tests and backup captures
- Version 1 regression proof

## Prompt

```text
You are a senior frontend architect, UX engineer, API integration engineer, and
release-integration engineer working through Codex with GPT-5.6 Sol.

Implement Phase 6 — Integrated API and Thin UI.

The repository already contains an earlier frontend. Build the new frontend as
Version 2 in `frontend-v2/` or the equivalent isolated workspace location.
Do not overwrite, delete, or destabilize Version 1. Both versions must remain
independently runnable.

Prerequisites: Phase 3 data, Phase 4 intelligence, and Phase 5 workflow/security
gates must pass.

1. AUDIT BEFORE IMPLEMENTATION

Inspect:

- latest phase plan;
- frontend-page-plan.md;
- current backend routes and generated OpenAPI;
- actual auth/scopes;
- current response DTOs;
- existing frontend Version 1;
- tests and implementation status.

Reclassify endpoints as usable, partial, stub, absent, or internal. Do not
pretend a 501 or absent endpoint works.

2. INTEGRATE THE BACKEND

Register all routers through one application composition path.

Verify:

- startup/shutdown;
- migrations and seeds;
- deterministic reset;
- current OpenAPI;
- request IDs/logs;
- auth dependency on every confidential route;
- provider/outlet/area policy;
- no internal analytics or raw ingestion endpoint is called by normal browser
  code.

3. VERSION 2 FOUNDATION

Create:

- isolated package/configuration;
- `.env.example` with placeholders:
  `NEXT_PUBLIC_API_BASE_URL`,
  `NEXT_PUBLIC_DEFAULT_LOCALE`,
  `NEXT_PUBLIC_ENABLE_DEV_FIXTURES=false`;
- typed API client;
- generated OpenAPI types where practical;
- auth/session bootstrap;
- safe error normalization;
- query/cache layer;
- semantic design tokens;
- README and frontend documentation.

Never expose Supabase service-role credentials to the browser. Production must
not silently use fixtures.

4. REQUIRED PAGES

Implement:

- `/login`;
- `/work?view=alerts|cases`;
- `/outlets/[outletId]`;
- `/outlets/[outletId]/insights?tab=liquidity|quality|activity|history`;
- `/alerts/[alertId]`;
- `/cases/[caseId]`;
- `/notifications`;
- `/demo`;
- `/validation`;
- `/forbidden`, not-found, route/global error, offline, and 501 states.

After the MVP works, add `/outlets` and `/settings/preferences` if still useful.

Do not build stretch planning/relationship/nearby-support pages.

5. ROLE-AWARE FLOW

Root redirect:

- unauthenticated → login;
- agent → own outlet;
- field/area/provider ops/risk → work queue;
- management → aggregate-safe read-only work view;
- demo/setup → demo controls.

Use backend-issued profile and permissions. Frontend hiding is not security.
Clear all scoped caches on logout/identity change.

6. OUTLET EXPERIENCE

Dashboard must show:

- one separate shared-cash section;
- separate bKash, Nagad, Rocket cards;
- data health and source timestamp;
- confidence and shortage time;
- contributing signals;
- active alerts.

Never show a blended total.

Insights must support liquidity, quality, unusual activity, and history with
provider filters, human-readable evidence, benign context, accessible charts,
and suppressed-data-quality state.

7. ALERT AND CASE EXPERIENCE

Alert detail must separate immutable evidence from linked mutable case state
and show situation, evidence, confidence, uncertainty, benign context, next
step, recipient, owner/status, locale, source time, and quality warnings.

Case workspace must support only legal actions:

- assignment;
- acknowledge;
- escalate with reason;
- note;
- review;
- resolve with summary;
- timeline;
- separate audit history.

Use Idempotency-Key and version/If-Match as supported. Preserve drafts on
network or 409/412 conflict.

8. DEMO AND VALIDATION

Demo controls must run/reset Scenarios A–D, apply/recover faults, poll run
status, and deep-link to generated outlet/alert/case artifacts.

Validation page must show real metrics only, each with value, unit, sample,
method, run/configuration, and limitations.

9. DESIGN DIRECTION

Use an Apple-inspired philosophy, not an Apple clone:

- strong typography;
- generous whitespace;
- restrained color;
- precise alignment;
- subtle borders;
- minimal shadows;
- calm hierarchy;
- system fonts that work offline.

Avoid the previously supplied AI-looking style:

- excessive pastel pills;
- badge around every value;
- repeated white rounded cards;
- thick colored top borders;
- generic admin-dashboard layout;
- duplicated evidence cards;
- raw ISO/key-value dumps;
- wide instructional banners everywhere;
- glassmorphism, neon, gradients, decorative blobs, or excessive shadows.

Use spacing and typography as the main hierarchy. Do not turn every component
into a card.

10. API INTEGRATION

Organize clients by domain: auth, reference, ledger, quality, intelligence,
alerts, cases, notifications, simulation, validation.

Requirements:

- use current OpenAPI;
- do not duplicate enums manually;
- preserve request IDs;
- send locale;
- normalize 401/403/404/409/412/422/429/500/501;
- cache by identity/scope;
- poll active runs and cases appropriately;
- reuse the same idempotency key on transport retry;
- never automatically retry a mutation with a new key;
- never call service-only routes from browser code.

If a required endpoint is unavailable, show a professional unavailable state
and document the gap. Fixture mode must be explicit and disabled by default.

11. ACCESSIBILITY AND RESPONSIVENESS

Support desktop judge presentation, tablet operations, and mobile agent use.

Include keyboard support, visible focus, landmarks, skip link, semantic
headings, accessible dialogs/tables/charts, text status in addition to color,
Bangla rendering, locale-aware dates/numbers, reduced motion, sufficient
contrast, and practical touch targets.

12. E2E FLOW

Verify:

login → authorized landing → outlet/work queue → insights → alert → case →
assignment → acknowledgement → escalation/note/review → resolution →
notification → timeline/audit → validation.

Run deterministic Scenarios A–D end to end.

13. TESTS

Run:

- lint;
- type check;
- production build;
- component/API client tests;
- route smoke;
- accessibility checks;
- responsive checks;
- E2E tests;
- Version 1 regression.

Test provider separation, degraded data, suppression, immutable evidence,
legal actions, idempotency, conflicts, cross-provider denial, locale fallback,
and all required states.

14. MVP FREEZE GATE

Do not declare completion or begin stretch work unless:

- shared cash and three providers remain separate;
- shortage time/confidence works;
- one anomaly has evidence and benign context;
- degraded data safely lowers/suppresses;
- case lifecycle and audit work;
- EN and Bangla/Banglish render;
- provider boundary passes;
- no unsafe language/action exists;
- backend/frontend run with documented commands;
- Version 1 remains runnable;
- lint, type, tests, build, and A–D E2E pass.

Report files, pages, components, endpoints, A–D flow, design decisions, exact
test results, release candidate ID, backup captures, and blockers.
```

---

# Phase 7 — Validation, Observability and Safety

**Recommended target:** Codex with GPT-5.6 Sol

## Features in this phase

- Held-out analytical evaluation
- Forecast and anomaly metrics
- API latency and reliability measurements
- Data-quality handling, explanation, audit, and authorization metrics
- `/health`, `/metrics`, and validation results
- Structured logs
- Secret, identity, unsafe-language, and prohibited-action scans
- Frozen release evidence

## Deliverables

- At least three measured metrics
- Raw and summarized validation artifacts
- Performance/reliability report
- Security/safety scan report
- Validation endpoints
- Signed release candidate and exact evidence mapping

## Prompt

```text
You are a senior validation engineer, SRE, security tester, and responsible-AI
evaluation engineer working through Codex with GPT-5.6 Sol.

Implement Phase 7 — Validation, Observability and Safety against the frozen
Phase 6 release candidate.

Do not add product features, redesign architecture, or tune thresholds using
held-out failures. Fix only genuine implementation defects and rerun the full
affected evaluation.

1. FREEZE THE TARGET

Record:

- release/commit identifier;
- schema/migration version;
- engine/rule versions;
- configuration hash;
- dataset manifest and seeds;
- frontend/backend build identifiers;
- deterministic reset command.

Verify A–D regression passes before measuring.

2. HELD-OUT DATA INTEGRITY

Confirm the held-out split was not used for tuning.

Record:

- sample size;
- labels;
- scenarios/seeds;
- date range;
- class distribution;
- known limitations.

If tuning/held-out leakage exists, stop and repair the evaluation design before
publishing metrics.

3. ANALYTICS METRICS

Measure where supported:

- anomaly precision;
- anomaly recall;
- false-positive rate;
- confusion matrix;
- forecast MAE in minutes or shortage detection lead time;
- provider/reserve-level forecast error;
- data-quality degradation/suppression correctness.

Every metric must include value, unit, sample size, formula/method, dataset,
seeds, versions, configuration, raw evidence path, interpretation, and
limitations.

Handle zero denominators honestly. Never fabricate a value.

4. PERFORMANCE AND RELIABILITY

At a documented synthetic volume, measure:

- average API latency;
- p50/p95/p99 where appropriate;
- error rate;
- dashboard and core analytical endpoint latency;
- data-quality incident handling rate;
- explanation coverage;
- legal transition acceptance/rejection;
- notification correctness;
- audit completeness;
- idempotency correctness;
- stale/concurrent update correctness;
- provider-denial success.

Use realistic but moderate load. Do not make production-scale claims.

5. OBSERVABILITY

Complete/verify:

- request IDs;
- structured request/error logs;
- audit correlation;
- health endpoint;
- metrics endpoint or protected JSON summary;
- validation-result endpoint;
- counts for data-quality events, alerts, cases, failures, and latency.

Do not expose confidential data, credentials, raw provider evidence, or
service keys in metrics/logs.

6. SAFETY AND SECURITY

Run scans/tests for:

- committed secrets;
- real names/phone/account-like values;
- unsafe endpoint names/actions;
- definitive fraud language;
- unsupported production/regulatory claims;
- cross-provider authorization;
- RLS;
- append-only/immutability;
- alert/case boundary;
- missing/forbidden response non-leakage;
- role/scope escalation;
- browser exposure of internal/service routes.

Verify a degraded provider never generates a new high-confidence anomaly alert.

7. RAW ARTIFACTS

Store reproducible machine-readable evidence under the repository’s evidence
directory, including:

- evaluation inputs and manifest references;
- confusion matrix;
- forecast error records;
- latency summary;
- reliability/security matrix;
- safety/secret scan;
- exact commands;
- release metadata.

Do not store secrets or another provider’s confidential payload in shared
reports.

8. VALIDATION PERSISTENCE AND API

Persist completed validation runs, ground-truth links, and metric results where
the schema requires it.

Verify `/metrics` and `/api/v1/validation/results` return values matching the
stored evidence without silently recalculating them differently.

9. TEST AND DEFECT POLICY

For each defect include release, seed, request/input, expected, actual, failed
invariant, severity, reproduction, evidence, owner, and retest requirement.

After a fix, rerun all affected held-out and regression tests consistently.
Do not cherry-pick only improved cases.

10. DELIVERABLES

Create concise current reports for:

- analytics validation;
- performance/reliability;
- security/safety;
- limitations.

These may later be consolidated in Phase 8, but values and raw evidence must be
final now.

11. EXIT GATE

Do not declare completion unless:

- at least three credible numeric metrics exist;
- every metric has method/sample/limitation;
- evidence matches the exact frozen build;
- bad data never appears confidently normal;
- every high-impact alert has evidence and uncertainty;
- provider boundary, audit, idempotency, and concurrency tests pass;
- no critical privacy/security/responsible-design issue remains;
- validation endpoints match stored evidence.

Report exact commands/results, metric table, raw artifact paths, release ID,
limitations, defects fixed, and remaining blockers.
```

---

# Phase 8 — Documentation and Presentation

**Recommended target:** Codex with GPT-5.6 Sol

## Features in this phase

- Submission-ready README
- Architecture and provider-boundary documentation
- Data/simulation note
- Validation evidence
- Responsible-design note
- API guide and OpenAPI
- Demo guide
- Final presentation
- Documentation cleanup and consolidation
- Rehearsed story-driven demo

## Deliverables

- Working prototype and source repository
- Root README/setup instructions
- Architecture diagram
- Data and simulation note
- Validation evidence
- Responsible-design note
- Final presentation
- Backup screenshots/responses
- Clean, concise `docs/` structure

## Prompt

```text
You are a senior technical writer, software architect, documentation engineer,
and presentation strategist working through Codex with GPT-5.6 Sol.

Implement Phase 8 — Documentation and Presentation for the frozen, validated
Multi-Provider Agent Liquidity & Coordination Platform.

Do not change application behavior. Documentation must describe the exact
tested build and current evidence.

1. AUDIT REQUIRED DELIVERABLES

Read the original problem statement completely and extract all mandatory
deliverables, scenarios, guardrails, success criteria, and evaluation
categories.

Inspect:

- all files under docs/;
- root/backend/frontend READMEs;
- schema and ADRs;
- OpenAPI;
- migrations/seeds;
- current dataset and validation artifacts;
- current frontend/backend;
- screenshots;
- presentation drafts;
- CI/scripts referencing documentation.

Verify every claim against implementation, tests, database, OpenAPI, and
Phase 7 evidence.

2. FINAL DOCUMENTATION STRUCTURE

Consolidate into a concise structure such as:

README.md
docs/
  README.md
  architecture.md
  data-and-simulation.md
  validation-evidence.md
  responsible-design.md
  demo-guide.md
  api-reference.md
  schema.md
  diagrams/
  openapi/
  evidence/
  presentation/

Do not create empty folders or duplicate documents.

3. ROOT README

Include concise, verified:

- problem and product;
- connected end-to-end flow;
- features;
- exact stack;
- repository structure;
- prerequisites;
- environment setup;
- Supabase/database setup;
- migrations/seeds;
- backend/frontend commands;
- tests;
- deterministic demo/reset;
- demo identities without secrets;
- Scenario A–D summary;
- API/OpenAPI links;
- documentation index;
- responsible-use disclaimer;
- current limitations.

Every command must be tested.

4. ARCHITECTURE

Create/update architecture.md and diagram showing:

- frontend;
- modular-monolith backend modules;
- Supabase/PostgreSQL;
- provider feeds;
- shared cash versus separate provider e-money;
- data quality;
- forecasting;
- anomaly evidence;
- immutable alerts;
- mutable cases;
- localization;
- auth/RLS;
- notification/audit;
- validation/observability;
- provider boundaries;
- deployment topology.

Do not retain a duplicate system-design document with the same content.

5. DATA AND SIMULATION NOTE

Document actual:

- synthetic-only policy;
- Bangladesh-context assumptions;
- areas/outlets/providers;
- dates and row counts;
- transaction/status distributions;
- seeds and reset;
- normal and A–D;
- faults;
- balance generation;
- ground truth;
- benign lookalikes;
- assumptions;
- limitations;
- reproduction commands;
- evidence paths.

6. VALIDATION EVIDENCE

Document only measured Phase 7 values.

For each metric include value, unit, sample, split, seed/config, version,
method, raw evidence, interpretation, and limitation.

Explain tuning versus held out, false positives, uncertainty, and failure
modes.

7. RESPONSIBLE DESIGN

Document:

- advisory-only purpose;
- synthetic privacy;
- provider separation;
- human review;
- anomaly is not fraud;
- benign explanations;
- degraded-data behavior;
- roles/scopes/RLS;
- immutable evidence and audit;
- safe language;
- fairness;
- limitations;
- prohibited actions.

Explicitly state the system cannot transfer, convert, settle, refill, recover,
reverse real transactions, block, freeze, accuse, access production APIs,
collect credentials, or claim production/regulatory readiness.

8. DEMO GUIDE

Create a concise operational guide with:

- prerequisites/startup/reset;
- demo roles/scopes;
- initial state;
- Scenario A;
- Scenario B;
- Scenario C;
- Scenario D;
- provider-denial demonstration;
- validation page;
- expected outputs;
- recovery/troubleshooting;
- backup screenshots/responses.

Use one connected narrative.

9. API REFERENCE

Create a concise human guide for base path, auth, scopes, errors, request IDs,
pagination, decimals, locale, idempotency, concurrency, endpoint groups,
internal-only endpoints, and OpenAPI location.

Do not reproduce every schema already in OpenAPI.

10. PRESENTATION

Create/verify the final deck covering:

- problem/users;
- A;
- B;
- C;
- D;
- architecture;
- provider boundaries;
- metrics;
- responsible design;
- limitations;
- next steps.

Prepare at most one concise speaker/demo outline and backup media.

Rehearse twice from a clean deterministic reset, time it, record blockers, and
freeze slides/wording/backups after success.

11. CLEANUP

Classify every docs file as final required, supporting, machine contract,
evidence, development-only, or obsolete.

After consolidation, delete unneeded phase distributions, checklists,
member plans, prompts, progress trackers, superseded plans/audits, duplicate
system designs, obsolete data profiles, old metric summaries, and presentation
drafts.

Do not delete blindly. Search repository references first. Retain current
OpenAPI, schema, architecture diagram, evidence, and backup snapshots.

For ADRs, retain only currently relevant architectural/schema/security
decisions or consolidate them carefully before deletion.

12. WRITING STANDARD

Be precise and professional. Avoid filler, implementation diaries, repeated
theory, unsupported claims, marketing exaggeration, and duplicated content.

13. VERIFICATION

Run link checks and verify:

- every README/demo command;
- file links;
- OpenAPI;
- schema;
- metric values;
- screenshots;
- secrets;
- unsafe language;
- production/regulatory claims;
- references to deleted files.

14. EXIT GATE

Do not declare submission-ready unless all seven official deliverables exist,
commands reproduce the project, architecture/data/metrics match the build,
responsible-design boundaries are complete, presentation exists, rehearsal
passes, and no broken links/essential missing evidence remain.

Report files created/rewritten/moved/deleted, ADR/evidence retention,
conflicts found, commands verified, rehearsal result, missing deliverables, and
readiness status.
```

---

# Phase 9 — Final QA and Submission

**Recommended target:** Codex with GPT-5.6 Sol

## Features in this phase

- Frozen release verification
- Critical migration/backend/frontend/E2E tests
- Exact deterministic demo
- Metrics-to-build consistency check
- Permission and deployment verification
- Final secret/data/language/action scan
- Submission package audit
- Submission confirmation and stable backup

## Deliverables

- Final tested release identifier
- Critical test report
- Final checklist
- Permission/access proof
- Submission receipt/link
- Preserved stable local build and backup media
- Explicit disclosure of any remaining omission

## Prompt

```text
You are a senior release engineer, QA lead, security auditor, and submission
manager working through Codex with GPT-5.6 Sol.

Execute Phase 9 — Final QA and Submission.

This is a freeze-and-protect phase. Do not refactor, redesign, retune
thresholds, casually change schema, rename contracts, or add features.

Only fix:

- startup blockers;
- incorrect mandatory output;
- safety/security failures;
- missing mandatory deliverables;
- access/permission problems;
- submission blockers.

Any fix requires the affected regression tests to rerun.

1. FREEZE THE CANDIDATE

Record:

- Git commit/release ID;
- schema/migration versions and checksums;
- seed/dataset manifest hash;
- engine/config versions;
- OpenAPI version/hash;
- backend/frontend build identifiers;
- metric/validation run IDs;
- presentation version;
- deterministic reset command.

Ensure the working tree contains only intended final artifacts.

2. CLEAN ENVIRONMENT REPRODUCTION

From a clean environment where practical:

- install dependencies;
- validate environment examples;
- apply migrations;
- apply seeds/dataset;
- start backend;
- verify health/database readiness;
- build/start frontend;
- regenerate/compare OpenAPI;
- run critical tests.

Do not rely on untracked local files or undocumented manual database edits.

3. CRITICAL TEST MATRIX

Run:

- migration clean apply and re-run;
- schema/constraint/view/RLS tests;
- backend unit/integration tests;
- frontend lint/type/build/tests;
- A–D E2E;
- auth/provider denial;
- idempotency;
- stale concurrency;
- append-only/immutability;
- localization;
- validation endpoint;
- documentation link/command checks.

Record exact commands, versions, counts, and failures.

4. EXACT DEMO

Reset to the documented deterministic state and run the complete presentation
flow once exactly as the judge will see it:

- login and scope;
- shared cash and separate provider balances;
- Scenario A shortage/confidence;
- Scenario B evidence/benign context;
- Scenario C degradation/suppression;
- Scenario D routing/assignment/acknowledgement/escalation/note/review/
  resolution/audit;
- provider A/B denial;
- validation metrics.

Verify expected values and backup captures match.

5. METRIC CONSISTENCY

Compare:

- displayed metrics;
- validation API/database values;
- docs;
- slides;
- raw evidence;
- release ID and dataset.

Any mismatch is a blocker. Do not change a metric cosmetically without
recomputing evidence.

6. SECURITY AND SAFETY FINAL SCAN

Scan repository, built frontend, sample data, docs, and presentation for:

- secrets/keys/passwords/tokens;
- real identities, phone/account-like data;
- unsafe endpoint/action names;
- definitive fraud language;
- unsupported provider integration;
- production/regulatory claims;
- cross-provider data leakage;
- browser exposure of service credentials;
- debug/admin bypasses;
- internal-only routes exposed to normal clients.

7. DELIVERABLE AUDIT

Confirm inclusion and correctness of:

- source repository;
- README;
- `.env.example`;
- migrations;
- seeds/sample data;
- OpenAPI;
- architecture diagram;
- data/simulation note;
- validation evidence;
- responsible-design note;
- final presentation;
- backup media;
- license or repository metadata if required.

Do not include obsolete phase/checklist/prompt clutter if Phase 8 intentionally
removed it.

8. PERMISSION AND ACCESS CHECK

From a non-owner/incognito view, verify:

- repository access;
- deployment URL;
- backend/frontend availability;
- presentation access;
- shared media access;
- no secret/private file exposure.

9. SUBMISSION

Submit the exact frozen artifacts and URLs. Record:

- submission time;
- submission identifier/receipt;
- repository link;
- deployment link;
- presentation link;
- any upload/checksum information.

Confirm the links after submission.

Preserve the exact tested local build, environment-independent backup
instructions, screenshots, and media unchanged.

10. DEFECT POLICY

For any blocker, record severity, reproduction, expected/actual, affected
invariant, proposed minimal fix, tests to rerun, and final result.

Do not hide unresolved omissions. Explicitly disclose them in the final
checklist.

11. EXIT GATE

Do not declare completion unless:

- critical tests pass or every exception is documented;
- exact demo succeeds;
- metrics/docs/slides match the frozen build;
- permissions work from a non-owner view;
- final scans are clean;
- all mandatory deliverables exist;
- submission receipt/link is confirmed;
- stable backup is preserved.

Final response must contain release ID, commands/results, demo result,
permission checks, scan results, deliverable checklist, submission receipt,
fixes made, regressions rerun, and any disclosed omissions.
```

---

# Suggested execution map

| Phase | Suggested agent |
|---|---|
| 1 | Claude Code — Opus 4.8 |
| 2 | Claude Code — Opus 4.8 |
| 3 | Codex — GPT-5.6 Sol |
| 4 | Claude Code — Opus 4.8 |
| 5 | Claude Code — Opus 4.8 |
| 6 | Codex — GPT-5.6 Sol |
| 7 | Codex — GPT-5.6 Sol |
| 8 | Codex — GPT-5.6 Sol |
| 9 | Codex — GPT-5.6 Sol |

## Final project success chain

```text
Authoritative schema
→ separate provider data and shared cash
→ deterministic simulation and ingestion
→ visible data quality
→ liquidity forecast and unusual-activity evidence
→ immutable localized alert
→ provider-aware human case
→ traceable resolution
→ measured validation
→ concise documentation
→ tested submission
```
