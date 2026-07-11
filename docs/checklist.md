# Project Progress Checklist
### Codex Community Hackathon — bKash presents SUST CSE Carnival 2026

Use this checklist to track development progress against `docs/16-hour-hackathon-phase-distribution.md`. Check a parent only after the capability works end to end on the frozen build. Re-verify items against code/tests before marking complete — do not assume from file presence alone.

**Last verified:** 2026-07-11 · **Current focus:** Phase 6 MVP freeze (backend E2E green; Playwright selector fix pending) → Phase 7 validation evidence.

| Phase | Status | Evidence |
|-------|--------|----------|
| 1 Schema | ✅ Complete | `docs/verification/` (53 schema tests) |
| 2 Foundation | ✅ Complete | `backend/app/`, contracts, OpenAPI, frontend scaffold |
| 3 Ingestion/Ledger | ✅ Complete | `tests/phase3/` (determinism, no-blend, faults) |
| 4 Intelligence | ✅ Complete | `tests/analytics/`, Scenario A/B/C API tests |
| 5 Alerts/Cases | ✅ Complete | `tests/phase5/`, Scenario D lifecycle |
| 6 Integrated UI | 🟡 In progress | `tests/phase6/` (10/10); thin UI + `docs/demo-snapshots/`; Playwright `e2e/demo.spec.ts` failing on scenario label selector |
| 7–9 | ⬜ Not started | `/metrics`, validation evidence, presentation deliverables |

**Backend test suite:** `208 passed` (`pytest tests -q`, local PostgreSQL).

---

## 0. Zero-State and Schema-First Baseline

### 0.1 Planning state

- [x] Authoritative professional schema/API contract completed in `docs/schema.md`.
- [x] Solo schema-first phase plan completed in `docs/16-hour-hackathon-phase-distribution.md`.
- [x] Development environment and database target selected. — Local PostgreSQL 17 (docker-compose port 5433); Supabase-compatible migration chain; FastAPI + Next.js.
- [x] Repository conventions, command names and contract versioning agreed. — `backend/Makefile` (`migrate`, `seed`, `test`, `server`, `openapi`); frozen contract `docs/openapi/openapi.v1.json`.

### 0.2 Phase 1 — physical schema implementation

- [x] Migration 001: foundation and identity. — `backend/migrations/001_foundation_and_identity.sql`
- [x] Migration 002: simulation, ingestion and ledger. — `backend/migrations/002_simulation_ingestion_ledger.sql`
- [x] Migration 003: data quality and intelligence. — `backend/migrations/003_quality_and_intelligence.sql`
- [x] Migration 004: alerts and coordination. — `backend/migrations/004_alerts_and_coordination.sql`
- [x] Migration 005: validation, indexes and read views. — `backend/migrations/005_validation_indexes_views.sql`
- [x] Migration 006: security, immutability, grants and RLS. — `backend/migrations/006_security_immutability_rls.sql`
- [x] Reference/demo seeds implemented. — `backend/seeds/reference_seed.sql` (deterministic, idempotent)
- [x] Migration runner/checksum history implemented. — `backend/migrations/run_migrations.py`; `schema_migrations` table; see `docs/verification/migration_checksums.txt`
- [x] Clean empty-database migration passes. — `docs/verification/migration_log.txt` (42 tables, 7 views, 75 indexes, 30 policies)
- [x] Re-run/idempotency check passes. — `docs/verification/migration_log.txt` ("nothing to apply"); `test_migration_chain.py::test_reapply_is_idempotent`
- [x] Constraint, trigger, view and provider A/B RLS tests pass. — `docs/verification/test_report.txt` (53 passed); `rls_provider_ab_report.txt`
- [x] Schema dump/metadata snapshot and migration log saved. — `docs/verification/schema.sql`, `migration_log.txt`
- [x] Deviations recorded as decision notes. — `docs/adr/0001`–`0005`

