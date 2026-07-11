# 16-Hour Hackathon Phase Distribution

## 1. Objective

Build and demonstrate a **complete and well-engineered** (not maximal) decision-support prototype — a modular monolith for multi-provider agent liquidity and coordination — that:

1. Shows one shared physical-cash reserve alongside **separate** provider e-money balances (bKash, Nagad, Rocket — never blended or converted).
2. Predicts which reserve may run short and approximately when, with a confidence indicator on every projection.
3. Detects at least one unusual transaction pattern with an evidence trail and a plausible-benign-explanation field — never a fraud label.
4. Reduces confidence or falls back safely when source data is missing, delayed, or conflicting (Data Quality & Confidence Engine).
5. Routes important alerts through assignment, acknowledgement, escalation, and resolution with provider-boundary-respecting RBAC.
6. Renders explainable alert copy in English and at least one Bengali/Banglish template from a single structured alert object.
7. Uses synthetic data only, preserves provider boundaries, and supports human review without declaring fraud or executing financial actions.

The plan deliberately favors a **connected liquidity → anomaly → coordination chain** (traceable end-to-end) over a broad collection of unfinished features or "three cards on a dashboard."

## 2. Scope Decision Before the Clock Starts

### Committed MVP (maps to System Design [M] + critical [E] items)

**Architecture:** Single deployable modular monolith — clear internal module boundaries, no microservice sprawl. **Persistence:** PostgreSQL hosted on **Supabase** (SQL migrations in repo; secrets in `.env` only).

**Providers & data:**
- Three logically separate providers: **bKash, Nagad, Rocket** (simulated feeds; no real API integration).
- One agent/outlet with a shared physical-cash pool and per-provider e-money balances.
- Provider Feed Ingestion & Normalization with injectable delay/inconsistency for Scenario C.

**Core backend modules (minimum):**
- Ledger & Aggregation Service — shared cash + per-provider balances; read-only unified view; no cross-provider transfers.
- Data Quality & Confidence Engine — `fresh` / `stale` / `missing` / `conflicting` flags feeding downstream engines.
- Liquidity Forecasting Engine — burn-rate projection per provider and shared cash with confidence band.
- Anomaly Detection Engine — one fully-built pattern (e.g., near-identical repeated amounts); evidence + `plausible_benign_explanation`.
- Alert & Case Management Service — routing, ownership, lifecycle `open → acknowledged → escalated → resolved`, case notes.
- Explainability & Localization Service — EN + at least one Bangla/Banglish template fill (situation, evidence, uncertainty, next step).
- Auth & Provider-Boundary Guard — JWT RBAC; Provider A ops cannot open Provider B cases.
- Monitoring & Observability — structured logs, `/health` + `/metrics` summary.

**UI views (minimum):**
- Agent / unified operations dashboard (mobile-responsive).
- Alert detail and case coordination view.
- Provider-scoped access enforced per role.

**Demo & validation:**
- Configurable fault injection for stale/conflicting feeds (Scenario C).
- Activity/audit trail for every case transition.
- At least three measured validation metrics (see Phase 7).
- README, architecture diagram, data/simulation note, responsible-design note, and final presentation.

### Stretch Scope Only ([R] and [O] from System Design)

- Multi-agent overview for Operations/Management.
- Contributing-signal breakdown on forecasts; what-if simulation.
- Second/third anomaly patterns; cross-provider relationship view.
- Nearby-agent support discovery.
- Simulated webhook/email notification stub beyond in-app alerts.
- Short demo video.
- Redis cache or sophisticated ML models.

Do not begin stretch work until the MVP passes the Hour 12 integration gate.

### Explicitly Excluded (System Design §7 — do not build)

- Real bKash/Nagad/Rocket API integration or credentials.
- Any endpoint capable of moving money, blocking users, or freezing funds.
- Multi-service/distributed architecture (Kafka, service mesh, multi-region).
- Free-form LLM-generated financial recommendations without template/evidence structure.
- Deep learning anomaly models without labeled validation data.

## 3. Recommended Technical Strategy

Keep the architecture small enough to finish while matching the System Design modular monolith:

```text
[Simulated Provider Feeds: bKash / Nagad / Rocket]
                 │
                 ▼
      [Ingestion & Normalization] ──► [Data Quality & Confidence Engine]
                 │                              │
                 ▼                              │ (confidence signal)
       [Ledger & Aggregation]                  │
        (cash + per-provider balances)         │
                 │                              │
     ┌───────────┴────────────┐                 │
     ▼                        ▼                  │
[Liquidity Engine]     [Anomaly Detection] ◄─────┘
     │                        │
     └───────────┬────────────┘
                 ▼
     [Alert & Case Management]
        (routing + ownership)
                 │
      ┌──────────┴───────────┐
      ▼                       ▼
[Explainability /      [Coordination /
 Localization]          Notification (in-app)]
      │                       │
      └───────────┬───────────┘
                  ▼
     [Role-based Dashboards]  ◄── [Auth & Provider-Boundary Guard]
                  │
                  ▼
        [Human: ack / escalate / resolve / notes]
                  │
                  ▼
        [Audit Log] ──► [Metrics Store] ──► [/metrics + validation evidence]
```

**Suggested stack** (from System Design §6):

| Layer | Suggestion |
|---|---|
| Frontend | React (or Next.js) + Tailwind — shared component library across Agent/Ops/Risk views |
| Backend | Node.js (Express/NestJS) or Python (FastAPI) — modular boundaries matching §2 components |
| Database | PostgreSQL via **Supabase** — ledger, cases, audit trail; SQL migrations in repo |
| Auth | JWT-based RBAC in app layer — provider-boundary enforcement (optional: Supabase RLS policies per provider scope) |
| Analytics | Hand-rolled statistical rules or pandas/scikit-learn — explainable, not opaque |
| Deployment | Single Docker container — one command for judges |

**Degraded-data behavior** (Scenario C path — non-negotiable):

- Data Quality Engine flags `stale` / `conflicting` → Liquidity Engine widens confidence band or marks projection low-confidence.
- Anomaly Engine **suppresses** new high-confidence flags for the affected provider; surfaces a data-issue advisory instead.
- Dashboard shows: "Provider X data delayed — figures may be outdated" (balances stay separate; no blended misleading number).

Suggested analytics:

- **Liquidity forecast:** rolling burn rate per provider and shared cash. Output `{provider, projected_shortage_time, confidence, contributing_signal}`. Wider band when data quality is degraded.
- **Forecast confidence:** feed freshness, sample count, rate stability, conflicting-balance checks → consumed by both engines via the Data Quality modifier.
- **Unusual activity:** one fully-built rule (e.g., near-identical repeated amounts from a small account cluster — Scenario B). Every flag carries triggering signals, raw evidence, confidence, and `plausible_benign_explanation` (e.g., "may reflect Eid demand").
- **Safe language:** `unusual`, `requires review`, `possible liquidity pressure`, `estimated`. Never `fraudster`, `fraud confirmed`, or `block account`.

## 4. Role Allocation

For a four-person team, use these parallel lanes aligned to System Design modules:

| Lane | Primary responsibility |
|---|---|
| Product/UX and presentation | Requirements, wireframes (Agent / Ops / Risk views), alert wording, demo story (Scenarios A–D), slides, responsible-design note |
| Frontend | Role-based dashboards, forecast cards, data-health indicators, alert evidence, filters, case workflow UI, localization toggle |
| Backend/data | Supabase project + SQL migrations, Ingestion & normalization, Ledger & Aggregation, schemas, synthetic generator with fault injection, APIs, case/audit persistence, Auth & Provider-Boundary Guard |
| Analytics/QA | Data Quality & Confidence Engine, Liquidity + Anomaly engines, Explainability templates, test scenarios, `/metrics`, validation evidence |

For fewer people:

- **Three people:** combine Product/UX with Frontend.
- **Two people:** one owns UI/demo; one owns data/backend/analytics. Both test and document.
- **Solo:** follow the phases sequentially, use one application process and a **Supabase** project (free tier) for Postgres, and omit all stretch work.

Assign one integration owner. That person controls shared schemas, approves interface changes, keeps the main branch runnable, and calls each phase gate.

## 5. Sixteen-Hour Schedule at a Glance

