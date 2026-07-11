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

This plan assumes **exactly three people working simultaneously**. Each person owns a different implementation surface so two people never edit or implement the same feature. Collaboration happens through versioned contracts and explicit handoffs, not shared ownership.

| Member | Permanent lane | Owns | Does not own |
|---|---|---|---|
| **Member 1 — Product/UI** | Product decisions, frontend, localization, demo and presentation | Screen flows, React components, UI state, alert wording/templates, accessibility, screenshots and slides | Database, API implementation, analytical formulas |
| **Member 2 — Platform/Workflow** | Backend, persistence, security and integration | Supabase migrations, ingestion, ledger, APIs, case lifecycle, audit log, JWT/RBAC, startup/deployment | Frontend components, forecast/anomaly algorithms |
| **Member 3 — Intelligence/Quality** | Analytics, data quality, synthetic data, testing and metrics | Scenario generator, confidence engine, liquidity forecast, anomaly detection, automated tests, evaluation and `/metrics` calculations | UI layout, database/API ownership |

**Member 2 is the integration owner** and owns shared schema/API versions and the runnable main branch. Member 1 approves user-visible semantics; Member 3 approves analytics fields and expected outputs. A downstream task may depend on another member's earlier deliverable, but no member waits idle: every phase gives all three members independent work based on already frozen inputs or fixtures.

### Non-overlap rules

1. A task has exactly one owner. Reviewers may comment but do not co-implement it.
2. Member 1 consumes APIs and analytics through fixtures/contracts; Member 1 does not patch backend logic to unblock the UI.
3. Member 2 exposes and persists analytical results; Member 2 does not reimplement Member 3's formulas.
4. Member 3 supplies pure functions, expected outputs, and tests; Member 3 does not wire UI components or database routes.
5. Contract changes go through Member 2 and must preserve the previous fixture until all consumers have moved.
6. At each phase boundary, commit or tag the named deliverables before dependent work begins.

## 5. Sixteen-Hour Schedule at a Glance

| Clock | Duration | Phase | Member 1 — Product/UI | Member 2 — Platform/Workflow | Member 3 — Intelligence/Quality |
|---|---:|---|---|---|---|
| 00:00-00:45 | 0:45 | 1. Scope lock | Story, screens, wording guardrails | Stack, repo and integration rules | Scenario and metric acceptance criteria |
| 00:45-02:15 | 1:30 | 2. Contracts | Wireframes and UI fixtures | Schemas, API contract and migrations | Analytics interfaces and scenario specification |
| 02:15-05:00 | 2:45 | 3. Foundations | Dashboard and case shells | Ingestion, ledger, persistence and APIs | Generator, data-quality engine and tests |
| 05:00-07:30 | 2:30 | 4. Decision intelligence | Forecast/anomaly UI and localized copy | Alert creation, routing and result persistence | Liquidity and anomaly engines |
| 07:30-10:00 | 2:30 | 5. Safe response | Case actions, history and notification UI | Lifecycle, audit log and RBAC | Degraded-data behavior and security/quality tests |
| 10:00-12:00 | 2:00 | 6. Integration freeze | Complete demo UX and responsive polish | Live wiring, startup and integration fixes | End-to-end fixtures, regression and safety suite |
| 12:00-13:30 | 1:30 | 7. Validation | UX/accessibility QA and evidence capture | Performance, health and reliability instrumentation | Analytics evaluation and failure-mode validation |
| 13:30-14:30 | 1:00 | 8. Documentation | README usage, screenshots and slide skeleton | Architecture, setup and data/simulation note | Metrics, responsible-design note and limitations |
| 14:30-15:30 | 1:00 | 9. Rehearsal | Demo lead and presentation timing | Reset/backup operator and architecture Q&A | Evidence/safety presenter and result verification |
| 15:30-16:00 | 0:30 | 10. Submission | Visual/presentation check | Build, repository and submission check | Data, tests, metrics and secret scan |

Total: **16 hours**.

### Workload balance check

Complexity is estimated on a 1–5 scale **within each time block**. Scores measure implementation effort, not business importance. No member differs by more than one point from another member in the same phase.

