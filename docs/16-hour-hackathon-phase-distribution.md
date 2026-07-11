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

**Data/API contract:** [`schema.md`](./schema.md) is the implementation baseline. Source observations and analytical outputs are append-only; current dashboard values are derived. Analytical **alerts are immutable evidence records**, while **cases are separate mutable human-workflow records** opened only for important alerts.

**Demo surfaces (minimum, intentionally thin):**
- Agent/unified dashboard sufficient to exercise data and intelligence endpoints.
- Alert detail and case coordination console sufficient to exercise workflow endpoints.
- Provider-scoped access enforced per role; no time is reserved for a high-polish frontend or broad component library.

**Demo & validation:**
- Configurable fault injection for stale/conflicting feeds (Scenario C).
- Activity/audit trail for every case transition.
- At least three measured validation metrics (see Phase 6).
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
| Frontend | Thin React (or Next.js) + Tailwind demo surfaces only — enough to exercise dashboard/scenario and alert/case APIs |
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

## 4. Solo Ownership and Current Baseline

This plan assumes **one person owns the entire project**. The existing data/API, coordination/security and analytics boundaries remain useful as internal module boundaries, but they are no longer people or handoff points. Work is serialized in dependency order inside one modular monolith:

```text
Scenario/generator and normalized input
        ↓
Data quality → liquidity/anomaly engines
        ↓ ResultEnvelope
Persistence/API adapter → AlertCandidate
        ↓
Immutable alert → routing → mutable case workflow
        ↓
Audit/notifications → validation metrics → thin demo UI
```

### Repository state verified before replanning

| Area | Current state | Solo implication |
|---|---|---|
| Data/API foundation | FastAPI modules, migrations `001`/`002`/`003`/`005`, adapters, fixtures, OpenAPI and data/intelligence routes exist | Verify and finish seams; do not rebuild foundation |
| Analytics | Confidence, forecast and anomaly modules exist; **23 analytics tests pass** when run from repository root | Integrate engines into persisted/API flow and extend degraded/evaluation coverage |
| Coordination/security | Auth/alert/case/notification/audit scaffolds and fixtures exist; **128 coordination tests pass** from `backend/` | Replace honest `501` services with runtime persistence and register routers |
| Contracts | Fixture verification passes for `ResultEnvelope`, derived `AlertCandidate`, validation payload and dashboard response | Preserve contracts; consolidate ownership rather than redesigning them |
| Database | Top-level `004_coordination.sql` and `006_security.sql` are pointer/placeholders; detailed coordination migration scaffolds exist separately and are unapplied | Promote/reconcile/apply them in serialized order and restore deferred FKs/views |
| Application composition | `app.main` includes data/intelligence routers but not coordination routers | Register coordination after runtime auth/services are ready |
| Test execution | Suites pass separately, but one unified pytest invocation fails because analytics imports `backend.*` while coordination imports `app.*` | Normalize package/test invocation during Phase 1 |
| Environment | Current interpreter is missing `pydantic-settings`, so full app import fails until requirements are installed in the intended environment | Establish reproducible environment before runtime work |
| Frontend | Next.js default starter page only | Build one thin demonstration surface after backend integration |

### Solo responsibilities

The single owner is responsible for all schema sections, all 48 proposed endpoints, all analytics, all tests, the thin frontend, documentation, rehearsal and submission. Keep internal packages separated:

- `backend/analytics/**`: pure generator/quality/forecast/anomaly/evaluation logic.
- `backend/app/member1/**`: data, simulation, ledger, analytics persistence and read APIs.
- `backend/app/coordination/**`: auth, alerts, routing, cases, notifications and audit.
- `backend/app/core/**`, migrations and `app/main.py`: shared composition/infrastructure.
- `frontend/**`: thin demo only.

### Endpoint scope