> Verified on local PostgreSQL 17.5 with the Supabase-compatible chain. Supabase
> deployment verification is **blocked pending project credentials** in
> `backend/.env` (see `backend/README.md`); it is not claimed until run.

### 0.3 Solo operating rules

- [x] Preserve module boundaries: normalized input → engines → result → candidate → alert → case.
- [x] Complete/test each producer before its consumer.
- [x] Apply only forward numbered migrations; record every later schema change.
- [x] Keep all 43 MVP endpoints under one owner; defer 5 stretch endpoints until the complete MVP gate.
- [ ] Record schema/contract/release versions at each phase boundary.
- [x] Cut optional breadth/UI polish before correctness, evidence, provider boundaries or safe fallback.

---

## A. Functional Requirements

### A.1 Mandatory

- [x] Show shared physical cash and separate balances for each provider
  - [x] *Design data model: shared cash pool + per-provider e-money balance fields (`schema.md`)*
  - [x] *Implement the designed tables, constraints and views through Phase 1 migrations* — migrations `001`–`006`; separation enforced by `lp_reserve_xor`, no-`provider_id` on `cash_balance_snapshots`, `v_outlet_dashboard` (no blended total). Evidence: `test_reserve_invariants.py`, `docs/verification/schema.sql`
  - [x] *Build unified dashboard view combining cash + all provider balances* — `GET /api/v1/outlets/{id}/dashboard` + `OutletDashboard.tsx`; four separate reserve cards, explicit no-blend copy. Evidence: `tests/phase3/test_no_blend.py`, `tests/phase6/test_e2e_scenarios.py::test_scenario_a_*`
- [x] Show which provider or shared cash reserve may face a shortage and approximately when
  - [x] *Implement demand/burn-rate projection logic (e.g., time-series or rate-based forecast)* — `services/analytics/liquidity_engine.py`; rolling burn-rate window with quality modifier.
  - [x] *Display estimated time-to-shortage per provider and for shared cash* — `LiquidityPanel.tsx` + `GET /api/v1/outlets/{id}/liquidity-projections`; Scenario A shows shared-cash shortage without false provider e-money shortage.
- [x] Detect at least one type of unusual activity and show why it was flagged
  - [x] *Choose at least one anomaly pattern (velocity, near-identical amounts, splitting, circular activity, etc.)* — `near_identical_amounts` within one provider/outlet/window.
  - [x] *Implement detection logic (rule-based, statistical, or ML)* — `services/analytics/anomaly_engine.py`.
  - [x] *Attach human-readable reason/evidence to each flag* — structured evidence items (count, amount cluster, parties, window) + `AnomalyPanel.tsx`.
- [x] Use careful language such as "unusual" or "requires review"; do not declare fraud
  - [x] *Review all alert copy/UI text to remove definitive fraud language* — contract fixture `alert_candidate_unsafe_language.json`; `tests/phase6/test_e2e_scenarios.py::test_no_definitive_fraud_language_in_user_visible_text`.
- [x] For at least one important alert, show who receives it, who owns it, the recommended next step, and the final status
  - [x] *Build alert routing logic (who is notified)* — routing precedence in `services/coordination/routing.py`; notifications on publish.
  - [x] *Build case ownership / assignment mechanism* — `POST /api/v1/cases/{id}/assignments`.
  - [x] *Add recommended next-step field* — persisted on case open; visible in `CasePanel.tsx`.
  - [x] *Add status tracking (open / acknowledged / escalated / resolved)* — full lifecycle in Scenario D; `tests/phase5/test_scenario_d.py`, `tests/phase6/test_e2e_scenarios.py::test_scenario_d_*`.
- [x] Show lower confidence or a safe fallback when data is missing, late, or conflicting
  - [x] *Implement data quality checks (missing, delayed, conflicting feeds)* — `services/analytics/quality_engine.py`; fault injection in simulation layer.
  - [x] *Implement confidence scoring or fallback state in UI* — data-health badges on dashboard; suppressed evaluations marked non-alertable in `AnomalyPanel.tsx`; Scenario C tests.
