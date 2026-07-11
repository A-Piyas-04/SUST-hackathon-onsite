# Solo Project Phase Distribution

## 1. Planning Assumption

This plan is for **one solo developer starting from zero**. Treat the backend and frontend as empty implementation directories. Do not assume that any existing route, migration, model, service, fixture, test, seed, UI component or deployment setup is reusable or complete.

The filename is retained for repository continuity, but this plan intentionally contains **no hour or duration allocation**. Progress is controlled by phase prerequisites and exit gates.

The implementation order is deliberately schema-first:

```text
Authoritative schema
    ↓
Physical migrations, constraints, views and RLS
    ↓
Application foundation and contracts
    ↓
Synthetic data, ingestion and ledger
    ↓
Data quality, forecasting and anomaly engines
    ↓
Alerts, cases, localization, audit and security
    ↓
Integrated API and thin UI
    ↓
Validation, documentation and presentation
```

## 2. Product Objective

Build a complete, explainable and safe decision-support prototype that:

1. Shows one shared physical-cash reserve alongside separate bKash, Nagad and Rocket e-money balances.
2. Predicts which reserve may run short and approximately when, with confidence on every projection.
3. Detects at least one unusual pattern with structured evidence and plausible benign context.
4. Reduces confidence or becomes non-actionable when data is missing, stale, malformed or conflicting.
5. Converts important analytical results into immutable alerts and provider-aware human cases.
6. Supports routing, assignment, acknowledgement, escalation, notes, notification, review and resolution.
7. Preserves a complete audit trail.
8. Renders structured English and Bangla/Banglish alert explanations.
9. Enforces provider/outlet/area boundaries with application authorization and PostgreSQL RLS.
10. Uses synthetic data only and never executes financial or punitive actions.

## 3. Hard Guardrails

- Shared cash and provider e-money are separate reserves. Never blend or convert them.
- No real provider integration, wallet, account, customer identity, credential, PIN, OTP, password or secret data.
- No endpoint or table may transfer, convert, settle, refill, recover, reverse, block, freeze, accuse or make a fraud decision.
- An anomaly means “unusual” or “requires review,” never proof of fraud.
- Alerts preserve analytical evidence; cases own the mutable human workflow.
- Conflicting source snapshots remain preserved and visibly lower confidence.
- Suppressed anomaly evaluations remain measurable but cannot create a high-confidence anomaly alert.
- Provider A users cannot read or mutate Provider B confidential records.
- Every important action is attributable and auditable.

## 4. Schema Authority

[`schema.md`](./schema.md) is the authoritative v1 contract for the entire project.

### 4.1 Phase 1 schema rule

Phase 1 physically implements the complete MVP schema before feature development:

1. `001_foundation_and_identity.sql`
2. `002_simulation_ingestion_ledger.sql`
3. `003_quality_and_intelligence.sql`
4. `004_alerts_and_coordination.sql`
5. `005_validation_indexes_views.sql`
6. `006_security_immutability_rls.sql`

The schema phase includes tables, constraints, indexes, views, triggers, grants, RLS policies, reference seeds and schema verification tests. No placeholder migration is allowed in the Phase 1 exit gate.

### 4.2 Controlled changes later

The schema may change when implementation reveals a genuine need. Every change must:

- have a short decision record;
- use a new forward-only migration;
- update `schema.md`, API/OpenAPI contracts, fixtures and tests together;
- document compatibility and rollback impact;
- preserve provider separation, append-only evidence, safe language and prohibited-action guardrails;
- pass both clean-database and upgrade-path verification.

## 5. Solo Development Rules

1. Keep analytics, persistence/API and coordination/security as separate internal modules even though one person owns all of them.
2. Implement and test a producer before its consumer.
3. Preserve these seams:
   - normalized input → quality/analytics engine;
   - engine → `ResultEnvelope`;
   - persisted result → `AlertCandidate`;
   - candidate → immutable alert;
   - alert → mutable case.
