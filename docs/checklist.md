# Project Progress Checklist
### Codex Community Hackathon — bKash presents SUST CSE Carnival 2026

Use this checklist to track development progress against `docs/16-hour-hackathon-phase-distribution.md`. Check a parent only after the capability works end to end on the frozen build. Re-verify items against code/tests before marking complete — do not assume from file presence alone.

**Last verified:** 2026-07-11 · **Current focus:** Phase 7 complete (held-out validation evidence, `/metrics` + `/validation/results`, safety scans) → Phase 8 documentation/presentation.

| Phase | Status | Evidence |
|-------|--------|----------|
| 1 Schema | ✅ Complete | `docs/verification/` (53 schema tests) |
| 2 Foundation | ✅ Complete | `backend/app/`, contracts, OpenAPI, frontend scaffold |
| 3 Ingestion/Ledger | ✅ Complete | `tests/phase3/` (determinism, no-blend, faults) |
| 4 Intelligence | ✅ Complete | `tests/analytics/`, Scenario A/B/C API tests |
| 5 Alerts/Cases | ✅ Complete | `tests/phase5/`, Scenario D lifecycle |
| 6 Integrated UI | 🟡 In progress | `tests/phase6/` (10/10); thin UI + `docs/demo-snapshots/`; Playwright `e2e/demo.spec.ts` failing on scenario label selector |
| 7 Validation/Observability | ✅ Complete | `docs/evidence/*.json`, `tests/phase7/` (29); `/metrics` + `/api/v1/validation/results` |
| 8–9 | ⬜ Not started | documentation, presentation, final submission |

**Backend test suite:** `259 passed` (`pytest tests -q`, local PostgreSQL).

---

## 0. Zero-State and Schema-First Baseline

### 0.1 Planning state

- <span style="color:#16a34a">✓</span> Authoritative professional schema/API contract completed in `docs/schema.md`.
- <span style="color:#16a34a">✓</span> Solo schema-first phase plan completed in `docs/16-hour-hackathon-phase-distribution.md`.
- <span style="color:#16a34a">✓</span> Development environment and database target selected. — Local PostgreSQL 17 (docker-compose port 5433); Supabase-compatible migration chain; FastAPI + Next.js.
- <span style="color:#16a34a">✓</span> Repository conventions, command names and contract versioning agreed. — `backend/Makefile` (`migrate`, `seed`, `test`, `server`, `openapi`); frozen contract `docs/openapi/openapi.v1.json`.

### 0.2 Phase 1 — physical schema implementation

- <span style="color:#16a34a">✓</span> Migration 001: foundation and identity. — `backend/migrations/001_foundation_and_identity.sql`
- <span style="color:#16a34a">✓</span> Migration 002: simulation, ingestion and ledger. — `backend/migrations/002_simulation_ingestion_ledger.sql`
- <span style="color:#16a34a">✓</span> Migration 003: data quality and intelligence. — `backend/migrations/003_quality_and_intelligence.sql`
- <span style="color:#16a34a">✓</span> Migration 004: alerts and coordination. — `backend/migrations/004_alerts_and_coordination.sql`
- <span style="color:#16a34a">✓</span> Migration 005: validation, indexes and read views. — `backend/migrations/005_validation_indexes_views.sql`
- <span style="color:#16a34a">✓</span> Migration 006: security, immutability, grants and RLS. — `backend/migrations/006_security_immutability_rls.sql`
- <span style="color:#16a34a">✓</span> Reference/demo seeds implemented. — `backend/seeds/reference_seed.sql` (deterministic, idempotent)
- <span style="color:#16a34a">✓</span> Migration runner/checksum history implemented. — `backend/migrations/run_migrations.py`; `schema_migrations` table; see `docs/verification/migration_checksums.txt`
- <span style="color:#16a34a">✓</span> Clean empty-database migration passes. — `docs/verification/migration_log.txt` (42 tables, 7 views, 75 indexes, 30 policies)
- <span style="color:#16a34a">✓</span> Re-run/idempotency check passes. — `docs/verification/migration_log.txt` ("nothing to apply"); `test_migration_chain.py::test_reapply_is_idempotent`
- <span style="color:#16a34a">✓</span> Constraint, trigger, view and provider A/B RLS tests pass. — `docs/verification/test_report.txt` (53 passed); `rls_provider_ab_report.txt`
- <span style="color:#16a34a">✓</span> Schema dump/metadata snapshot and migration log saved. — `docs/verification/schema.sql`, `migration_log.txt`
- <span style="color:#16a34a">✓</span> Deviations recorded as decision notes. — `docs/adr/0001`–`0005`