| Clock | Duration | Phase | Required result |
|---|---:|---|---|
| 00:00-00:45 | 0:45 | 1. Alignment and scope lock | Demo story, roles, stack, MVP and safety boundaries agreed |
| 00:45-02:15 | 1:30 | 2. UX, architecture, and data contracts | Screen map, schemas, API/state contracts, synthetic scenarios |
| 02:15-05:00 | 2:45 | 3. Foundation vertical slice | Data flows into a runnable unified dashboard |
| 05:00-07:30 | 2:30 | 4. Liquidity and anomaly analytics | Forecasts and explainable alerts work on controlled scenarios |
| 07:30-10:00 | 2:30 | 5. Confidence and coordinated response | Bad-data fallback and end-to-end case workflow work |
| 10:00-12:00 | 2:00 | 6. UX integration and MVP freeze | Complete demo path works without manual data edits |
| 12:00-13:30 | 1:30 | 7. Validation, reliability, and safety QA | Three or more metrics and failure evidence captured |
| 13:30-14:30 | 1:00 | 8. Submission documentation | Repository and all required notes/diagram complete |
| 14:30-15:30 | 1:00 | 9. Presentation and rehearsal | Timed story-driven demo rehearsed with backup |
| 15:30-16:00 | 0:30 | 10. Final buffer and submission | Only critical fixes; final checklist and submission |

Total: **16 hours**.

---

## 6. Detailed Phase Instructions

## Phase 1 — Alignment and Scope Lock

**Time:** 00:00-00:45  
**Goal:** Remove ambiguity and agree on one demonstrable story.

### Actions

1. Read the mandatory requirements, guardrails, deliverables, demonstration scenarios, and scoring weights together.
2. Select the main story (Scenarios A–D from problem statement §11):
   - An outlet has shared cash and **three separate** provider balances (bKash, Nagad, Rocket).
   - bKash cash-outs accelerate, creating a projected shared-cash shortage (Scenario A).
   - Several near-identical transactions are flagged as unusual with evidence and a plausible-benign explanation (Scenario B).
   - A provider feed later becomes stale/conflicting; confidence drops and anomaly flags are suppressed for that provider (Scenario C).
   - The alert is routed per hierarchy (agent → field officer → provider ops), assigned, acknowledged, escalated, and resolved (Scenario D).
3. Define the primary views from System Design §1:
   - Agent view (web, mobile-responsive).
   - Operations / Coordinator view.
   - Alert detail and case coordination view (Risk/Compliance as stretch if time permits).
4. Freeze the technology stack (including **Supabase** for PostgreSQL), repository conventions, owners, and integration method.
5. Write the exact three-to-five-minute demo sequence before implementation begins.
6. Copy the mandatory submission checklist into the issue board and assign every item.

### Deliverables

- One-paragraph product definition.
- Prioritized backlog labeled `Must`, `Should`, and `Stretch`.
- Named owners for UI, backend/data, analytics/QA, documentation, and integration.
- Written demo script skeleton.
- Explicit guardrail list visible to every teammate.

### Exit gate

- Every mandatory capability maps to a screen, service, data field, test, or document.
- No planned feature transfers money, merges provider wallets, blocks users, exposes real identities, or declares fraud.
- The team can state what it will cut first if delayed.

## Phase 2 — UX, Architecture, and Data Contracts

**Time:** 00:45-02:15  
**Goal:** Make parallel work possible without integration ambiguity.

### Actions

1. Sketch the dashboard:
   - Shared-cash card (never blended with provider totals).
   - Separate bKash, Nagad, and Rocket balance cards.
   - Per-provider **data health** indicator (`fresh` / `stale` / `missing` / `conflicting`).
   - Estimated time-to-shortage and confidence on each card.
   - Transaction/liquidity trend.
   - Prioritized alerts.
   - Clear provider colors and labels without implying wallet interoperability.
2. Sketch the alert detail:
   - Situation and severity.
   - Why it was flagged (contributing signals).
   - Evidence and uncertainty.
   - `plausible_benign_explanation` field.
   - EN explanation + Bangla/Banglish template toggle (same underlying alert object).
   - Recipient, owner, recommended safe next step, status, notes, and history.
3. Define minimum entities (System Design §4):
   - `Agent/Outlet`, `ProviderBalance`, `Transaction`, `LiquidityProjection`, `AnomalyFlag`, `Case/Alert`, `AuditEvent`.
4. Define provider-separated schemas and response contracts. Include timestamps, synthetic identifiers, data source, feed_status, and provider scope on relevant records.
5. Define controlled scenarios with **fault injection** toggles:
   - Normal operation.
   - Scenario A — Hidden provider shortage.
   - Scenario B — Liquidity pressure plus repeated-amount activity.
   - Scenario C — Stale/conflicting provider data (confidence degradation + anomaly suppression).
   - Scenario D — Coordinated alert closure through full lifecycle.