- [x] Use AI, APIs, analytics, or data processing as a meaningful part of the product
  - [x] *Implement non-trivial analytics components: confidence, liquidity forecast and anomaly rule modules with tests* — `tests/analytics/` (quality, liquidity, anomaly engines + API).
  - [ ] *Document how it's used and why it's meaningful (not decorative)* — deferred to Phase 8 responsible-design / presentation notes.

### A.2 Recommended

- [ ] Allow users to filter or prioritize by provider, agent, area, or time
- [x] Provide evidence and a simple history for important alerts
- [x] Offer clear Bengali, Banglish, or English explanations
- [x] Show at least one simple Bengali or Banglish alert with situation, evidence, uncertainty, and a safe next step
- [x] Support provider-specific escalation, case notes, alert history, and coordination while keeping provider boundaries clear

### A.3 Optional

- [x] Support simulations, peer comparison, relationship views, or cross-provider patterns — scenario runner + fault controls (`ScenarioPanel.tsx`); stretch relationship/nearby-support endpoints not built.
- [ ] Independently defined additional fraud/anomaly-detection scenario(s)
  - [ ] *Document chosen pattern, detection approach, and evidence*
  - [x] *Confirm scenario uses simulated/anonymized data only*
  - [x] *Confirm anomaly score is NOT presented as proof of fraud*

---

## B. Non-Functional Requirements

- [x] **Usability** — Provider distinctions, shared cash exposure, and risk signals are easy to understand — thin demo UI with labelled reserve cards and advisory copy.
- [ ] **Performance** — Core analytical and dashboard interactions are responsive under demonstrated data volume
  - [ ] *Benchmark response times at target data volume* — Phase 7.
- [x] **Reliability** — Provider data failures/inconsistencies do not silently produce confident conclusions
  - [x] *Test with intentionally broken/missing/delayed provider data* — Scenario C + fault injection tests.
- [x] **Explainability** — Every high-impact alert exposes reason, relevant evidence, and uncertainty
- [x] **Security and privacy** — Synthetic identifiers only; no real credentials, customer identities, or sensitive account data
  - [x] *Audit dataset for any real/sensitive data leakage* — synthetic generator + demo identities only.
- [x] **Fairness and responsible AI** — No unsupported profiling; human review demonstrated for risk judgments — case review step required before resolve.
- [x] **Auditability** — Alerts, ownership changes, acknowledgements, escalations, evidence, and resolutions are traceable
  - [x] *Implement audit log / activity trail* — `case_audit_events` + timeline/audit API + `CasePanel.tsx`.
- [x] **Interoperability** — Multiple providers represented without assuming real technical integration

---

## C. Scope & Guardrail Compliance (self-check)

- [x] At least two logically separate financial service providers simulated — three: bKash, Nagad, Rocket.
- [x] No real interoperability, settlement, or conversion between provider wallets implemented
- [x] No access to production APIs, real customer identities, real balances, or real accounts
- [x] No automatic blocking, accusation, disciplinary action, or final fraud determination
- [x] No unauthorized cash movement, wallet refill, transfer, recovery, or reversal
- [x] No collection of PINs, OTPs, passwords, or private authentication data
- [x] No claims of regulatory approval or production fraud-detection readiness
- [x] All risk/anomaly signals framed as advisory, not final decisions

---

## D. Data & Simulation

- [x] Synthetic / mock / anonymized dataset created (agent & provider IDs, area, time, transaction type, amount, status, balances, event flags, case status) — `services/synthetic/generator.py`, scenarios A–D.
- [ ] Data generation method documented (how it was created) — partial: `docs/Prototype-Simulation-Walkthrough.md`; formal data & simulation note deferred to Phase 8.
- [ ] Assumptions documented
- [ ] Known limitations documented
- [x] Risk interpretation rule documented (anomaly ≠ fraud; false-positive risk; human review requirement) — enforced in schema constraints, alert copy, and tests.