> Verified on local PostgreSQL 17.5 with the Supabase-compatible chain. Supabase
> deployment verification is **blocked pending project credentials** in
> `backend/.env` (see `backend/README.md`); it is not claimed until run.

### 0.3 Solo operating rules

- <span style="color:#16a34a">✓</span> Preserve module boundaries: normalized input → engines → result → candidate → alert → case.
- <span style="color:#16a34a">✓</span> Complete/test each producer before its consumer.
- <span style="color:#16a34a">✓</span> Apply only forward numbered migrations; record every later schema change.
- <span style="color:#16a34a">✓</span> Keep all 43 MVP endpoints under one owner; defer 5 stretch endpoints until the complete MVP gate.
- <span style="color:#16a34a">✓</span> Record schema/contract/release versions at each phase boundary. — Phase 7 records the release-candidate identifier (git commit + `contract_version` + engine versions) in every `validation_runs.configuration` and evidence artifact.
- <span style="color:#16a34a">✓</span> Cut optional breadth/UI polish before correctness, evidence, provider boundaries or safe fallback.

---

## A. Functional Requirements

### A.1 Mandatory

- <span style="color:#16a34a">✓</span> Show shared physical cash and separate balances for each provider
  - <span style="color:#16a34a">✓</span> *Design data model: shared cash pool + per-provider e-money balance fields (`schema.md`)*
  - <span style="color:#16a34a">✓</span> *Implement the designed tables, constraints and views through Phase 1 migrations* — migrations `001`–`006`; separation enforced by `lp_reserve_xor`, no-`provider_id` on `cash_balance_snapshots`, `v_outlet_dashboard` (no blended total). Evidence: `test_reserve_invariants.py`, `docs/verification/schema.sql`
  - <span style="color:#16a34a">✓</span> *Build unified dashboard view combining cash + all provider balances* — `GET /api/v1/outlets/{id}/dashboard` + `OutletDashboard.tsx`; four separate reserve cards, explicit no-blend copy. Evidence: `tests/phase3/test_no_blend.py`, `tests/phase6/test_e2e_scenarios.py::test_scenario_a_*`
- <span style="color:#16a34a">✓</span> Show which provider or shared cash reserve may face a shortage and approximately when
  - <span style="color:#16a34a">✓</span> *Implement demand/burn-rate projection logic (e.g., time-series or rate-based forecast)* — `services/analytics/liquidity_engine.py`; rolling burn-rate window with quality modifier.
  - <span style="color:#16a34a">✓</span> *Display estimated time-to-shortage per provider and for shared cash* — `LiquidityPanel.tsx` + `GET /api/v1/outlets/{id}/liquidity-projections`; Scenario A shows shared-cash shortage without false provider e-money shortage.
- <span style="color:#16a34a">✓</span> Detect at least one type of unusual activity and show why it was flagged
  - <span style="color:#16a34a">✓</span> *Choose at least one anomaly pattern (velocity, near-identical amounts, splitting, circular activity, etc.)* — `near_identical_amounts` within one provider/outlet/window.
  - <span style="color:#16a34a">✓</span> *Implement detection logic (rule-based, statistical, or ML)* — `services/analytics/anomaly_engine.py`.
  - <span style="color:#16a34a">✓</span> *Attach human-readable reason/evidence to each flag* — structured evidence items (count, amount cluster, parties, window) + `AnomalyPanel.tsx`.