| Phase | Member 1 | Member 2 | Member 3 | Balance rationale |
|---|---:|---:|---:|---|
| 1 | 2 | 2 | 2 | Three bounded definition artifacts |
| 2 | 3 | 4 | 4 | UI fixtures offset the heavier schema/algorithm specifications |
| 3 | 5 | 5 | 5 | Frontend foundation, backend foundation, and data/quality foundation |
| 4 | 4 | 4 | 5 | Rich intelligence UI, alert platform, and two tested analytical engines |
| 5 | 4 | 5 | 5 | Workflow UI, secure lifecycle, and degraded-data/adversarial work |
| 6 | 4 | 5 | 4 | UI integration, deployable integration, and full regression |
| 7 | 3 | 4 | 4 | UX evidence, platform evidence, and analytics evidence |
| 8 | 3 | 3 | 3 | Three separate documentation packages |
| 9 | 3 | 3 | 3 | Demo, technical fallback, and evidence presentation |
| 10 | 1 | 1 | 1 | Three bounded final checks |

If a member finishes early, they review another lane or prepare their next-phase fixture; they do not take over another member's implementation. If a task exceeds its estimate, cut its `Should/Stretch` portion before moving ownership.

---

## 6. Detailed Phase Instructions

## Phase 1 — Alignment and Scope Lock

**Time:** 00:00-00:45  
**Goal:** Remove ambiguity and agree on one demonstrable story.

### Actions

| Owner | Independent work | Output ID |
|---|---|---|
| **Member 1** | Freeze the three primary views, the 3–5 minute Scenarios A–D demo sequence, visible terminology, and `Must/Should/Stretch` UI backlog. | `P1-M1` story and screen map |
| **Member 2** | Freeze stack (including Supabase), repository conventions, branch/integration policy, module boundaries, environment variables, and prohibited backend actions. | `P1-M2` technical charter |
| **Member 3** | Freeze scenario inputs/expected outcomes, analytical success conditions, minimum validation metrics, and safety assertions for stale/conflicting data and unusual activity. | `P1-M3` acceptance matrix |

**Final 10-minute checkpoint:** compare the three outputs only for contradictions. Member 2 records the agreed interfaces; owners retain their respective implementation areas.

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

| Owner | Independent work | Inputs | Output ID |
|---|---|---|---|
| **Member 1** | Produce low-fidelity dashboard, alert detail and case-flow wireframes. Create UI fixtures for loading/empty/error and `fresh/stale/missing/conflicting` states, plus EN/Bangla/Banglish copy keys. | `P1-M1`; field names requested from `P1-M3` | `P2-M1` wireframes + frontend fixtures |
| **Member 2** | Define provider-separated entities, OpenAPI/response contracts, routing fields and state transitions. Draft Supabase migrations, `.env.example`, and architecture diagram. | `P1-M2`, `P1-M3` acceptance fields | `P2-M2` schema/API v1 + migration draft |
| **Member 3** | Specify deterministic Scenarios A–D, fault toggles, thresholds, forecast/anomaly formulas, confidence rules and expected outputs. Export pure-function input/output examples matching API v1. | `P1-M3`; schema names from `P1-M2` | `P2-M3` scenario + analytics contract |

**Handoff order:** Member 2 publishes the schema skeleton by 01:15. Members 1 and 3 bind their fixtures/examples to it by 01:45. Member 2 freezes API v1 at 02:00 and uses the final 15 minutes for mismatch corrections.

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

### Simultaneous assignments

| Owner | Independent implementation | Prerequisite | Completion handoff |
|---|---|---|---|
| **Member 1** | Build the dashboard shell, shared-cash and separate provider cards, data-health states, alert list, alert-detail shell and case shell. Use only `P2-M1` fixtures; start visible-language and requirement-evidence notes. | `P2-M1`, API field names from `P2-M2` | `P3-M1` fixture-driven frontend |
| **Member 2** | Apply migrations; implement ingestion/normalization, Supabase connection, Ledger & Aggregation, read APIs, seed-import endpoint and a minimal JWT/provider-scope stub. Member 2 persists data but does not generate scenario logic. | `P2-M2` and sample payloads from `P2-M3` | `P3-M2` persisted foundation API |
| **Member 3** | Implement deterministic synthetic generator, fault injection and Data Quality & Confidence Engine as pure modules. Add labeled forecast/anomaly cases and unit tests for normal, malformed and degraded inputs. | `P2-M3`, entity shapes from `P2-M2` | `P3-M3` generator + quality package |

### Integration checkpoint at Hour 4

- Member 3 hands `P3-M3` payloads to Member 2; Member 2 imports them without copying generator logic.
- Member 2 exposes one live dashboard response; Member 1 swaps one fixture adapter to the live endpoint without changing the component model.
- Contract mismatches are fixed by the owner of the producing contract or module.

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