---

## E. Required Deliverables

- [x] **Working prototype**
  - [x] *Live flow: multi-provider balances visible* — `OutletDashboard.tsx`.
  - [x] *Live flow: at least one liquidity or anomaly alert triggers* — Scenario A liquidity + Scenario B anomaly publish path.
  - [x] *Live flow: at least one case is coordinated/escalated end-to-end* — Scenario D via API (`tests/phase6`) and `CasePanel.tsx`.
- [ ] **Source repository**
  - [ ] *Source code pushed*
  - [x] *README written* — `backend/README.md` (frontend README minimal).
  - [x] *Setup / installation steps documented* — `backend/README.md` (`make db-up && make migrate && make seed && make server`).
  - [x] *Environment variable examples (.env.example) included* — `backend/.env.example`.
  - [x] *Sample data included* — `backend/seeds/reference_seed.sql` + deterministic scenario generator.
- [ ] **Architecture diagram**
  - [x] *Main interfaces shown* — `docs/diagram.md` (Mermaid data-flow + component views).
  - [x] *Backend components shown*
  - [x] *Data flow shown*
  - [x] *Analytics/AI services shown*
  - [ ] *Monitoring shown* — `/metrics` not implemented (Phase 7).
  - [x] *Provider boundaries shown*
  - [x] *Alert coordination flow shown*
- [ ] **Data and simulation note** (write-up of how synthetic data/scenarios were created, assumptions, limitations)
- [ ] **Validation evidence** — at least 3 measured metrics (analytics, performance, and/or reliability) — Phase 7.
  - [ ] *Metric 1 chosen and measured: __________*
  - [ ] *Metric 2 chosen and measured: __________*
  - [ ] *Metric 3 chosen and measured: __________*
- [ ] **Responsible-design note** (privacy, human review, false positives, advisory boundaries, what the prototype intentionally does NOT do)
- [ ] **Final presentation**
  - [ ] *Problem statement covered*
  - [ ] *Users/stakeholders covered*
  - [ ] *Story-driven live demo prepared* — demo snapshots captured in `docs/demo-snapshots/`; Playwright suite needs selector fix.
  - [ ] *Architecture explained*
  - [ ] *Metrics presented*
  - [ ] *Coordination flow demonstrated*
  - [ ] *Risks & limitations discussed*
  - [ ] *Next steps outlined*

---

## F. Optional Supporting Materials

- [ ] Short demonstration video
- [ ] Alert case study or review log
- [ ] Load-test, profiling, or trace outputs
- [ ] Additional multi-provider scenarios or relationship visualizations

---

## G. Demonstration Scenario Coverage (from Section 11)

- [x] Scenario A — Hidden shared-cash shortage driven by provider cash-out demand — `tests/phase6/test_e2e_scenarios.py::test_scenario_a_*`; snapshot `docs/demo-snapshots/dashboard_a.json`.
- [x] Scenario B — Liquidity pressure with unusual activity — `test_scenario_b_*`; snapshots `anomaly_flags_b.json`, `publish_b.json`.
- [x] Scenario C — Cross-provider or data inconsistency — `test_scenario_c_*`; snapshots `anomaly_run_c.json`, `liquidity_run_c.json`.
- [x] Scenario D — Coordinated response and closure — `test_scenario_d_*`; snapshots `case_*.json`, `case_timeline.json`, `case_audit.json`.

---

## H. System Design Feature List

Features grouped by module from the System Design document. Tags: **[M]** Mandatory, **[R]** Recommended, **[O]** Optional, **[E]** Engineering-depth.

### H.1 Unified Visibility

- [x] **[M]** Combined agent view: shared cash + each provider's balance, clearly separated (never summed into one blended figure)
- [ ] **[R]** Filter/prioritize by provider, agent, area, or time
- [ ] **[E]** Multi-agent overview for Operations/Management

### H.2 Liquidity Intelligence