- <span style="color:#16a34a">✓</span> Use careful language such as "unusual" or "requires review"; do not declare fraud
  - <span style="color:#16a34a">✓</span> *Review all alert copy/UI text to remove definitive fraud language* — contract fixture `alert_candidate_unsafe_language.json`; `tests/phase6/test_e2e_scenarios.py::test_no_definitive_fraud_language_in_user_visible_text`.
- <span style="color:#16a34a">✓</span> For at least one important alert, show who receives it, who owns it, the recommended next step, and the final status
  - <span style="color:#16a34a">✓</span> *Build alert routing logic (who is notified)* — routing precedence in `services/coordination/routing.py`; notifications on publish.
  - <span style="color:#16a34a">✓</span> *Build case ownership / assignment mechanism* — `POST /api/v1/cases/{id}/assignments`.
  - <span style="color:#16a34a">✓</span> *Add recommended next-step field* — persisted on case open; visible in `CasePanel.tsx`.
  - <span style="color:#16a34a">✓</span> *Add status tracking (open / acknowledged / escalated / resolved)* — full lifecycle in Scenario D; `tests/phase5/test_scenario_d.py`, `tests/phase6/test_e2e_scenarios.py::test_scenario_d_*`.
- <span style="color:#16a34a">✓</span> Show lower confidence or a safe fallback when data is missing, late, or conflicting
  - <span style="color:#16a34a">✓</span> *Implement data quality checks (missing, delayed, conflicting feeds)* — `services/analytics/quality_engine.py`; fault injection in simulation layer.
  - <span style="color:#16a34a">✓</span> *Implement confidence scoring or fallback state in UI* — data-health badges on dashboard; suppressed evaluations marked non-alertable in `AnomalyPanel.tsx`; Scenario C tests.
- <span style="color:#16a34a">✓</span> Use AI, APIs, analytics, or data processing as a meaningful part of the product
  - <span style="color:#16a34a">✓</span> *Implement non-trivial analytics components: confidence, liquidity forecast and anomaly rule modules with tests* — `tests/analytics/` (quality, liquidity, anomaly engines + API).
  - <span style="color:#9ca3af">◻</span> *Document how it's used and why it's meaningful (not decorative)* — deferred to Phase 8 responsible-design / presentation notes.

### A.2 Recommended

- <span style="color:#9ca3af">◻</span> Allow users to filter or prioritize by provider, agent, area, or time
- <span style="color:#16a34a">✓</span> Provide evidence and a simple history for important alerts
- <span style="color:#16a34a">✓</span> Offer clear Bengali, Banglish, or English explanations
- <span style="color:#16a34a">✓</span> Show at least one simple Bengali or Banglish alert with situation, evidence, uncertainty, and a safe next step
- <span style="color:#16a34a">✓</span> Support provider-specific escalation, case notes, alert history, and coordination while keeping provider boundaries clear

### A.3 Optional

- <span style="color:#16a34a">✓</span> Support simulations, peer comparison, relationship views, or cross-provider patterns — scenario runner + fault controls (`ScenarioPanel.tsx`); stretch relationship/nearby-support endpoints not built.
- <span style="color:#9ca3af">◻</span> Independently defined additional fraud/anomaly-detection scenario(s)
  - <span style="color:#9ca3af">◻</span> *Document chosen pattern, detection approach, and evidence*
  - <span style="color:#16a34a">✓</span> *Confirm scenario uses simulated/anonymized data only*
  - <span style="color:#16a34a">✓</span> *Confirm anomaly score is NOT presented as proof of fraud*

---

## B. Non-Functional Requirements

- <span style="color:#16a34a">✓</span> **Usability** — Provider distinctions, shared cash exposure, and risk signals are easy to understand — thin demo UI with labelled reserve cards and advisory copy.
- <span style="color:#16a34a">✓</span> **Performance** — Core analytical and dashboard interactions are responsive under demonstrated data volume
  - <span style="color:#16a34a">✓</span> *Benchmark response times at target data volume* — `api_avg_ms`/`api_p95_ms` measured over 90 read requests (dashboard, liquidity-projections, anomaly-flags); persisted in `metric_results`, surfaced via `/metrics` and `docs/evidence/performance-reliability.json`.