4. Do not start a phase until its prerequisite gate passes.
5. At each phase exit, record the schema version, migration state, contract version and tested release identifier.
6. Fix current-phase blockers before adding breadth.
7. Stretch scope starts only after the complete integrated MVP gate passes.

## 6. Phase Overview

| Phase | Focus | Required result |
|---|---|---|
| 1 | Authoritative schema implementation | Complete clean-database migration chain, constraints, views and RLS |
| 2 | Application foundation and contracts | Runnable modular monolith, configuration, DB layer, errors, OpenAPI and seam contracts |
| 3 | Synthetic ecosystem, ingestion and ledger | Deterministic scenarios, fault injection, append-only observations and separated dashboard reads |
| 4 | Data quality and intelligence | Quality, confidence, liquidity and anomaly engines producing persisted explainable results |
| 5 | Alerts, cases and security | Candidate-to-alert routing, localization, workflow, notification, audit, auth and provider boundaries |
| 6 | Integrated API and thin UI | Complete Scenarios A–D through one runnable backend and minimal frontend |
| 7 | Validation, observability and safety | Numeric analytics/performance/reliability evidence and complete safety verification |
| 8 | Documentation and presentation | All required deliverables and rehearsed story-driven demo |
| 9 | Final QA and submission | Frozen tested build, verified permissions and confirmed submission |

---

## Phase 1 — Authoritative Schema Implementation

### Goal

Turn `schema.md` into a complete, tested PostgreSQL/Supabase schema before writing application features.

### Prerequisites

- Final review of `Problem_Statement.md`, `System-Design.md`, `schema.md` and `checklist.md`.
- PostgreSQL/Supabase development database credentials stored outside source control.
- Agreed naming, UUID, timestamp, decimal money and migration conventions.

### Work

#### 1. Freeze the logical contract

- Review every enum, table, relationship, optionality rule and unique constraint.
- Confirm shared-cash/provider-e-money XOR rules.
- Confirm synthetic-only fields and prohibited data.
- Confirm alert versus case separation.
- Confirm role/scope and provider-boundary model.
- Confirm validation/ground-truth/metric schema.
- Record any amendment before physical implementation.

#### 2. Implement migration 001 — foundation and identity

- Extensions and constrained enum/domain strategy.
- `areas`, `providers`, `outlets`, `outlet_provider_accounts`.
- `app_users`, `user_access_scopes`.
- Synthetic bKash/Nagad/Rocket and demo scope seeds.
- Area hierarchy and account/provider consistency constraints.

#### 3. Implement migration 002 — simulation, ingestion and ledger

- Scenario/run/fault tables.
- Ingestion batches/events.
- Transactions and cash/provider balance snapshots.
- Append-only protections.
- Provider/account/outlet consistency triggers.
- Conflicting snapshots allowed and preserved.

#### 4. Implement migration 003 — quality and intelligence

- Quality assessments/issues.
- Analytics runs.
- Liquidity projections/signals/quality links.
- Anomaly rules/flags/evidence/transaction links.
- Active near-identical-amount rule seed.
- Confidence, sample and reserve-type integrity constraints.

#### 5. Implement migration 004 — alerts and coordination

- Alerts and typed analytical-source links.
- Explanation templates/renders.
- Routing rules.
- Cases, assignments, status history, notes, reviews.
- Notifications and audit events.
- English plus one Bangla/Banglish demo template.

#### 6. Implement migration 005 — validation, indexes and views

- Validation runs, ground truth and metric results.
- Required indexes from `schema.md`.
- Latest cash/provider/quality/projection views.
- Outlet dashboard, case timeline and validation summary views.
- No blended monetary total.

#### 7. Implement migration 006 — security and immutability

- Database roles and minimum grants.
- RLS policies for provider/outlet/area access.
- Append-only ledger/evidence/audit protection.
- Alert immutability.
- Case transition/scope consistency checks.
- Audit mutation protection.

#### 8. Verify the schema

- Apply all migrations to an empty database.
- Re-run migrations and prove idempotent migration tracking.
- Test every critical constraint with valid and invalid rows.
- Test provider A/B RLS denial.
- Compile/query every required view.
- Produce a schema-only dump or metadata snapshot.
- Verify upgrade/change procedure with a small test migration if desired.