| Owner | Independent implementation | Prerequisite | Completion handoff |
|---|---|---|---|
| **Member 1** | Build forecast cards/bands, contributing-signal view, anomaly evidence panel and combined-alert presentation. Implement EN + Bangla/Banglish template rendering and safe recommended-action copy from structured fixtures. | `P3-M1`; final result shapes from `P2-M3` | `P4-M1` decision-intelligence UI |
| **Member 2** | Implement alert creation, provider/area routing, case persistence and endpoints that invoke Member 3's engine interfaces. Persist combined liquidity/anomaly results without altering their calculations. | `P3-M2`; callable interfaces from `P3-M3` | `P4-M2` routed-alert API |
| **Member 3** | Implement separate shared-cash/provider burn-rate forecasts with confidence bands and one near-identical-amount anomaly rule. Cover zero burn, replenishment, minimum samples, provider isolation, threshold edges and benign demand with tests. | `P3-M3`; data access adapter contract from `P3-M2` | `P4-M3` tested analytics engines |

**Dependency:** `P4-M2` may use the frozen expected outputs from `P2-M3` while `P4-M3` is being implemented. At 06:45, Member 3 replaces the stubs with the real package; Member 2 owns only the adapter. Member 1 switches from fixtures to `P4-M2` after that handoff.

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

| Owner | Independent implementation | Prerequisite | Completion handoff |
|---|---|---|---|
| **Member 1** | Implement case assignment/acknowledgement/escalation/resolution controls, notes, audit timeline and in-app notification UI. Add visible delayed/conflicting advisory states and validate localized situation/evidence/uncertainty/next-step copy. | `P4-M1`; lifecycle contract from `P4-M2` | `P5-M1` response-workflow UI |
| **Member 2** | Implement legal case transitions, ownership, notes, assignment notifications, append-only audit events and provider-scoped JWT/RBAC enforcement. Reject invalid transitions and cross-provider reads/writes. | `P4-M2`; provider fields from `P3-M2` | `P5-M2` secure workflow backend |
| **Member 3** | Harden missing/stale/conflicting/insufficient-sample checks. Apply confidence reduction and band widening; suppress new high-confidence anomalies for degraded providers and emit a data-issue advisory. Add state-transition fixtures, leakage tests and Scenario C assertions against Member 2's API. | `P4-M3`; test endpoint from `P4-M2` | `P5-M3` degraded-data engine + adversarial suite |

**Dependency:** Member 1 builds against the Phase 2 lifecycle fixture while `P5-M2` is underway. `P5-M3` depends on Member 2's Phase 4 test endpoint, not on unfinished Phase 5 RBAC. At 09:15, Member 2 publishes the secured API; Members 1 and 3 run their separate UI and adversarial checks against it.

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

| Owner | Independent implementation | Prerequisite | Completion handoff |
|---|---|---|---|
| **Member 1** | Replace all demo-path fixtures with live adapters; finalize urgency ordering, filters, responsive layout, formatting, uncertainty placement, localization toggle and dashboard → evidence → case navigation. | `P5-M1`, secured endpoints from `P5-M2` | `P6-M1` demo-ready frontend |
| **Member 2** | Wire all modules in the single deployable app; stabilize API errors, migrations, seed/reset command, Docker/local startup and clean-session authentication. Fix integration defects only in platform-owned code. | `P5-M2`, packages from `P4-M3`/`P5-M3` | `P6-M2` reproducible integrated build |
| **Member 3** | Create and run an automated A–D end-to-end regression suite, including expected forecasts, anomaly evidence, degraded-data suppression, lifecycle completion, provider isolation and safe-language scan. Fix only analytics/test-owned defects. | `P5-M3`, stable routes from `P5-M2` | `P6-M3` MVP regression report |

**Integration order:** Member 2 publishes a release candidate at 11:00. Member 1 and Member 3 independently validate that same build. Member 2 accepts only reproducible blocking defects until the Hour 12 gate.

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

| Owner | Independent validation work | Prerequisite | Evidence ID |
|---|---|---|---|
| **Member 1** | Run responsive, accessibility, navigation, localization and safe-wording QA. Measure alert explanation coverage and capture final screenshots from the release candidate. | `P6-M1`, `P6-M2` | `P7-M1` UX/safety evidence |
| **Member 2** | Add structured request logs, `/health`, latency instrumentation and data-quality event counts. Benchmark average/p95 API latency and verify clean Docker/setup, migrations, auth and audit persistence. | `P6-M2` | `P7-M2` platform/reliability evidence |
| **Member 3** | Freeze held-out labeled data; measure forecast error/lead time, anomaly precision/recall/false-positive rate and degraded-input handling. Run secret/real-data/unsafe-action scans and publish metric payloads for Member 2's `/metrics` endpoint. | `P6-M3`; metrics ingestion shape from `P6-M2` | `P7-M3` analytics/security evidence |