- [x] **[M]** Per-provider and shared-cash shortage projection with estimated time window
- [x] **[M]** Confidence indicator on every projection
- [x] **[R]** Contributing-signal breakdown (why the projection says what it says)
- [ ] **[O]** What-if simulation (e.g., "what if cash-out demand doubles for the next hour") — stretch endpoint.

### H.3 Anomaly & Risk Detection

- [x] **[M]** At least one fully implemented anomaly pattern with evidence trail
- [x] **[M]** Careful, non-accusatory language throughout ("unusual," "requires review")
- [x] **[R]** Evidence + short history attached to each anomaly alert
- [x] **[E]** Plausible-benign-explanation field alongside every anomaly flag
- [ ] **[O]** Second/third anomaly pattern (e.g., transaction splitting, circular activity) if time allows
- [ ] **[O]** Cross-provider relationship view using simulated identifiers

### H.4 Coordination & Case Management

- [x] **[M]** For each important alert: assigned receiver, owner, recommended next step, current status
- [x] **[R]** Case notes and alert history, provider-boundary-respecting
- [x] **[E]** Full case lifecycle (open → acknowledged → escalated → resolved) with timestamps
- [x] **[E]** Routing rules aligned to the agent → field officer → area manager → central ops hierarchy
- [ ] **[O]** Nearby-agent support discovery (e.g., "Agent X 400m away has surplus cash")

### H.5 Data Quality & Trust

- [x] **[M]** Confidence/fallback state shown when data is missing, late, or conflicting
- [x] **[E]** Configurable fault injection for live demo of Scenario C
- [x] **[E]** Visible "data health" indicator per provider feed

### H.6 Explainability & Localization

- [x] **[R]** English explanations for every alert
- [x] **[R]** At least one Bengali/Banglish alert with situation, evidence, uncertainty, and next step
- [x] **[E]** Consistent multi-language rendering from one structured alert object (no drift between languages)

### H.7 Security, Privacy & Responsible Design

- [x] **[M]** Synthetic identifiers only; no real credentials or account data anywhere in the system
- [x] **[M]** No automatic blocking, accusation, or financial action anywhere in the codebase
- [x] **[E]** Role-based access control enforcing provider data boundaries — app auth + RLS; `tests/phase5/test_authorization.py`, `tests/phase6/test_provider_isolation_*`.
- [ ] **[E]** "Responsible-design note" content generated directly from documented guardrails, not written after the fact — Phase 8.

### H.8 Observability & Validation

- [x] **[M]** Analytics/AI meaningfully embedded (liquidity forecasting + anomaly detection, not decorative)
- [ ] **[E]** `/metrics` endpoint or dashboard panel showing: forecast error on held-out simulated data, shortage detection lead time, anomaly precision/recall against injected test cases, false-positive rate, alert explanation coverage, API latency, and data-quality incident counts — Phase 7.
- [x] **[E]** Structured audit log covering every ownership change, acknowledgement, escalation, and resolution

### H.9 Presentation-Ready Artifacts

- [x] **[M]** Architecture diagram (System Design, Section 1) — `docs/diagram.md`.
- [ ] **[M]** Data & simulation note (how synthetic data/scenarios were generated)
- [ ] **[M]** Responsible-design note (derived from H.7 guardrails)
- [ ] **[R]** Short demo video walking through Scenarios A–D

---

## I. Solo Endpoint Completion

An endpoint group is complete only when routes are registered, runtime behavior is persistence-backed, authorization is enforced, tests pass, OpenAPI matches and the demo can exercise the critical path.

### I.1 Data and intelligence APIs — 24 MVP