- <span style="color:#16a34a">✓</span> **Reliability** — Provider data failures/inconsistencies do not silently produce confident conclusions
  - <span style="color:#16a34a">✓</span> *Test with intentionally broken/missing/delayed provider data* — Scenario C + fault injection tests.
- <span style="color:#16a34a">✓</span> **Explainability** — Every high-impact alert exposes reason, relevant evidence, and uncertainty
- <span style="color:#16a34a">✓</span> **Security and privacy** — Synthetic identifiers only; no real credentials, customer identities, or sensitive account data
  - <span style="color:#16a34a">✓</span> *Audit dataset for any real/sensitive data leakage* — synthetic generator + demo identities only.
- <span style="color:#16a34a">✓</span> **Fairness and responsible AI** — No unsupported profiling; human review demonstrated for risk judgments — case review step required before resolve.
- <span style="color:#16a34a">✓</span> **Auditability** — Alerts, ownership changes, acknowledgements, escalations, evidence, and resolutions are traceable
  - <span style="color:#16a34a">✓</span> *Implement audit log / activity trail* — `case_audit_events` + timeline/audit API + `CasePanel.tsx`.
- <span style="color:#16a34a">✓</span> **Interoperability** — Multiple providers represented without assuming real technical integration

---

## C. Scope & Guardrail Compliance (self-check)

- <span style="color:#16a34a">✓</span> At least two logically separate financial service providers simulated — three: bKash, Nagad, Rocket.
- <span style="color:#16a34a">✓</span> No real interoperability, settlement, or conversion between provider wallets implemented
- <span style="color:#16a34a">✓</span> No access to production APIs, real customer identities, real balances, or real accounts
- <span style="color:#16a34a">✓</span> No automatic blocking, accusation, disciplinary action, or final fraud determination
- <span style="color:#16a34a">✓</span> No unauthorized cash movement, wallet refill, transfer, recovery, or reversal
- <span style="color:#16a34a">✓</span> No collection of PINs, OTPs, passwords, or private authentication data
- <span style="color:#16a34a">✓</span> No claims of regulatory approval or production fraud-detection readiness
- <span style="color:#16a34a">✓</span> All risk/anomaly signals framed as advisory, not final decisions

---

## D. Data & Simulation

- <span style="color:#16a34a">✓</span> Synthetic / mock / anonymized dataset created (agent & provider IDs, area, time, transaction type, amount, status, balances, event flags, case status) — `services/synthetic/generator.py`, scenarios A–D.
- <span style="color:#9ca3af">◻</span> Data generation method documented (how it was created) — partial: `docs/Prototype-Simulation-Walkthrough.md`; formal data & simulation note deferred to Phase 8.
- <span style="color:#9ca3af">◻</span> Assumptions documented
- <span style="color:#9ca3af">◻</span> Known limitations documented
- <span style="color:#16a34a">✓</span> Risk interpretation rule documented (anomaly ≠ fraud; false-positive risk; human review requirement) — enforced in schema constraints, alert copy, and tests.

---

## E. Required Deliverables

- <span style="color:#16a34a">✓</span> **Working prototype**
  - <span style="color:#16a34a">✓</span> *Live flow: multi-provider balances visible* — `OutletDashboard.tsx`.
  - <span style="color:#16a34a">✓</span> *Live flow: at least one liquidity or anomaly alert triggers* — Scenario A liquidity + Scenario B anomaly publish path.
  - <span style="color:#16a34a">✓</span> *Live flow: at least one case is coordinated/escalated end-to-end* — Scenario D via API (`tests/phase6`) and `CasePanel.tsx`.