### Deliverables

- Six complete numbered migrations.
- Migration runner and checksum/history table.
- Reference/demo seed script.
- Constraint, trigger, view and RLS tests.
- Clean migration log and metadata/schema dump.
- Decision records for every deviation from `schema.md`.

### Exit gate

- A fresh database reaches the full MVP schema with one command.
- No required migration or object is a placeholder.
- All critical invariants and provider-boundary tests pass.
- Views return separated cash/provider structures.
- Application feature work may now begin.

---

## Phase 2 — Application Foundation and Contracts

### Goal

Create the runnable modular-monolith foundation and freeze the contracts connecting future modules.

### Prerequisite

Phase 1 schema gate passes on a fresh database.

### Work

- Create backend project structure and dependency manifest.
- Implement environment/config loading with `.env.example` containing placeholders only.
- Implement async database connection/session/transaction handling.
- Implement migration/seed commands.
- Create application factory, startup/shutdown and CORS for the thin frontend.
- Add request ID, structured logging and safe global error handling.
- Define authentication dependency interface without bypassing authorization.
- Create versioned Pydantic/domain contracts for:
  - normalized transaction/balance input;
  - quality assessment;
  - liquidity projection;
  - anomaly flag/evidence;
  - `ResultEnvelope`;
  - `AlertCandidate`;
  - validation metric payload;
  - dashboard, alert and case responses.
- Create fixture examples and contract tests.
- Generate OpenAPI from registered routes/stubs without claiming unimplemented behavior works.
- Create one documented command for tests, migrations, seed, server and OpenAPI generation.
- Create the frontend project shell only; defer feature UI.

### Deliverables

- Runnable backend skeleton connected to the Phase 1 database.
- Safe configuration/error/logging/transaction infrastructure.
- Frozen v1 seam contracts and fixtures.
- Test harness and CI-ready commands.
- Generated OpenAPI baseline.
- Minimal frontend scaffold.

### Exit gate

- Application boots and `/health` verifies database readiness.
- Migrations/seeds/tests run from documented commands.
- All contracts validate positive/negative fixtures.
- A `ResultEnvelope` can be transformed into a valid candidate fixture without case fields.
- No route bypasses the future auth dependency for confidential data.

---

## Phase 3 — Synthetic Ecosystem, Ingestion and Ledger

### Goal

Produce deterministic multi-provider data, ingest it safely and expose a trustworthy separated ledger/dashboard foundation.

### Prerequisite

Phase 2 application/contracts gate passes.

### Work

#### Synthetic scenarios

- Implement normal operation and Scenarios A–D with deterministic seeds.
- Generate one outlet, shared cash, three provider accounts, transactions and snapshots.
- Maintain tuning, held-out and demo dataset splits.
- Implement delay, missing feed/field, malformed payload and conflicting balance faults.

#### Ingestion and ledger

- Validate and persist ingestion batches/events.
- Normalize provider-specific mock shapes into one internal format without losing provider identity.
- Reject malformed events without updating ledger tables.
- Persist append-only transactions and snapshots.
- Implement deterministic run/reset/fault behavior and idempotency.
- Build latest cash/provider read repositories and preserve conflict candidates.

#### APIs

- Providers, areas, outlets and outlet detail.
- Scenario list, run start/status/reset and fault create/toggle.
- Batch ingestion.
- Dashboard, transactions and balance history.
- Initial current/history quality endpoints may return assessed foundation data.

#### Tests

- Determinism and replay.
- Provider/account/outlet consistency.
- Append-only behavior.
- Invalid ingestion rejection.
- No blended total.
- Conflicting snapshots coexist.

### Deliverables

- Deterministic generator and A–D fixtures.
- Ingestion/normalization/ledger services and repositories.
- Reference/simulation/ingestion/dashboard APIs.
- Seed/reset/fault commands.
- Foundation integration tests.

### Exit gate