- [x] Reference/outlet endpoints complete (4): providers, areas, outlet list and outlet detail.
- [x] Dashboard/ledger endpoints complete (3): dashboard, transactions and balance history.
- [x] Simulation endpoints complete (6): scenario list, run start/status/reset and fault create/toggle.
- [x] Ingestion/data-quality endpoints complete (3): batch ingestion and quality current/history.
- [x] Liquidity endpoints complete (2): run and projection read.
- [x] Anomaly endpoints complete (3): run, list and evidence detail.
- [ ] Operations/evidence endpoints complete (3): `/health`, `/metrics`, validation results. — `/health` ✅; `/metrics` not implemented (Phase 7); `/api/v1/validation/results` stub only (`stubs.py`).

### I.2 Coordination and security APIs — 19 MVP

- [x] Auth/profile endpoints complete (3): demo login, `/me`, locale preference.
- [x] Alert endpoints complete (4): list, detail, explanations and case opening.
- [x] Case endpoints complete (9): list, detail, timeline, assignment, acknowledge, escalate, resolve, notes and review.
- [x] Notification/audit endpoints complete (3): notification list/read and case audit events.

### I.3 Stretch endpoints — 5, complete MVP gate required

- [ ] What-if run create/read.
- [ ] Synthetic relationship insight.
- [ ] Nearby support options.
- [ ] Approved-process support request.

## J. Solo Phase Gates — Dependency-Based, No Time Boxes

- [x] **Phase 1 — Authoritative schema:** all six migrations, constraints, indexes, views, seeds, grants and RLS pass on a fresh database.
- [x] **Phase 2 — Application foundation:** runnable backend/DB/config/errors/logging/OpenAPI/contracts/tests and frontend scaffold.
- [x] **Phase 3 — Synthetic ingestion and ledger:** deterministic A–D data, faults, append-only ledger and separated dashboard reads.
- [x] **Phase 4 — Data quality and intelligence:** quality/confidence, forecast, anomaly evidence, suppression, persistence and analytics APIs.
- [x] **Phase 5 — Alerts, cases and security:** auth, localized immutable alerts, routing, lifecycle, notifications, audit, idempotency/concurrency and provider RBAC/RLS.
- [ ] **Phase 6 — Integrated API and thin UI:** one release candidate passes complete Scenarios A–D; MVP frozen. — Backend regression `tests/phase6/` (10/10) ✅; thin UI panels ✅; demo snapshots ✅; Playwright E2E needs scenario-title selector fix; formal MVP freeze sign-off pending.
- [ ] **Phase 7 — Validation/observability/safety:** at least three numeric metrics plus safety/security evidence signed off.
- [ ] **Phase 8 — Documentation/presentation:** all seven deliverables match implementation and two clean rehearsals pass.
- [ ] **Phase 9 — Final QA/submission:** critical checks pass and submission receipt/permissions are confirmed.

### J.1 Phase 6 MVP freeze gate (must all pass before stretch work)

- [x] Shared cash plus three provider balances displayed, never blended
- [x] Shortage timing and confidence shown for every actionable projection
- [x] At least one evidence-backed anomaly with benign context visible
- [x] Missing/stale/conflicting data produces safe fallback and suppression (Scenario C)
- [x] Routed case with owner, next step, full lifecycle, and complete audit trail (Scenario D)
- [x] English and Bangla/Banglish explanation rendering works
- [x] Provider-boundary enforcement holds in UI and API
- [x] No unsafe language or prohibited financial/punitive actions anywhere

## K. Final Submission Checklist (from problem statement Section 16)

- [x] At least two provider contexts represented distinctly
- [x] Shared cash and provider-specific balances demonstrated
- [x] Forward-looking liquidity insight demonstrated
- [x] At least one anomaly category demonstrated with evidence
- [x] Human-review and careful risk language included
- [x] At least one alert demonstrates routing, ownership, acknowledgement or escalation, and a visible resolution status
- [ ] Repository, data, README, and architecture complete — push + formal docs pending Phase 8.
- [ ] At least three metrics measured and explained — Phase 7.
- [x] Failure, uncertainty, and false-positive considerations shown — Scenario C suppression + benign context.
- [ ] Safety, privacy, boundaries, and limitations stated — responsible-design note pending Phase 8.
- [ ] Final presentation ready