- <span style="color:#9ca3af">◻</span> **Source repository**
  - <span style="color:#9ca3af">◻</span> *Source code pushed*
  - <span style="color:#16a34a">✓</span> *README written* — `backend/README.md` (frontend README minimal).
  - <span style="color:#16a34a">✓</span> *Setup / installation steps documented* — `backend/README.md` (`make db-up && make migrate && make seed && make server`).
  - <span style="color:#16a34a">✓</span> *Environment variable examples (.env.example) included* — `backend/.env.example`.
  - <span style="color:#16a34a">✓</span> *Sample data included* — `backend/seeds/reference_seed.sql` + deterministic scenario generator.
- <span style="color:#9ca3af">◻</span> **Architecture diagram**
  - <span style="color:#16a34a">✓</span> *Main interfaces shown* — `docs/diagram.md` (Mermaid data-flow + component views).
  - <span style="color:#16a34a">✓</span> *Backend components shown*
  - <span style="color:#16a34a">✓</span> *Data flow shown*
  - <span style="color:#16a34a">✓</span> *Analytics/AI services shown*
  - <span style="color:#16a34a">✓</span> *Monitoring shown* — `GET /metrics` (protected JSON summary: release id, process counters, latest validation metrics) implemented in `app/api/v1/observability.py`.
  - <span style="color:#16a34a">✓</span> *Provider boundaries shown*
  - <span style="color:#16a34a">✓</span> *Alert coordination flow shown*
- <span style="color:#9ca3af">◻</span> **Data and simulation note** (write-up of how synthetic data/scenarios were created, assumptions, limitations)
- <span style="color:#16a34a">✓</span> **Validation evidence** — at least 3 measured metrics (analytics, performance, and/or reliability) — 8 persisted on the `held_out` split; `tests/phase7/`, `docs/evidence/validation-summary.json`.
  - <span style="color:#16a34a">✓</span> *Metric 1 chosen and measured:* `anomaly_precision` / `anomaly_recall` / `anomaly_false_positive_rate` (analytics, held-out A/B/C).
  - <span style="color:#16a34a">✓</span> *Metric 2 chosen and measured:* `shortage_lead_time_minutes` (analytics) + `api_avg_ms` / `api_p95_ms` (performance).
  - <span style="color:#16a34a">✓</span> *Metric 3 chosen and measured:* `alert_explanation_coverage` + `data_quality_incident_rate` (reliability).
- <span style="color:#9ca3af">◻</span> **Responsible-design note** (privacy, human review, false positives, advisory boundaries, what the prototype intentionally does NOT do)
- <span style="color:#9ca3af">◻</span> **Final presentation**
  - <span style="color:#9ca3af">◻</span> *Problem statement covered*
  - <span style="color:#9ca3af">◻</span> *Users/stakeholders covered*
  - <span style="color:#9ca3af">◻</span> *Story-driven live demo prepared* — demo snapshots captured in `docs/demo-snapshots/`; Playwright suite needs selector fix.
  - <span style="color:#9ca3af">◻</span> *Architecture explained*
  - <span style="color:#9ca3af">◻</span> *Metrics presented*
  - <span style="color:#9ca3af">◻</span> *Coordination flow demonstrated*
  - <span style="color:#9ca3af">◻</span> *Risks & limitations discussed*
  - <span style="color:#9ca3af">◻</span> *Next steps outlined*

---

## F. Optional Supporting Materials

- <span style="color:#9ca3af">◻</span> Short demonstration video
- <span style="color:#9ca3af">◻</span> Alert case study or review log
- <span style="color:#9ca3af">◻</span> Load-test, profiling, or trace outputs
- <span style="color:#9ca3af">◻</span> Additional multi-provider scenarios or relationship visualizations

---

## G. Demonstration Scenario Coverage (from Section 11)

- <span style="color:#16a34a">✓</span> Scenario A — Hidden shared-cash shortage driven by provider cash-out demand — `tests/phase6/test_e2e_scenarios.py::test_scenario_a_*`; snapshot `docs/demo-snapshots/dashboard_a.json`.
- <span style="color:#16a34a">✓</span> Scenario B — Liquidity pressure with unusual activity — `test_scenario_b_*`; snapshots `anomaly_flags_b.json`, `publish_b.json`.
- <span style="color:#16a34a">✓</span> Scenario C — Cross-provider or data inconsistency — `test_scenario_c_*`; snapshots `anomaly_run_c.json`, `liquidity_run_c.json`.
- <span style="color:#16a34a">✓</span> Scenario D — Coordinated response and closure — `test_scenario_d_*`; snapshots `case_*.json`, `case_timeline.json`, `case_audit.json`.