Member 2 only serves Member 3's metric payload; Member 2 does not recalculate it. Member 1 only presents captured evidence; Member 1 does not alter test results.

### Exit gate

- At least three metrics have numeric results, sample sizes, methods, and limitations.
- The demo survives bad-data tests without crashing or producing misleading confidence.
- All high-impact alerts expose evidence and uncertainty.
- No critical safety, privacy, or provider-boundary issue remains.

## Phase 8 — Submission Documentation

**Time:** 13:30-14:30  
**Goal:** Complete every required non-code deliverable.

### Actions

| Owner | Independent documentation work | Prerequisite | Output ID |
|---|---|---|---|
| **Member 1** | Write README problem/users, features, demo-scenario instructions and UI usage; add screenshots and build the presentation skeleton. | `P7-M1` | `P8-M1` product/demo docs |
| **Member 2** | Write exact setup/run/migration/seed/environment instructions; finalize the modular-monolith architecture diagram and integration/deployment notes. | `P7-M2` | `P8-M2` architecture/setup docs |
| **Member 3** | Write data/simulation methodology, deterministic scenarios, validation split, metrics/methods/limitations and responsible-design note covering human review, privacy, provider separation and prohibited actions. | `P7-M3` | `P8-M3` evidence/responsibility docs |

**Assembly:** Member 2 links the three owned documents and confirms commands against the release candidate. Content corrections return to the original owner; no one silently rewrites another member's evidence.

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

| Owner | Independent preparation | Prerequisite | Live responsibility |
|---|---|---|---|
| **Member 1** | Finalize slides, speaker transitions and backup screenshots; time the full story and trim narration. | `P8-M1` | Lead problem, users, UI and Scenarios A–D demo |
| **Member 2** | Validate deterministic reset, local build and backup path; prepare architecture, persistence, RBAC and deployment answers. | `P8-M2` | Operate reset/backup and explain platform boundaries |
| **Member 3** | Recheck every displayed number; prepare forecast, anomaly, confidence, false-positive, metrics and responsible-design answers. | `P8-M3` | Present analytical evidence, safety and limitations |

Run two full-team rehearsals at approximately 14:45 and 15:10. Rehearsal is the only shared activity; preparation and artifact ownership remain separate. Stop adding features.

### Exit gate

- The presentation fits the official time limit with a small buffer.
- Every speaker knows the next action and fallback.
- The live demo starts from a known state and ends with a visible resolution.

## Phase 10 — Final Buffer and Submission

**Time:** 15:30-16:00  
**Goal:** Protect the finished submission from last-minute regressions.

### Actions

| Owner | Final non-overlapping check | May fix |
|---|---|---|
| **Member 1** | Slides, screenshots, links, wording, responsive demo route and presentation permissions. | Only presentation/UI blockers |
| **Member 2** | Release commit/tag, repository access, startup, migrations, `.env.example`, deployment and actual submission/upload. | Only build/platform/submission blockers |
| **Member 3** | Sample data, deterministic reset outputs, tests, metrics, provider-boundary checks, and final secret/real-data scan. | Only analytics/test/data blockers |

At 15:45, Member 2 runs the exact demo once using the frozen build while Members 1 and 3 check their own evidence. Do not refactor or exchange ownership. Submit early enough to recover from access/network problems and keep the tested local build unchanged.

### Exit gate

- Submission receipt/link is confirmed.
- Repository and presentation permissions work from a non-owner view.
- The final checklist below is entirely checked or any omission is explicitly disclosed.

---

## 7. Milestone Control Board

| Deadline | Non-negotiable milestone | If missed |
|---|---|---|
| Hour 2:15 | Contracts, scenarios, wireframes, and architecture agreed | Stop UI polish; resolve contracts first |
| Hour 5 | Runnable dashboard with synthetic multi-provider data (3 providers) | Keep all three provider cards; simplify interactions and use local fixtures |
| Hour 7:30 | Forecast and explainable anomaly work | Simplify to deterministic rate forecast and one rule |
| Hour 10 | Confidence fallback, anomaly suppression, case lifecycle, RBAC | Drop filters, localization, and all optional views |
| Hour 12 | Integrated MVP passes full story | Freeze scope; only repair mandatory flow |
| Hour 13:30 | Metrics and safety/reliability evidence captured | Stop feature work; measure the stable build |
| Hour 14:30 | All required repository documents complete | Each member shortens only their owned document to concise factual notes |
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