- A clean run displays shared cash and three separate provider balances from persisted synthetic data.
- Same seed/config produces the same semantic dataset.
- Faults are reproducible.
- No rejected/malformed event updates the ledger.
- No API/view exposes a blended balance.

---

## Phase 4 — Data Quality and Intelligence

### Goal

Turn the ledger into explainable, confidence-aware liquidity and anomaly results.

### Prerequisite

Phase 3 provides stable normalized inputs, scenarios and ledger reads.

### Work

#### Data Quality & Confidence Engine

- Classify `fresh`, `stale`, `missing` and `conflicting` with defined precedence.
- Emit issue evidence, sample count, last source time and confidence modifier.
- Preserve last trusted value/time and conflicting candidates.
- Handle insufficient samples and malformed inputs.

#### Liquidity Forecasting Engine

- Forecast shared cash independently from each provider e-money reserve.
- Use transparent recent-window depletion/burn rate.
- Return no shortage for zero/negative depletion.
- Return non-actionable output for insufficient samples.
- Apply quality modifier, confidence level and widening bounds.
- Emit contributing signals.

#### Anomaly Detection Engine

- Implement near-identical-amount rule within one provider/outlet/window.
- Emit exact evidence references, counts, amount cluster, party count and window.
- Provide confidence, reason and plausible benign explanation.
- Retain suppressed evaluations with suppression reason under degraded data.
- Prevent suppressed evaluations from becoming anomaly candidates.

#### Persistence and APIs

- Persist analytics runs, quality results, projections, flags and evidence.
- Implement liquidity run/read and anomaly run/list/detail endpoints.
- Implement validated `ResultEnvelope` and `AlertCandidate` adapter.

#### Tests/evaluation preparation

- Zero/replenishing and threshold boundaries.
- Provider isolation.
- Known A/B positives and normal high-demand negatives.
- Scenario C confidence degradation/suppression.
- Decimal/timestamp/evidence round trip.

### Deliverables

- Quality, liquidity and anomaly engines.
- Persisted analytical results and evidence APIs.
- Result/candidate adapter.
- Scenario A/B/C expected outputs.
- Unit, boundary and integration tests.

### Exit gate

- Scenario A identifies the correct reserve, approximate shortage and confidence.
- Scenario B produces an evidence-backed unusual pattern with benign context.
- Scenario C lowers/unavailable confidence and suppresses risk alertability safely.
- Every analytical result is reproducible and explainable.

---

## Phase 5 — Alerts, Cases and Security

### Goal

Turn important analytical candidates into safe, localized and provider-scoped human workflows.

### Prerequisite

Phase 4 produces persisted results and valid candidates.

### Work

#### Authentication and scopes

- Seed demo agent, field/area, provider ops, risk analyst and management users.
- Implement demo login, current user and locale preference.
- Enforce provider/outlet/area authorization in application code and RLS.
- Return the same safe not-found response for missing and forbidden confidential IDs.

#### Alerts and explanations

- Validate candidate source/scope/alertability.
- Deduplicate active alerts.
- Persist typed analytical source links without copying/recalculating evidence.
- Freeze analytical alert content after publication.
- Render/save EN and Bangla/Banglish situation, evidence, uncertainty, next step and benign context.

#### Routing and cases

- Resolve provider+area → provider → area → fallback routing.
- Open a case only when required.
- Store recipient, current owner, safe next step and current status.
- Implement assignment/reassignment, acknowledge, escalate, notes, review and resolve.
- Enforce legal transition matrix and resolution requirements.
- Add optimistic version checks and idempotency for mutations.

#### Notifications and audit

- Queue/deliver/read in-app notifications.
- Write audit events atomically with mutations.
- Build case timeline and audit endpoints.

#### APIs and thin workflow controls

- Auth/profile endpoints.
- Alert list/detail/explanations/case opening.
- Case list/detail/timeline and action endpoints.
- Notification list/read and audit event endpoints.
- Minimal workflow controls for testing; complete UI waits for Phase 6.

### Deliverables