---

## H. System Design Feature List

Features grouped by module from the System Design document. Tags: **[M]** Mandatory, **[R]** Recommended, **[O]** Optional, **[E]** Engineering-depth.

### H.1 Unified Visibility

- <span style="color:#16a34a">✓</span> **[M]** Combined agent view: shared cash + each provider's balance, clearly separated (never summed into one blended figure)
- <span style="color:#9ca3af">◻</span> **[R]** Filter/prioritize by provider, agent, area, or time
- <span style="color:#9ca3af">◻</span> **[E]** Multi-agent overview for Operations/Management

### H.2 Liquidity Intelligence

- <span style="color:#16a34a">✓</span> **[M]** Per-provider and shared-cash shortage projection with estimated time window
- <span style="color:#16a34a">✓</span> **[M]** Confidence indicator on every projection
- <span style="color:#16a34a">✓</span> **[R]** Contributing-signal breakdown (why the projection says what it says)
- <span style="color:#9ca3af">◻</span> **[O]** What-if simulation (e.g., "what if cash-out demand doubles for the next hour") — stretch endpoint.

### H.3 Anomaly & Risk Detection

- <span style="color:#16a34a">✓</span> **[M]** At least one fully implemented anomaly pattern with evidence trail
- <span style="color:#16a34a">✓</span> **[M]** Careful, non-accusatory language throughout ("unusual," "requires review")
- <span style="color:#16a34a">✓</span> **[R]** Evidence + short history attached to each anomaly alert
- <span style="color:#16a34a">✓</span> **[E]** Plausible-benign-explanation field alongside every anomaly flag
- <span style="color:#9ca3af">◻</span> **[O]** Second/third anomaly pattern (e.g., transaction splitting, circular activity) if time allows
- <span style="color:#9ca3af">◻</span> **[O]** Cross-provider relationship view using simulated identifiers

### H.4 Coordination & Case Management

- <span style="color:#16a34a">✓</span> **[M]** For each important alert: assigned receiver, owner, recommended next step, current status
- <span style="color:#16a34a">✓</span> **[R]** Case notes and alert history, provider-boundary-respecting
- <span style="color:#16a34a">✓</span> **[E]** Full case lifecycle (open → acknowledged → escalated → resolved) with timestamps
- <span style="color:#16a34a">✓</span> **[E]** Routing rules aligned to the agent → field officer → area manager → central ops hierarchy
- <span style="color:#9ca3af">◻</span> **[O]** Nearby-agent support discovery (e.g., "Agent X 400m away has surplus cash")

### H.5 Data Quality & Trust

- <span style="color:#16a34a">✓</span> **[M]** Confidence/fallback state shown when data is missing, late, or conflicting
- <span style="color:#16a34a">✓</span> **[E]** Configurable fault injection for live demo of Scenario C
- <span style="color:#16a34a">✓</span> **[E]** Visible "data health" indicator per provider feed

### H.6 Explainability & Localization

- <span style="color:#16a34a">✓</span> **[R]** English explanations for every alert
- <span style="color:#16a34a">✓</span> **[R]** At least one Bengali/Banglish alert with situation, evidence, uncertainty, and next step
- <span style="color:#16a34a">✓</span> **[E]** Consistent multi-language rendering from one structured alert object (no drift between languages)

### H.7 Security, Privacy & Responsible Design

- <span style="color:#16a34a">✓</span> **[M]** Synthetic identifiers only; no real credentials or account data anywhere in the system
- <span style="color:#16a34a">✓</span> **[M]** No automatic blocking, accusation, or financial action anywhere in the codebase
- <span style="color:#16a34a">✓</span> **[E]** Role-based access control enforcing provider data boundaries — app auth + RLS; `tests/phase5/test_authorization.py`, `tests/phase6/test_provider_isolation_*`.
- <span style="color:#9ca3af">◻</span> **[E]** "Responsible-design note" content generated directly from documented guardrails, not written after the fact — Phase 8.