6. Define routing rules: alert type + provider + area → stakeholder (agent, field officer, provider ops, risk analyst) per Section 5 hierarchy.
7. Define thresholds and fault-injection config in a configuration file rather than scattering constants through code.
8. Create the initial architecture diagram matching System Design §1 (modular monolith, all §2 components labeled).
9. Create a **Supabase** project; add `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (backend only), and `DATABASE_URL` to `.env.example` — never commit real values.
10. Draft initial SQL migrations (or Supabase migration files) for core tables: agents, provider balances, transactions, cases, audit events.

### Deliverables

- Approved low-fidelity screen layout.
- Shared schema/API contract.
- Supabase migration draft applied to dev project.
- Synthetic scenario specification with expected outputs.
- Architecture diagram draft.
- Forecast, anomaly, and confidence rule definitions.

### Exit gate

- Frontend can build against fixtures without waiting for analytics/backend.
- Analytics can consume the exact transaction and balance schema.
- Every alert object supports reason, evidence, uncertainty, recipient, owner, next step, status, and timestamps.

## Phase 3 — Foundation Vertical Slice

**Time:** 02:15-05:00  
**Goal:** Produce the first runnable end-to-end system early.

### Parallel work

**Backend/data lane**

1. Implement schemas and the **Provider Feed Ingestion & Normalization** module.
2. Apply SQL migrations to **Supabase**; connect backend via `DATABASE_URL` or Supabase client.
3. Generate three providers (bKash, Nagad, Rocket), shared cash, timestamped balance snapshots, transactions, feed health, and case states; seed into Supabase.
4. Implement **Ledger & Aggregation Service** — shared cash + per-provider balances; no cross-provider transfer endpoints.
5. Add deterministic seeds and **configurable fault injection** (late arrival, missing fields, conflicting snapshots).
6. Stub **Auth & Provider-Boundary Guard** (JWT RBAC roles at minimum).
7. Expose fixtures through REST API (or GraphQL if team prefers).

**Frontend lane**

1. Build the dashboard shell and provider-separated balance cards.
2. Add loading, empty, error, and stale-data states from the beginning.
3. Build the alert list and alert-detail/case shell using fixtures.

**Analytics/QA lane**

1. Implement **Data Quality & Confidence Engine** — tag feeds `fresh` / `stale` / `missing` / `conflicting`; emit confidence modifier.
2. Write unit tests for normal, malformed, and fault-injected samples.
3. Prepare labeled synthetic cases for forecast and anomaly evaluation.

**Product/documentation lane**

1. Start README setup instructions and assumptions.
2. Review all visible wording for advisory language.
3. Maintain requirement-to-evidence mapping.

### Integration checkpoint at Hour 4

- Merge schemas, fixtures, and the first dashboard view.
- Resolve contract mismatches immediately; do not defer them.

### Exit gate at Hour 5

- One command starts the prototype (Docker or documented local setup); backend reads/writes **Supabase PostgreSQL**.
- The dashboard displays shared cash and **three separate** provider balances from generated data.
- Per-provider data-health state is visible.
- Synthetic scenarios can be selected or replayed deterministically; fault injection is toggleable.
- No real credentials, names, balances, accounts, or production APIs exist in the repository.

## Phase 4 — Liquidity and Anomaly Analytics

**Time:** 05:00-07:30  
**Goal:** Complete the core decision value and make every output explainable.

### Actions

1. Implement **Liquidity Forecasting Engine** — separate burn rates and shortage estimates for:
   - Shared physical cash.
   - bKash, Nagad, and Rocket e-money (each isolated).
2. Pull Data Quality confidence modifier into every projection; widen band when degraded.
3. Prevent invalid forecasts:
   - Never divide by zero.
   - Do not predict shortage for flat or replenishing balances.
   - Do not silently mix providers.
   - Make the forecast window and minimum sample count configurable.
4. Implement **Anomaly Detection Engine** — one fully-built rule (near-identical repeated amounts within a short window):
   - Define time window, amount tolerance, minimum count, and optional velocity threshold.
   - Return structured evidence + `plausible_benign_explanation`, not merely a Boolean flag.
5. Wire outputs into **Alert & Case Management Service** — create cases with routing rules when thresholds cross.
6. Connect liquidity and unusual activity in one alert when both affect the same provider/outlet/time window.
7. Implement **Explainability & Localization Service** — EN templates; add Bangla/Banglish template for at least one alert type.
8. Generate explanations such as:
   - `Shared cash may run short in approximately 2h 10m if the recent cash-out rate continues.`
   - `Requires review: 5 cash-outs of ~1,000 BDT from 3 accounts in 12 minutes; may reflect Eid demand.`
9. Display safe recommendations such as contacting the outlet, verifying feed health, reviewing transactions, or escalating through the provider's authorized process.
10. Add tests for threshold boundaries, no-depletion conditions, injected anomalies, and normal high-demand periods.

### Deliverables

- Working Liquidity Forecasting Engine with confidence and contributing signals.
- Working Anomaly Detection rule with evidence and `plausible_benign_explanation`.
- Alert & Case Management creating routed cases from engine outputs.
- EN + at least one Bangla/Banglish explanation from templates.
- At least one combined liquidity/anomaly alert.
- Initial analytics evaluation output.

### Exit gate

- A judge can see what may run short, approximately when, why the alert exists, how uncertain it is, and what safe human step is recommended.
- The unusual-activity alert never claims fraud.
- Known synthetic positives trigger; normal cases remain mostly unflagged.

## Phase 5 — Confidence and Coordinated Response

**Time:** 07:30-10:00  
**Goal:** Demonstrate reliability under imperfect data and a traceable human workflow.

### Actions

1. Harden **Data Quality & Confidence Engine** feed-health checks:
   - Missing feed or required fields.
   - Timestamp older than the configured freshness threshold.
   - Conflicting balance values or impossible transitions.
   - Insufficient samples for forecasting.
2. Map feed health to safe output behavior (Scenario C path):
   - Lower confidence / widen projection band.
   - Show the affected provider, data timestamp, and visible "data delayed" UI state.
   - **Suppress** new high-confidence anomaly flags for the affected provider; surface data-issue advisory instead.
   - Recommend checking the source rather than making a financial recommendation.
3. Implement full **Alert & Case Management** lifecycle:
   - Alert created and routed via rule engine (type + provider + area → stakeholder).
   - Owner assigned.
   - Acknowledgement recorded.
   - Note or evidence added.
   - Escalation to risk/review or operational follow-up when appropriate.
   - Resolution status and resolution note recorded.
4. Implement **Coordination / Notification Layer** — in-app notification to assigned stakeholder (primary demo channel).
5. Write every action to append-only **AuditEvent** log with actor, timestamp, previous state, new state, and provider scope.
6. Enforce **Auth & Provider-Boundary Guard** — Provider A ops cannot open Provider B cases; test cross-provider leakage.
7. Validate Bangla/Banglish template wording (situation, evidence, uncertainty, safe next step).

### Deliverables

- Low-confidence/stale/conflicting data states with visible per-provider data health.
- Anomaly suppression under degraded data (Scenario C).
- Provider-aware routing, ownership, and RBAC enforcement.
- In-app notification on alert assignment.
- Visible end-to-end case history and final status.
- Tests for invalid state changes and cross-provider leakage.

### Exit gate at Hour 10

- Scenario C visibly lowers confidence, widens bands, and suppresses high-confidence anomaly flags — shows data-issue advisory instead.
- Scenario D can be completed entirely through the UI/API without editing data manually.
- Alert creation, routing, assignment, acknowledgement, escalation, notes, and resolution are traceable in audit log.
- Provider-boundary RBAC verified (Provider A user cannot access Provider B case).

## Phase 6 — UX Integration and MVP Freeze

**Time:** 10:00-12:00  
**Goal:** Turn separate features into one clear, stable product story.

### Actions

1. Integrate all live data and remove placeholder content from the demo path.
2. Prioritize the dashboard by urgency and estimated shortage time.
3. Add filters for provider and time; add agent/area filters per [R] priority if the data model supports them.
4. Show per-provider **data health** indicators on the dashboard.
5. Add EN / Bangla / Banglish toggle on alert detail (same structured object, no drift).
6. Standardize severity, provider colors, status labels, timestamps, units, and number formatting.
7. Make uncertainty visible next to the prediction, not hidden in a tooltip or documentation.
8. Add clear navigation from dashboard alert → evidence → case actions/history.
9. Test the complete story from a fresh setup and clean browser/session.
10. Fix only issues that block comprehension, correctness, safety, or the demo.

### Deliverables

- Stable integrated MVP.
- Complete story covering scenarios A through D, whether as separate fixtures or one sequence.
- Feature freeze and tagged/demo-ready commit.

### Hour 12 hard gate

The following must work before any stretch feature is considered:

- Shared cash plus **three separate** provider balances (bKash, Nagad, Rocket), never blended.
- Forward shortage estimate with confidence on every projection.
- One evidence-backed unusual-activity alert with `plausible_benign_explanation`.
- Per-provider data-health indicator; missing/stale/conflicting-data fallback with anomaly suppression (Scenario C).
- Recipient, owner, next step, full lifecycle (ack → escalate → resolve).
- EN + at least one Bangla/Banglish explanation from templates.
- Audit trail and provider-boundary RBAC.
- Careful human-review language throughout.

If any item fails, spend all remaining development time on it and cut recommended/optional features.

## Phase 7 — Validation, Reliability, and Safety QA

**Time:** 12:00-13:30  
**Goal:** Produce credible measured evidence and eliminate high-risk failures.

### Required metrics

Measure at least three from System Design §5.8; the recommended set covers analytics, performance, and reliability:

1. **Analytics — anomaly precision/recall** and **false-positive rate** on labeled synthetic scenarios (injected test cases). State sample size and injection method.
2. **Analytics — forecast error** or **shortage detection lead time** on held-out simulated data.
3. **Performance — API latency** (average and p95) at documented transaction volume.
4. **Reliability — alert explanation coverage** — percentage of high-impact alerts containing reason, evidence, uncertainty, and recommended next step; target 100% for demo set.
5. **Reliability — data-quality incident handling** — percentage of missing/stale/conflicting inputs that correctly produce degraded confidence and anomaly suppression; target 100% for defined failure cases.

Expose results via `/metrics` endpoint or a validation dashboard panel.

### Actions

1. Implement **Monitoring & Observability** — structured request logs, `/health`, `/metrics` summary, data-quality event log.
2. Freeze a labeled validation dataset separate from threshold-tuning examples.
3. Run repeatable evaluation and save raw outputs or screenshots.
4. Test intentionally missing, delayed, malformed, and conflicting provider data (fault injection).
5. Test normal event-driven demand to expose false positives.
6. Verify no unsupported profiling or final fraud judgment appears.
7. Audit the repository for real credentials, identities, account data, and unsafe actions.
8. Verify setup on a clean environment or teammate machine (Docker one-command start).
9. Record limitations honestly; do not inflate simulated results into production claims.

### Exit gate

- At least three metrics have numeric results, sample sizes, methods, and limitations.
- The demo survives bad-data tests without crashing or producing misleading confidence.
- All high-impact alerts expose evidence and uncertainty.
- No critical safety, privacy, or provider-boundary issue remains.

## Phase 8 — Submission Documentation

**Time:** 13:30-14:30  
**Goal:** Complete every required non-code deliverable.

### Actions

1. Finalize README:
   - Problem and users.
   - Features and screenshots if available.
   - Architecture summary.
   - Setup/run steps (include Supabase project creation, running migrations, and seed command).
   - Environment variables and `.env.example` (`SUPABASE_URL`, `DATABASE_URL`, keys — placeholders only).
   - Demo scenario instructions.
   - Test and metric commands.
2. Finalize the architecture diagram — modular monolith with all §2 components: Ingestion, Ledger, Data Quality, Liquidity, Anomaly, Alert/Case, Explainability, Coordination, Auth, Monitoring; provider boundaries and case coordination flow shown.
3. Write the data and simulation note (System Design deliverable):
   - Generation method and deterministic seed.
   - Fields, volumes, and scenarios (A–D).
   - Fault-injection configuration.
   - Assumptions and injected anomalies.
   - Validation split.
   - Known limitations.
4. Write the responsible-design note (derived from guardrails — not after-the-fact):
   - Synthetic data and privacy.
   - Anomaly is not proof of fraud; `plausible_benign_explanation` purpose.
   - False-positive risk and human review.
   - Provider separation and RBAC.
   - Actions intentionally not performed (no fund movement, blocking, or accusation).
5. Add `/metrics` or validation panel results with methods and limitations.
6. Confirm sample data and source code are committed; `.env.example` documents Supabase vars; Docker/README setup is reproducible (judges use their own Supabase project or a shared read-only demo project).

### Exit gate

- A reviewer can run the prototype from the README.
- All seven required deliverables are present.
- Documentation matches the actual implementation; no production-readiness or regulatory claims are made.

## Phase 9 — Presentation and Rehearsal

**Time:** 14:30-15:30  
**Goal:** Present the complete decision-support story clearly and on time.

### Suggested presentation flow

1. **Problem and stakes:** one shared cash pool, three separate provider balances (bKash/Nagad/Rocket), fragmented coordination.
2. **Users:** agent, field officer, provider operations, risk/review, and management.
3. **Live scenario:** unified balance view and hidden shortage (Scenario A).
4. **Decision value:** forecast, confidence, contributing signals, unusual-activity evidence, and plausible-benign explanation (Scenario B).
5. **Reliability:** stale/conflicting feed lowers confidence and suppresses anomaly flags; data-health indicator visible (Scenario C).
6. **Coordination:** route per hierarchy, assign, acknowledge, escalate, resolve, in-app notification, audit history (Scenario D).
7. **Architecture:** modular monolith, provider boundaries, Data Quality → engines → Alert/Case chain.
8. **Evidence:** show three+ measured metrics from `/metrics` or validation panel.
9. **Responsibility:** synthetic data, human review, false positives, RBAC, and prohibited actions.
10. **Limitations and next steps:** explicitly excluded scope (no real APIs, no fund movement, no Kafka/microservices).

### Actions

1. Rehearse at least twice with a timer and assigned speaker transitions.
2. Use a deterministic demo dataset and reset procedure.
3. Prepare backup screenshots or a short local recording for every critical screen.
4. Prepare concise answers for:
   - Why this is more than separate charts.
   - How shortage time is calculated.
   - Why an activity was flagged.
   - How false positives and low-quality data are handled.
   - How provider boundaries are enforced.
   - What the system deliberately cannot do.
5. Stop adding features.

### Exit gate

- The presentation fits the official time limit with a small buffer.
- Every speaker knows the next action and fallback.
- The live demo starts from a known state and ends with a visible resolution.

## Phase 10 — Final Buffer and Submission

**Time:** 15:30-16:00  
**Goal:** Protect the finished submission from last-minute regressions.

### Actions

1. Fix only critical failures: startup, broken demo path, incorrect output, unsafe wording, missing deliverable, or submission access.
2. Run the exact demo once; do not refactor.
3. Verify repository access, branch/commit, README, sample data, diagram, notes, metrics, slides, and environment example.
4. Confirm no secrets or real data are committed.
5. Submit early enough to recover from upload/network problems.
6. Keep the tested local build and backup media unchanged.

### Exit gate

- Submission receipt/link is confirmed.
- Repository and presentation permissions work from a non-owner view.
- The final checklist below is entirely checked or any omission is explicitly disclosed.

---

## 7. Milestone Control Board

| Deadline | Non-negotiable milestone | If missed |
|---|---|---|
| Hour 2:15 | Contracts, scenarios, wireframes, and architecture agreed | Stop UI polish; resolve contracts first |
| Hour 5 | Runnable dashboard with synthetic multi-provider data (3 providers) | Reduce to two providers and one agent; use local fixtures |
| Hour 7:30 | Forecast and explainable anomaly work | Simplify to deterministic rate forecast and one rule |
| Hour 10 | Confidence fallback, anomaly suppression, case lifecycle, RBAC | Drop filters, localization, and all optional views |
| Hour 12 | Integrated MVP passes full story | Freeze scope; only repair mandatory flow |
| Hour 13:30 | Metrics and safety/reliability evidence captured | Stop feature work; measure the stable build |
| Hour 14:30 | All required repository documents complete | Assign one owner and use concise factual notes |
| Hour 15:30 | Rehearsed presentation and backup ready | Use screenshots/recording; do not risk untested fixes |
| Hour 16 | Submission confirmed | Submit the last stable build, not a late experimental version |

## 8. Requirement-to-Demo Traceability

| Requirement / System Design feature | Implementation evidence | Demo moment |
|---|---|---|
| Shared cash + separate provider balances [M] | Ledger & Aggregation; dashboard cards per bKash/Nagad/Rocket | Open dashboard |
| Upcoming shortage + confidence [M] | Liquidity Forecasting Engine | Trigger Scenario A |
| Unusual activity + evidence [M] | Anomaly Detection Engine with structured evidence | Open alert detail |
| Plausible-benign explanation [E] | `plausible_benign_explanation` on AnomalyFlag | Read alert wording |
| Careful language [M] | Copy review + responsible-design note | Read alert wording |
| Recipient, owner, next step, lifecycle [M/E] | Alert & Case Management + routing rules | Scenario D workflow |
| Missing/late/conflicting fallback [M] | Data Quality & Confidence Engine | Toggle fault injection (Scenario C) |
| Anomaly suppression under bad data [E] | Degraded-data flow in §3.3 | Scenario C — no false risk alert |
| Data health per provider [E] | Feed status on ProviderBalance | Dashboard health indicators |
| EN + Bangla/Banglish explanations [R/E] | Explainability & Localization Service | Toggle language on alert |
| Provider boundaries [M/E] | Auth & Provider-Boundary Guard (JWT RBAC) | Login as Provider A ops; verify B case blocked |
| Meaningful analytics [M] | Liquidity + Anomaly engines (not decorative) | Architecture + metrics slides |
| Auditability [E] | Append-only AuditEvent log | Review case history |
| ≥3 validation metrics [M/E] | `/metrics` or validation panel | Metrics slide |
| Safety/privacy/human review [M] | Synthetic IDs, advisory outputs, no automated action | Responsible-design slide |

## 9. Final Submission Checklist

### Prototype

- [ ] At least **two** provider contexts visibly and logically separate (target: three — bKash, Nagad, Rocket).
- [ ] Shared physical cash and each provider balance displayed together — **never blended**.
- [ ] A provider or shared-cash shortage projected with approximate timing and confidence indicator.
- [ ] At least one unusual pattern detected with evidence and `plausible_benign_explanation`.
- [ ] Alert wording says `unusual` or `requires review`, never confirmed fraud.
- [ ] Per-provider data-health indicator visible.
- [ ] Bad input lowers confidence, suppresses high-confidence anomaly flags, and shows data-issue advisory.
- [ ] One alert shows recipient, owner, next step, and full lifecycle (ack → escalate → resolve).
- [ ] EN + at least one Bangla/Banglish explanation from the same structured alert object.
- [ ] Alert and case changes traceable in audit log.
- [ ] Provider-boundary RBAC enforced (cross-provider case access blocked).

### Quality and evidence

- [ ] At least three numeric metrics include method, sample size, and limitation.
- [ ] Normal, anomalous, missing, stale, and conflicting scenarios were tested.
- [ ] Core interactions are responsive at the documented data volume.
- [ ] High-impact alerts expose reason, evidence, and uncertainty.
- [ ] False-positive risk and human-review boundaries are documented.

### Guardrails

- [ ] Only synthetic/mock/anonymized data is used.
- [ ] No production API, real identity, account, balance, or credential is used.
- [ ] No PIN, OTP, password, private key, or secret is collected or committed.
- [ ] No wallet conversion, real settlement, or unauthorized financial action exists.
- [ ] No automatic blocking, accusation, or final fraud decision exists.
- [ ] No claim of regulatory approval or production readiness exists.
- [ ] Provider data and authority boundaries remain explicit.

### Deliverables

- [ ] Working prototype.
- [ ] Source repository with README, setup steps (Supabase + migrations), `.env.example`, and sample data/seed script.
- [ ] Architecture diagram with all modular monolith components, analytics, monitoring, boundaries, and coordination flow.
- [ ] Data and simulation note (generation, fault injection, scenarios A–D).
- [ ] Validation evidence (`/metrics` or panel: precision/recall, forecast error or lead time, latency, etc.).
- [ ] Responsible-design note.
- [ ] Final presentation with a rehearsed live demo and backup.

## 10. Definition of Success

At Hour 16, the strongest achievable submission is not the one with the most screens. It is the one that reliably demonstrates this complete chain from System Design §0:

> Separate provider data and shared cash → Data Quality tagging → forward liquidity insight → explainable unusual-activity evidence (with plausible-benign context) → visible uncertainty → provider-aware routing and human ownership → traceable resolution → validation metrics.

Every feature, module, document, metric, and presentation choice should strengthen that connected **liquidity → anomaly → coordination** story.