| Group | MVP endpoint work |
|---|---|
| Reference/dashboard | Providers, areas, outlets, dashboard, transactions and balance history |
| Simulation/ingestion/quality | Scenario run/reset/faults, ingestion batches, current/history quality |
| Intelligence | Liquidity run/read, anomaly run/read/evidence |
| Auth/profile | Demo login, current user and locale preference |
| Alerts/cases | Alert list/detail/explanations; case open/list/detail/timeline/assignment/acknowledge/escalate/resolve/notes/review |
| Notification/audit | Notification list/read and case audit events |
| Operations/evidence | `/health`, `/metrics`, validation results |

#### Solo endpoint inventory

| Group | Endpoints |
|---|---|
| Reference/outlets | `GET /api/v1/providers`; `GET /api/v1/areas`; `GET /api/v1/outlets`; `GET /api/v1/outlets/{outletId}` |
| Dashboard/ledger | `GET /api/v1/outlets/{outletId}/dashboard`; `GET /api/v1/outlets/{outletId}/transactions`; `GET /api/v1/outlets/{outletId}/balances/history` |
| Simulation | `GET /api/v1/simulations/scenarios`; `POST /api/v1/simulations/runs`; `GET /api/v1/simulations/runs/{runId}`; `POST /api/v1/simulations/runs/{runId}/reset`; `POST /api/v1/simulations/runs/{runId}/faults`; `PATCH /api/v1/simulations/runs/{runId}/faults/{faultId}` |
| Ingestion/quality | `POST /api/v1/ingestion/batches`; `GET /api/v1/outlets/{outletId}/data-quality`; `GET /api/v1/outlets/{outletId}/data-quality/history` |
| Liquidity | `GET /api/v1/outlets/{outletId}/liquidity-projections`; `POST /api/v1/internal/analytics/liquidity/run` |
| Anomaly | `GET /api/v1/outlets/{outletId}/anomaly-flags`; `GET /api/v1/anomaly-flags/{flagId}`; `POST /api/v1/internal/analytics/anomalies/run` |
| Auth/profile | `POST /api/v1/auth/demo-login`; `GET /api/v1/me`; `PATCH /api/v1/me/preferences` |
| Alerts | `GET /api/v1/alerts`; `GET /api/v1/alerts/{alertId}`; `GET /api/v1/alerts/{alertId}/explanations`; `POST /api/v1/alerts/{alertId}/cases` |
| Cases | `GET /api/v1/cases`; `GET /api/v1/cases/{caseId}`; `GET /api/v1/cases/{caseId}/timeline`; `POST /api/v1/cases/{caseId}/assignments`; `POST /api/v1/cases/{caseId}/acknowledge`; `POST /api/v1/cases/{caseId}/escalate`; `POST /api/v1/cases/{caseId}/resolve`; `POST /api/v1/cases/{caseId}/notes`; `POST /api/v1/cases/{caseId}/review` |
| Notifications/audit | `GET /api/v1/notifications`; `POST /api/v1/notifications/{notificationId}/read`; `GET /api/v1/cases/{caseId}/audit-events` |
| Operations/evidence | `GET /health`; `GET /metrics`; `GET /api/v1/validation/results` |
| Stretch only | `POST /api/v1/outlets/{outletId}/what-if-runs`; `GET /api/v1/what-if-runs/{whatIfRunId}`; `GET /api/v1/outlets/{outletId}/relationships`; `GET /api/v1/outlets/{outletId}/nearby-support-options`; `POST /api/v1/cases/{caseId}/support-requests` |

Stretch endpoints—what-if, relationships, nearby support and support requests—remain frozen until the Hour 12 gate. No endpoint may transfer, convert, settle, refill, recover, reverse, block, freeze, accuse, or make a fraud decision.

### Solo serialization rules

1. Preserve `ResultEnvelope → AlertCandidate → Alert → Case` as four distinct contracts even though one person owns all of them.
2. Complete and test the producer before implementing its consumer.
3. Keep analytical calculations out of routes/workflow services and keep case fields out of analytical results.
4. Apply migrations in numeric dependency order; never leave parallel-owner placeholder/pointer migrations in the final path.
5. At each checkpoint, commit/tag or record the tested state before moving forward.
6. Fix blockers in the current phase only. Queue non-blocking polish for Phase 5 or cut it.
7. Do not start stretch scope before the complete Hour 12 MVP gate passes.