### H.8 Observability & Validation

- <span style="color:#16a34a">✓</span> **[M]** Analytics/AI meaningfully embedded (liquidity forecasting + anomaly detection, not decorative)
- <span style="color:#16a34a">✓</span> **[E]** `/metrics` endpoint or dashboard panel showing: forecast error on held-out simulated data, shortage detection lead time, anomaly precision/recall against injected test cases, false-positive rate, alert explanation coverage, API latency, and data-quality incident counts — `GET /metrics` + `GET /api/v1/validation/results` + management/admin Validation Evidence UI panel; metrics persisted in `metric_results` on the `held_out` split.
- <span style="color:#16a34a">✓</span> **[E]** Structured audit log covering every ownership change, acknowledgement, escalation, and resolution

### H.9 Presentation-Ready Artifacts

- <span style="color:#16a34a">✓</span> **[M]** Architecture diagram (System Design, Section 1) — `docs/diagram.md`.
- <span style="color:#9ca3af">◻</span> **[M]** Data & simulation note (how synthetic data/scenarios were generated)
- <span style="color:#9ca3af">◻</span> **[M]** Responsible-design note (derived from H.7 guardrails)
- <span style="color:#9ca3af">◻</span> **[R]** Short demo video walking through Scenarios A–D

---

## I. Solo Endpoint Completion

An endpoint group is complete only when routes are registered, runtime behavior is persistence-backed, authorization is enforced, tests pass, OpenAPI matches and the demo can exercise the critical path.

### I.1 Data and intelligence APIs — 24 MVP

- <span style="color:#16a34a">✓</span> Reference/outlet endpoints complete (4): providers, areas, outlet list and outlet detail.
- <span style="color:#16a34a">✓</span> Dashboard/ledger endpoints complete (3): dashboard, transactions and balance history.
- <span style="color:#16a34a">✓</span> Simulation endpoints complete (6): scenario list, run start/status/reset and fault create/toggle.
- <span style="color:#16a34a">✓</span> Ingestion/data-quality endpoints complete (3): batch ingestion and quality current/history.
- <span style="color:#16a34a">✓</span> Liquidity endpoints complete (2): run and projection read.
- <span style="color:#16a34a">✓</span> Anomaly endpoints complete (3): run, list and evidence detail.
- <span style="color:#16a34a">✓</span> Operations/evidence endpoints complete (3): `/health`, `/metrics`, validation results. — `/health` ✅; `/metrics` ✅ (`app/api/v1/observability.py`, admin/management); `/api/v1/validation/results` ✅ (`app/api/v1/validation.py`, persistence-backed, stub removed). `tests/phase7/` (29).

### I.2 Coordination and security APIs — 19 MVP

- <span style="color:#16a34a">✓</span> Auth/profile endpoints complete (3): demo login, `/me`, locale preference.
- <span style="color:#16a34a">✓</span> Alert endpoints complete (4): list, detail, explanations and case opening.
- <span style="color:#16a34a">✓</span> Case endpoints complete (9): list, detail, timeline, assignment, acknowledge, escalate, resolve, notes and review.
- <span style="color:#16a34a">✓</span> Notification/audit endpoints complete (3): notification list/read and case audit events.

### I.3 Stretch endpoints — 5, complete MVP gate required

- <span style="color:#9ca3af">◻</span> What-if run create/read.
- <span style="color:#9ca3af">◻</span> Synthetic relationship insight.
- <span style="color:#9ca3af">◻</span> Nearby support options.
- <span style="color:#9ca3af">◻</span> Approved-process support request.

## J. Solo Phase Gates — Dependency-Based, No Time Boxes