- Complete auth/alert/case/notification/audit API group.
- EN and localized explanation templates/renders.
- Routing and legal case lifecycle.
- Provider-boundary, idempotency, concurrency and audit tests.
- Scenario D API script.

### Exit gate

- Scenario D completes without direct database edits.
- Provider A cannot enumerate/read/mutate Provider B confidential records.
- Duplicate/stale mutations fail safely without duplicate history.
- Alert evidence remains immutable while case workflow evolves.
- Complete timeline/audit history is visible.

---

## Phase 6 — Integrated API and Thin UI

### Goal

Compose the complete MVP into one runnable release candidate and a minimal clear demonstration surface.

### Prerequisites

- Phase 3 data foundation passes.
- Phase 4 analytics gate passes.
- Phase 5 workflow/security gate passes.

### Work

- Register all routers through one application composition path.
- Apply auth dependency to all confidential endpoints.
- Verify startup/shutdown, migrations, seed/reset, OpenAPI and logs.
- Build one thin responsive frontend containing:
  - demo login/role switch;
  - shared-cash and separate provider cards;
  - data-health and confidence states;
  - forecast and contributing signals;
  - anomaly evidence and benign context;
  - scenario/fault controls;
  - alert explanation locale toggle;
  - case assignment/acknowledge/escalate/note/resolve controls;
  - notification and case timeline/audit display.
- Implement loading, empty, error and forbidden states.
- Run deterministic Scenarios A–D end to end.
- Verify idempotency, concurrency, alert immutability, provider isolation and safe language.

### Deliverables

- One-command runnable backend and frontend.
- Complete A–D demo path.
- Frozen OpenAPI and release candidate.
- End-to-end regression suite and backup captures.

### MVP freeze gate

- Shared cash plus three provider balances, never blended.
- Shortage timing and confidence for every projection.
- One evidence-backed anomaly with benign context.
- Missing/stale/conflicting safe fallback and suppression.
- Routed case with owner, next step, full lifecycle and audit.
- EN and Bangla/Banglish explanation.
- Provider-boundary enforcement.
- No unsafe language/action.

If any item fails, do not begin stretch work. Repair the MVP path.

---

## Phase 7 — Validation, Observability and Safety

### Goal

Produce credible measured evidence and eliminate high-risk failures on the frozen MVP.

### Prerequisite

Phase 6 release candidate and A–D regression pass.

### Work

#### Analytics evidence

- Freeze held-out data before evaluation.
- Measure anomaly precision, recall and false-positive rate.
- Measure forecast error or shortage detection lead time.
- State sample sizes, seeds, configuration, versions and limitations.

#### Performance/reliability evidence

- Measure average and p95 API latency at documented volume.
- Measure data-quality incident handling rate.
- Measure alert explanation coverage.
- Measure legal transition, notification and audit completeness.
- Measure provider-denial, idempotency and concurrency correctness.

#### Observability

- Structured request/error/audit logs with request IDs.
- `/health`, `/metrics` and validation-result endpoints.
- Data-quality event counts and failure evidence.

#### Safety/security

- Scan for secrets, real identities and unsafe action endpoints.
- Scan user-visible text for definitive fraud language.
- Re-run provider A/B RLS and application authorization tests.
- Verify append-only and immutable protections.

### Deliverables

- At least three numeric metrics with method, sample size and limitation.
- Raw/summary validation artifacts.
- Performance and reliability report.
- Security/safety scan report.
- Signed-off release candidate identifier.

### Exit gate

- Evidence matches the exact frozen build.
- Bad data never produces misleading confidence.
- All high-impact alerts contain evidence and uncertainty.
- No critical privacy, authorization, audit or responsible-design issue remains.

---

## Phase 8 — Documentation and Presentation

### Goal

Complete every required deliverable and prepare a reliable story-driven demo.

### Prerequisite

Phase 7 evidence is signed off.

### Documentation work