## 5. Sixteen-Hour Schedule at a Glance

| Clock | Duration | Phase | Serialized solo focus | Required result |
|---|---:|---|---|---|
| 00:00-02:15 | 2:15 | 1. API/schema contract and scaffolding | Reproduce environment/tests, audit current implementation, normalize imports/composition/migrations/contracts | One runnable baseline, unified test command, frozen solo backlog |
| 02:15-05:00 | 2:45 | 2. Foundation APIs | Finish ingestion/simulation seams; promote coordination migrations; implement demo auth/scopes; register protected empty queues | Persisted synthetic foundation plus working auth/provider boundaries |
| 05:00-07:30 | 2:30 | 3. Intelligence-to-alert chain | Wire engines → persistence → `AlertCandidate`; implement immutable alerts, explanations, routing and initial case | Scenario A/B analytical result becomes an explainable routed case |
| 07:30-10:00 | 2:30 | 4. Safe coordinated response | Finish degraded data behavior, case lifecycle, notification, audit, idempotency/concurrency and RBAC/RLS | Scenarios C/D work safely end to end |
| 10:00-12:00 | 2:00 | 5. Integration and MVP freeze | Build thin UI, compose full app, seed/reset and run A–D regression | Complete demo-ready release candidate |
| 12:00-13:30 | 1:30 | 6. Validation and observability | Held-out analytics, API latency, explanation/audit/quality coverage, safety/security scans | Three or more signed-off metrics with evidence |
| 13:30-14:30 | 1:00 | 7. Documentation | Reconcile README, OpenAPI, schema, data/analytics, responsible design and limitations | All seven submission deliverables present and truthful |
| 14:30-15:30 | 1:00 | 8. Presentation and rehearsal | Prepare/reset/backup, rehearse twice and verify every displayed result | Timed story-driven demo with fallback |
| 15:30-16:00 | 0:30 | 9. Final buffer and submission | Critical checks only, final demo, permissions and submission | Frozen tested build submitted |

Total: **16 hours**.

### Solo workload control

The first four phases are intentionally dense, so each has a strict internal sequence and cut rule. The current codebase already contains contracts, analytics modules and coordination scaffolds; the solo plan spends time on runtime completion and integration rather than recreating those artifacts.

| Phase | Difficulty | Do not exceed | First cut if late |
|---|---:|---|---|
| 1 | 4/5 | 2:15 | Historical owner-doc cleanup; preserve runtime/test consolidation |
| 2 | 5/5 | 2:45 | Nonessential read filters and UI shells |
| 3 | 5/5 | 2:30 | Combined/extra alert variants; retain one forecast and one anomaly rule |
| 4 | 5/5 | 2:30 | Review sophistication and extra routing/locales; retain security/lifecycle/audit |
| 5 | 4/5 | 2:00 | Visual polish and optional filters |
| 6 | 4/5 | 1:30 | Extra metrics beyond the strongest required three |
| 7 | 3/5 | 1:00 | Long prose; keep concise factual deliverables |
| 8 | 3/5 | 1:00 | Extra slides/video |
| 9 | 1/5 | 0:30 | Nothing mandatory; fix only submission blockers |

---

## 6. Detailed Phase Instructions

## Phase 1 — API/Schema Contract and Executable Scaffolding

**Time:** 00:00-02:15  
**Goal:** Convert the existing multi-owner scaffold into one reproducible solo baseline before adding features.

### Serialized work