- <span style="color:#16a34a">✓</span> **Phase 1 — Authoritative schema:** all six migrations, constraints, indexes, views, seeds, grants and RLS pass on a fresh database.
- <span style="color:#16a34a">✓</span> **Phase 2 — Application foundation:** runnable backend/DB/config/errors/logging/OpenAPI/contracts/tests and frontend scaffold.
- <span style="color:#16a34a">✓</span> **Phase 3 — Synthetic ingestion and ledger:** deterministic A–D data, faults, append-only ledger and separated dashboard reads.
- <span style="color:#16a34a">✓</span> **Phase 4 — Data quality and intelligence:** quality/confidence, forecast, anomaly evidence, suppression, persistence and analytics APIs.
- <span style="color:#16a34a">✓</span> **Phase 5 — Alerts, cases and security:** auth, localized immutable alerts, routing, lifecycle, notifications, audit, idempotency/concurrency and provider RBAC/RLS.
- <span style="color:#9ca3af">◻</span> **Phase 6 — Integrated API and thin UI:** one release candidate passes complete Scenarios A–D; MVP frozen. — Backend regression `tests/phase6/` (10/10) ✅; thin UI panels ✅; demo snapshots ✅; Playwright E2E needs scenario-title selector fix; formal MVP freeze sign-off pending.
- <span style="color:#16a34a">✓</span> **Phase 7 — Validation/observability/safety:** 8 numeric metrics on the `held_out` split (analytics + performance + reliability) plus secrets/unsafe-endpoint/prohibited-language scans passing; evidence in `docs/evidence/*.json`, `tests/phase7/` (29). Re-run: `make validate` + `make safety-scan`.
- <span style="color:#9ca3af">◻</span> **Phase 8 — Documentation/presentation:** all seven deliverables match implementation and two clean rehearsals pass.
- <span style="color:#9ca3af">◻</span> **Phase 9 — Final QA/submission:** critical checks pass and submission receipt/permissions are confirmed.

### J.1 Phase 6 MVP freeze gate (must all pass before stretch work)

- <span style="color:#16a34a">✓</span> Shared cash plus three provider balances displayed, never blended
- <span style="color:#16a34a">✓</span> Shortage timing and confidence shown for every actionable projection
- <span style="color:#16a34a">✓</span> At least one evidence-backed anomaly with benign context visible
- <span style="color:#16a34a">✓</span> Missing/stale/conflicting data produces safe fallback and suppression (Scenario C)
- <span style="color:#16a34a">✓</span> Routed case with owner, next step, full lifecycle, and complete audit trail (Scenario D)
- <span style="color:#16a34a">✓</span> English and Bangla/Banglish explanation rendering works
- <span style="color:#16a34a">✓</span> Provider-boundary enforcement holds in UI and API
- <span style="color:#16a34a">✓</span> No unsafe language or prohibited financial/punitive actions anywhere

## K. Final Submission Checklist (from problem statement Section 16)

- <span style="color:#16a34a">✓</span> At least two provider contexts represented distinctly
- <span style="color:#16a34a">✓</span> Shared cash and provider-specific balances demonstrated
- <span style="color:#16a34a">✓</span> Forward-looking liquidity insight demonstrated
- <span style="color:#16a34a">✓</span> At least one anomaly category demonstrated with evidence
- <span style="color:#16a34a">✓</span> Human-review and careful risk language included
- <span style="color:#16a34a">✓</span> At least one alert demonstrates routing, ownership, acknowledgement or escalation, and a visible resolution status
- <span style="color:#9ca3af">◻</span> Repository, data, README, and architecture complete — push + formal docs pending Phase 8.
- <span style="color:#16a34a">✓</span> At least three metrics measured and explained — 8 metrics on the `held_out` split with method + sample size + limitations; `docs/evidence/validation-summary.json`, `GET /api/v1/validation/results`.
- <span style="color:#16a34a">✓</span> Failure, uncertainty, and false-positive considerations shown — Scenario C suppression + benign context.
- <span style="color:#9ca3af">◻</span> Safety, privacy, boundaries, and limitations stated — responsible-design note pending Phase 8.
- <span style="color:#9ca3af">◻</span> Final presentation ready