- Root README with problem, users, features and exact setup/run/test/demo commands.
- Backend/frontend environment and deployment instructions.
- Current OpenAPI and endpoint guide.
- Architecture diagram with provider boundaries and coordination flow.
- Data/simulation note: seeds, scenarios, faults, assumptions and limitations.
- Analytics/validation note: methods, splits, metrics and false-positive risk.
- Responsible-design note: privacy, human review, provider separation and prohibited actions.
- Screenshots/backup responses from the frozen build.
- Limitations and next steps without production/regulatory claims.

### Presentation flow

1. Problem: shared cash, separate provider balances and fragmented coordination.
2. Scenario A: hidden shortage with timing/confidence.
3. Scenario B: unusual repeated amounts with evidence and benign context.
4. Scenario C: delayed/conflicting data lowers confidence and suppresses alerts.
5. Scenario D: route, assign, acknowledge, escalate, note, resolve and audit.
6. Architecture and provider boundaries.
7. Metrics and validation evidence.
8. Responsible design and limitations.

### Rehearsal work

- Run twice from a clean deterministic reset.
- Time the full presentation.
- Prepare backup screenshots/responses for every critical step.
- Prepare concise answers on forecast method, anomaly reason, false positives, bad data, provider boundaries and prohibited actions.
- Freeze slides, spoken wording and backup media after the final successful rehearsal.

### Deliverables

- Working prototype and source repository.
- README/setup/OpenAPI.
- Architecture diagram.
- Data/simulation note.
- Validation evidence.
- Responsible-design note.
- Final presentation and backup.

### Exit gate

- A reviewer can reproduce the prototype from documentation.
- All seven required deliverables exist and match implementation.
- The solo presentation completes with buffer and fallback.

---

## Phase 9 — Final QA and Submission

### Goal

Protect the completed submission from last-minute regression.

### Prerequisite

Phase 8 documentation and rehearsal gate passes.

### Work

- Run the critical backend, frontend, migration, fixture and E2E checks.
- Run exact deterministic demo once.
- Verify metrics and displayed values against signed-off evidence.
- Verify repository/deployment/presentation permissions from a non-owner view.
- Run final secret, real-data, unsafe-language and prohibited-action scan.
- Confirm README, `.env.example`, migrations, seeds, sample data, OpenAPI, diagrams, notes, evidence and slides are included.
- Submit and confirm receipt/link.
- Preserve the tested local build and backup media unchanged.

### May fix

Only startup, incorrect mandatory output, safety/security, missing deliverable, access or submission blockers. Do not refactor, retune, change schema casually or add features.

### Exit gate

- Submission receipt/link confirmed.
- Repository and presentation permissions work.
- Final checklist is complete or any omission is explicitly disclosed.

## 7. Milestone Control Board

| Gate | Non-negotiable milestone | If missed |
|---|---|---|
| Schema gate | Complete migrations, views, constraints, seeds and RLS on a fresh database | Do not write feature services; repair schema |
| Foundation gate | Runnable app, DB, errors, logging, OpenAPI and seam contracts | Do not build domain modules; repair foundation |
| Ledger gate | Deterministic synthetic data and separated persisted dashboard | Cut filters/UI; preserve three providers and append-only ledger |
| Intelligence gate | Quality + forecast + evidence-backed anomaly + suppression | Keep one transparent forecast and anomaly rule |
| Coordination gate | Auth, localized alert, routed lifecycle, notification, audit and RBAC/RLS | Cut review/routing breadth; preserve full mandatory lifecycle/security |
| MVP gate | Complete A–D path through thin UI | Freeze scope; repair mandatory flow only |
| Evidence gate | Three or more metrics and safety/security proof | Stop features; measure stable build |
| Documentation gate | Seven required deliverables and rehearsed demo | Shorten prose; preserve reproducibility/evidence |
| Submission gate | Tested frozen build submitted and accessible | Submit last stable build, not experimental changes |

## 8. Requirement-to-Phase Traceability