| Clock | Solo task | Checkpoint output |
|---|---|---|
| 00:00-00:30 | Create/activate the intended backend environment, install `backend/requirements.txt`, verify Node dependencies, and record exact Python/Node/Postgres commands. | Full app imports or an exact dependency blocker is recorded |
| 00:30-01:00 | Normalize test package paths/config so coordination and analytics run from one documented root command; preserve the currently verified 128 coordination and 23 analytics tests. | One unified backend test command; fixture verifier still passes |
| 01:00-01:30 | Audit `TODO(owner=...)`, `501` services, router registration, migration placeholders/sub-migrations, deferred FKs/views and default frontend. Convert them into one ordered solo blocker list. | Current-state matrix with `done`, `scaffolded`, `runtime missing`, `stretch` |
| 01:30-02:00 | Revalidate `ResultEnvelope`, `AlertCandidate`, validation payload, schema/API invariants, case transitions, role scopes and Scenario A-D expectations. Freeze contracts rather than redesigning them. | Frozen contracts, scenario expectations and test fixtures |
| 02:00-02:15 | Freeze the nine-phase backlog, cut list, exact demo sequence and checkpoint commands. | `P1-SOLO` reproducible baseline and serialized execution board |

### Deliverables

- Reproducible environment and one documented backend test command.
- Current implementation/TODO/501/migration/UI inventory.
- Frozen OpenAPI/schema/contracts and canonical dashboard, analytics, alert and case fixtures.
- One numeric migration path with former owner-specific scaffolds reconciled.
- Existing coordination and analytics tests plus fixture verification passing.
- Thin single-page demo plan covering dashboard/scenario and alert/case controls.
- Written 3-5 minute demo sequence and explicit guardrail list.

### Exit gate

- Every mandatory capability maps to an endpoint, engine output, table/view, test, minimal demo control or document.
- A `ResultEnvelope` produces a valid `AlertCandidate` through the existing verified adapter.
- Full app import, test invocation and pending runtime seams are reproducible from the solo setup notes.
- Alerts preserve analytical evidence; cases alone own receiver, owner, notes, transitions, and resolution.
- No planned schema or endpoint transfers money, merges wallets, blocks/freezes users, exposes real identities, or declares fraud.

## Phase 2 — Foundation APIs

**Time:** 02:15-05:00  
**Goal:** Finish the runtime foundation in dependency order: database and synthetic input first, then identity/scope, then protected reads.

### Serialized work

| Clock | Solo task | Checkpoint output |
|---|---|---|
| 02:15-03:00 | Reconcile/promote coordination identity/workflow migration scaffolds into the numeric migration path; restore deferred `app_users` FKs and prepare security/view dependencies without breaking existing `001`-`005`. | Clean pending migration plan; local/Supabase check succeeds |
| 03:00-03:40 | Finish ingestion normalization persistence, deterministic seed/reset behavior, simulation idempotency and data-quality round trip using existing generator/contracts. | Synthetic normal/A-C data persists and replays deterministically |
| 03:40-04:20 | Implement demo identities, login, `/me`, locale preference and request scope dependency; replace the shared auth TODO and register coordination routers only after safe middleware is active. | Scoped demo authentication works across route groups |
| 04:20-05:00 | Implement protected empty alert/case queues, safe same-shape 404 behavior, provider A/B denial tests and dashboard quality read; verify no blended total. | `P2-SOLO` persisted foundation and provider-boundary proof |

### Checkpoint at Hour 4

- Migrations apply in one order and are idempotent.
- Deterministic scenario/quality fixtures persist without cross-provider mixing.
- Demo authentication and scope dependency work; if not, stop and finish them before workflow routes.
- The unified backend suite remains green after each serialized slice.

### Exit gate at Hour 5

- One command starts the prototype (Docker or documented local setup); backend reads/writes **Supabase PostgreSQL**.
- The dashboard displays shared cash and **three separate** provider balances from generated data.
- Per-provider data-health state is visible.
- Synthetic scenarios can be selected or replayed deterministically; fault injection is toggleable.
- Demo authentication and provider/outlet authorization middleware work on both endpoint groups.
- Coordination routers are registered without any unauthenticated confidential read path.
- No real credentials, names, balances, accounts, or production APIs exist in the repository.

## Phase 3 — Intelligence-to-Alert Chain

**Time:** 05:00-07:30  
**Goal:** Complete the engine → persisted result → immutable alert → routed initial case chain and make every output explainable.

### Actions

| Clock | Solo task | Checkpoint output |
|---|---|---|
| 05:00-05:45 | Wire existing confidence, liquidity and anomaly modules into the internal run endpoints and persistence adapters. Verify separate shared-cash/provider projections, quality links, evidence and precision-preserving round trips. | Scenario A/B `ResultEnvelope`s persist and read correctly |
| 05:45-06:15 | Finish candidate gating/mapping: invalid or suppressed anomaly results cannot create risk candidates; actionable results retain confidence/evidence/benign context. | Persisted result → valid `AlertCandidate` trace |
| 06:15-07:00 | Replace alert-service `501`s with candidate validation, source links, deduplication, immutable alert persistence, EN + Bangla/Banglish render snapshots and routing. | Live candidate becomes one explainable alert |
| 07:00-07:30 | Implement initial case creation plus alert/case list/detail reads; add the smallest combined Scenario B path and regression tests. | `P3-SOLO` result → alert → routed case chain |

### Deliverables

- Working Liquidity Forecasting Engine with confidence and contributing signals.
- Working Anomaly Detection rule with evidence and `plausible_benign_explanation`.
- Immutable alert records linked to their projection/flag evidence, with routed cases created only for important alerts.
- EN + at least one Bangla/Banglish explanation from templates.
- At least one combined liquidity/anomaly alert.
- Initial analytics evaluation output.
- Former coordination alert-service `501`s on the Phase 3 path are removed.

### Exit gate

- A judge can see what may run short, approximately when, why the alert exists, how uncertain it is, and what safe human step is recommended.
- The unusual-activity alert never claims fraud.
- Known synthetic positives trigger; normal cases remain mostly unflagged.

## Phase 4 — Safe Coordinated Response

**Time:** 07:30-10:00  
**Goal:** Demonstrate reliability under imperfect data and a traceable human workflow.

### Actions

| Clock | Solo task | Checkpoint output |
|---|---|---|
| 07:30-08:10 | Harden stale/missing/conflicting/insufficient-sample behavior; show last trusted balance plus conflict evidence, lower/unavailable forecasts, widened bounds and retained suppressed anomaly evaluations. | Scenario C safe analytical/read behavior |
| 08:10-09:10 | Replace case/notification/audit `501`s: assignment, acknowledge, escalate, resolve, notes, review, notification/read, timeline and audit, all with legal transitions. | Scenario D workflow works locally |
| 09:10-09:40 | Add durable idempotency, optimistic version checks, atomic workflow+audit writes and safe same-shape errors. | Duplicate/stale mutation tests pass |
| 09:40-10:00 | Apply RBAC/RLS/grants and run provider/outlet/area leakage tests across data and workflow routes. | `P4-SOLO` secured Scenarios C/D |

### Deliverables

- Low-confidence/stale/conflicting data states with visible per-provider data health.
- Anomaly suppression under degraded data (Scenario C).
- Provider-aware routing, ownership, and RBAC enforcement.
- In-app notification on alert assignment.
- Visible end-to-end case history and final status.
- Tests for invalid state changes and cross-provider leakage.
- No MVP coordination service still returns an intentional `501`.

### Exit gate at Hour 10

- Scenario C visibly lowers confidence, widens bands, and suppresses high-confidence anomaly flags — shows data-issue advisory instead.
- Scenario D can be completed entirely through the UI/API without editing data manually.
- Alert creation, routing, assignment, acknowledgement, escalation, notes, and resolution are traceable in audit log.
- Provider-boundary RBAC verified (Provider A user cannot access Provider B case).

## Phase 5 — Integration and MVP Freeze

**Time:** 10:00-12:00  
**Goal:** Compose one stable release candidate and add only the frontend needed to demonstrate the complete backend/analytics story.

### Actions