| Requirement | Primary phase | Verification |
|---|---|---|
| Professional authoritative schema | 1 | Clean migrations, constraints, views, RLS and schema tests |
| Shared cash + separate provider balances | 3 | Dashboard/ledger tests; no blended total |
| Shortage timing + confidence | 4 | Scenario A and forecast tests |
| Unusual activity + evidence/benign context | 4 | Scenario B and anomaly evidence tests |
| Missing/stale/conflicting fallback | 4 | Scenario C and suppression tests |
| Recipient, owner, next step and lifecycle | 5 | Scenario D API workflow |
| EN + Bangla/Banglish explanation | 5 | Render snapshot coverage |
| Provider-boundary RBAC/RLS | 1 and 5 | Database and API provider A/B denial tests |
| Auditability | 5 | Timeline/audit completeness |
| Integrated prototype | 6 | A–D E2E regression |
| Three or more measured metrics | 7 | Metrics/validation endpoints and report |
| Required documents/presentation | 8 | Deliverable audit and rehearsal |
| Safe final submission | 9 | Final checklist and receipt |

## 9. Definition of Success

The project succeeds when it demonstrates one connected, reproducible and safe chain:

> Authoritative schema → separate provider data and shared cash → visible data quality → forward liquidity insight → evidence-backed unusual activity with benign context → immutable localized alert → provider-aware human case → traceable resolution → measured evidence.

Completeness, correctness, explainability and provider boundaries take priority over feature count or visual polish.

## 10. Endpoint Delivery Map

### Phase 2 — foundation

- `GET /health`

### Phase 3 — reference, simulation, ingestion and ledger

- `GET /api/v1/providers`
- `GET /api/v1/areas`
- `GET /api/v1/outlets`
- `GET /api/v1/outlets/{outletId}`
- `GET /api/v1/outlets/{outletId}/dashboard`
- `GET /api/v1/outlets/{outletId}/transactions`
- `GET /api/v1/outlets/{outletId}/balances/history`
- `GET /api/v1/simulations/scenarios`
- `POST /api/v1/simulations/runs`
- `GET /api/v1/simulations/runs/{runId}`
- `POST /api/v1/simulations/runs/{runId}/reset`
- `POST /api/v1/simulations/runs/{runId}/faults`
- `PATCH /api/v1/simulations/runs/{runId}/faults/{faultId}`
- `POST /api/v1/ingestion/batches`
- `GET /api/v1/outlets/{outletId}/data-quality`
- `GET /api/v1/outlets/{outletId}/data-quality/history`

### Phase 4 — intelligence

- `GET /api/v1/outlets/{outletId}/liquidity-projections`
- `POST /api/v1/internal/analytics/liquidity/run`
- `GET /api/v1/outlets/{outletId}/anomaly-flags`
- `GET /api/v1/anomaly-flags/{flagId}`
- `POST /api/v1/internal/analytics/anomalies/run`

### Phase 5 — auth, alerts and coordination

- `POST /api/v1/auth/demo-login`
- `GET /api/v1/me`
- `PATCH /api/v1/me/preferences`
- `GET /api/v1/alerts`
- `GET /api/v1/alerts/{alertId}`
- `GET /api/v1/alerts/{alertId}/explanations`
- `POST /api/v1/alerts/{alertId}/cases`
- `GET /api/v1/cases`
- `GET /api/v1/cases/{caseId}`
- `GET /api/v1/cases/{caseId}/timeline`
- `POST /api/v1/cases/{caseId}/assignments`
- `POST /api/v1/cases/{caseId}/acknowledge`
- `POST /api/v1/cases/{caseId}/escalate`
- `POST /api/v1/cases/{caseId}/resolve`
- `POST /api/v1/cases/{caseId}/notes`
- `POST /api/v1/cases/{caseId}/review`
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{notificationId}/read`
- `GET /api/v1/cases/{caseId}/audit-events`

### Phase 7 — validation evidence

- `GET /metrics`
- `GET /api/v1/validation/results`

### Stretch after the complete Phase 6 MVP gate

- `POST /api/v1/outlets/{outletId}/what-if-runs`
- `GET /api/v1/what-if-runs/{whatIfRunId}`
- `GET /api/v1/outlets/{outletId}/relationships`
- `GET /api/v1/outlets/{outletId}/nearby-support-options`
- `POST /api/v1/cases/{caseId}/support-requests`