| Clock | Solo task | Checkpoint output |
|---|---|---|
| 10:00-10:30 | Compose all routers/migrations, clean startup/shutdown, seed/reset, OpenAPI and environment commands; remove obsolete owner-only runtime seams. | One-command backend release candidate |
| 10:30-11:20 | Replace the Next.js starter with one thin responsive page: login/role switch, shared/provider cards, quality/forecast/anomaly evidence, fault/scenario controls, alert explanation and case actions/timeline. | Complete demonstrable UI path, minimal styling |
| 11:20-12:00 | Run deterministic A-D end-to-end regression: no blended totals, confidence/evidence, suppression, alert immutability, lifecycle, denial, idempotency, concurrency and safe language. Fix blockers only. | `P5-SOLO` tested demo-ready release candidate |

### Deliverables

- Stable integrated MVP.
- Complete story covering scenarios A through D, whether as separate fixtures or one sequence.
- Feature freeze and tagged/demo-ready commit.
- Unified backend tests, frontend lint/build and fixture verification pass from documented commands.

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

## Phase 6 — Validation, Reliability, and Safety QA

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

| Clock | Solo task | Evidence output |
|---|---|---|
| 12:00-12:35 | Run frozen held-out analytics; calculate anomaly precision/recall/FPR and forecast error or lead time with seed, version, sample size and limitations. | Analytical metric payloads and raw summaries |
| 12:35-13:00 | Measure average/p95 API latency, data-quality handling rate and explanation coverage at documented volume. | Performance/reliability evidence |
| 13:00-13:20 | Measure case transition, notification, audit, idempotency/concurrency and provider-denial correctness. | Workflow/security evidence |
| 13:20-13:30 | Persist/serve metrics unchanged; run secret, real-data, unsafe-action, prohibited-language and provider-boundary scans. | `P6-SOLO` signed-off evidence pack |

### Exit gate

- At least three metrics have numeric results, sample sizes, methods, and limitations.
- The demo survives bad-data tests without crashing or producing misleading confidence.
- All high-impact alerts expose evidence and uncertainty.
- No critical safety, privacy, or provider-boundary issue remains.

## Phase 7 — Submission Documentation

**Time:** 13:30-14:30  
**Goal:** Complete every required non-code deliverable.

### Actions

| Clock | Solo task | Output |
|---|---|---|
| 13:30-13:50 | Update root/backend/frontend README with exact environment, migration, seed/reset, test, run and demo commands; regenerate/check OpenAPI. | Reproducible source-repository guide |
| 13:50-14:05 | Finalize architecture/data flow and schema deviation notes; remove stale claims that owner-specific placeholders are intentionally unimplemented. | Architecture/setup documentation |
| 14:05-14:20 | Write data/simulation and analytics/validation methodology with seeds, splits, metrics, false-positive risk and limitations. | Data and validation notes |
| 14:20-14:30 | Write responsible-design note and assemble links/screenshots/deliverables. | `P7-SOLO` complete submission documentation |

### Exit gate

- A reviewer can run the prototype from the README.
- All seven required deliverables are present.
- Documentation matches the actual implementation; no production-readiness or regulatory claims are made.

## Phase 8 — Presentation and Rehearsal

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

| Clock | Solo task | Output |
|---|---|---|
| 14:30-14:45 | Freeze slides/narration, deterministic reset, backup screenshots/responses and Q&A answers. | Rehearsal-ready package |
| 14:45-15:00 | Rehearsal 1: run the complete story with a timer; record only blocking timing/demo issues. | First timing and issue list |
| 15:00-15:10 | Fix narration/reset/backup issues only; do not add features. | Corrected presentation |
| 15:10-15:25 | Rehearsal 2 from a clean state, including fallback. | Passing timed rehearsal |
| 15:25-15:30 | Freeze build, slides, spoken wording and backup media. | `P8-SOLO` final presentation package |

### Exit gate

- The presentation fits the official time limit with a small buffer.
- The solo presenter knows every transition, next action and fallback.
- The live demo starts from a known state and ends with a visible resolution.

## Phase 9 — Final Buffer and Submission

**Time:** 15:30-16:00  
**Goal:** Protect the finished submission from last-minute regressions.

### Actions

| Clock | Solo task | May fix |
|---|---|---|
| 15:30-15:40 | Run critical tests, fixture verification, frontend build, migrations/check, secret scan and non-owner permission check. | Only startup, correctness, safety, access or missing-deliverable blockers |
| 15:40-15:50 | Run the exact demo once on the frozen build and compare metrics/expected outputs. | Only a reproducible demo blocker; rerun affected checks |
| 15:50-16:00 | Submit, confirm receipt/link and preserve the tested local build/backups unchanged. | Submission/access issue only |

### Exit gate

- Submission receipt/link is confirmed.
- Repository and presentation permissions work from a non-owner view.
- The final checklist below is entirely checked or any omission is explicitly disclosed.

---

## 7. Milestone Control Board

| Deadline | Non-negotiable milestone | If missed |
|---|---|---|
| Hour 2:15 | Environment/app/tests are reproducible; current runtime gaps are inventoried; migrations/contracts/scenarios are frozen for solo work | Stop feature work; resolve environment, import and contract blockers first |
| Hour 5 | Synthetic data/quality APIs, demo auth, provider boundaries and scoped empty workflow queues run on one database path | Keep all three providers; cut nonessential reads and UI work |
| Hour 7:30 | Engine → persisted result → immutable explainable alert → routed initial case works | Keep one deterministic forecast and anomaly rule; cut combined/extra alert variants |
| Hour 10 | Confidence fallback, anomaly suppression, case lifecycle, RBAC | Drop filters, localization, and all optional views |
| Hour 12 | Integrated MVP passes full story | Freeze scope; only repair mandatory flow |
| Hour 13:30 | Metrics and safety/reliability evidence captured | Stop feature work; measure the stable build |
| Hour 14:30 | All required repository documents complete | Shorten prose; keep setup, evidence, safety and limitations factual |
| Hour 15:30 | Rehearsed presentation and backup ready | Use screenshots/recording; do not risk untested fixes |
| Hour 16 | Submission confirmed | Submit the last stable build, not a late experimental version |

## 8. Requirement-to-Demo Traceability

| Requirement / System Design feature | Implementation evidence | Demo moment |
|---|---|---|
| Shared cash + separate provider balances [M] | Ledger/dashboard endpoints and no blended-total invariant | Open dashboard |
| Upcoming shortage + confidence [M] | Forecast engine persisted/exposed through projection endpoints | Trigger Scenario A |
| Unusual activity + evidence [M] | Anomaly engine, evidence records and alert source links | Open alert detail |
| Plausible-benign explanation [E] | Flag field preserved through result, candidate and alert render | Read alert wording |
| Careful language [M] | Template/render and prohibited-language tests + responsible-design note | Read alert wording |
| Recipient, owner, next step, lifecycle [M/E] | Alert/case/routing endpoints | Scenario D workflow |
| Missing/late/conflicting fallback [M] | Quality engine plus fault/quality/read endpoints | Toggle fault injection (Scenario C) |
| Anomaly suppression under bad data [E] | Suppression result enforced by candidate adapter | Scenario C — no false risk alert |
| Data health per provider [E] | Data-quality endpoints and dashboard read model | Dashboard health indicators |
| EN + Bangla/Banglish explanations [R/E] | Template/render and alert explanation endpoints | Toggle language on alert |
| Provider boundaries [M/E] | JWT/RBAC/RLS and scope contract | Login as Provider A ops; verify B case blocked |
| Meaningful analytics [M] | Quality, liquidity and anomaly engines exposed through APIs | Architecture + metrics slides |
| Auditability [E] | Append-only audit and timeline endpoints | Review case history |
| ≥3 validation metrics [M/E] | Frozen evaluation calculations served by `/metrics` | Metrics slide |
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
