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
- Agent/unified dashboard sufficient to exercise Member 1 data and intelligence endpoints.
- Alert detail and case coordination console sufficient to exercise Member 2 workflow endpoints.
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

## 4. Role Allocation

This plan assumes **exactly three people working simultaneously**. Members 1 and 2 are both backend engineers, split by endpoint ownership rather than frontend/backend layers. Member 3 retains the Intelligence/Quality lane. The UI is deliberately thin: Member 1 builds only the dashboard/demo controls required to exercise Member 1 endpoints; Member 2 builds only the alert/case controls required to exercise Member 2 endpoints.

| Member | Permanent lane | Owns | Does not own |
|---|---|---|---|
| **Member 1 — Data & Intelligence APIs** | Reference data, simulations, ingestion, ledger, dashboard reads, data quality, analytics persistence/adapters, health and metrics delivery | `schema.md` §§6.1–6.4, 7–9, 11–12; assigned endpoints below; minimal dashboard and scenario controls | Auth/case workflow, analytical formulas, polished frontend |
| **Member 2 — Coordination & Security APIs** | Authentication profiles/scopes, immutable alerts, localization snapshots, routing, cases, assignments, notifications, audit and provider-boundary enforcement | `schema.md` §§6.5–6.6, 10, 13, 15; assigned endpoints below; minimal alert/case controls | Ledger/analytics calculations, data ingestion, polished frontend |
| **Member 3 — Intelligence/Quality** | Analytics and validation logic | Scenario generator, confidence engine, liquidity forecast, anomaly detection, expected outputs, automated tests, evaluation and metric calculations | HTTP routes, database migrations, UI implementation |

**Member 1 is the API integration owner** and owns the shared OpenAPI file, application composition, Supabase connection, startup/deployment path, and runnable main branch. Member 2 owns authorization policy and case-state correctness. Member 3 owns analytical semantics and expected results.

### Endpoint ownership

The following is the complete proposed endpoint inventory from `schema.md`. An owner implements the route, validation, persistence adapter, authorization hook, tests, and minimal demo control for that endpoint.

#### Member 1 — Data & Intelligence APIs

| Group | Endpoints |
|---|---|
| Reference/outlets | `GET /api/v1/providers`; `GET /api/v1/areas`; `GET /api/v1/outlets`; `GET /api/v1/outlets/{outletId}` |
| Dashboard/ledger | `GET /api/v1/outlets/{outletId}/dashboard`; `GET /api/v1/outlets/{outletId}/transactions`; `GET /api/v1/outlets/{outletId}/balances/history` |
| Simulation | `GET /api/v1/simulations/scenarios`; `POST /api/v1/simulations/runs`; `GET /api/v1/simulations/runs/{runId}`; `POST /api/v1/simulations/runs/{runId}/reset`; `POST /api/v1/simulations/runs/{runId}/faults`; `PATCH /api/v1/simulations/runs/{runId}/faults/{faultId}` |
| Ingestion/quality | `POST /api/v1/ingestion/batches`; `GET /api/v1/outlets/{outletId}/data-quality`; `GET /api/v1/outlets/{outletId}/data-quality/history` |
| Liquidity | `GET /api/v1/outlets/{outletId}/liquidity-projections`; `POST /api/v1/internal/analytics/liquidity/run` |
| Anomaly | `GET /api/v1/outlets/{outletId}/anomaly-flags`; `GET /api/v1/anomaly-flags/{flagId}`; `POST /api/v1/internal/analytics/anomalies/run` |
| Operations/evidence | `GET /health`; `GET /metrics`; `GET /api/v1/validation/results` |
| Stretch only | `POST /api/v1/outlets/{outletId}/what-if-runs`; `GET /api/v1/what-if-runs/{whatIfRunId}`; `GET /api/v1/outlets/{outletId}/relationships`; `GET /api/v1/outlets/{outletId}/nearby-support-options` |

#### Member 2 — Coordination & Security APIs

| Group | Endpoints |
|---|---|
| Auth/profile | `POST /api/v1/auth/demo-login`; `GET /api/v1/me`; `PATCH /api/v1/me/preferences` |
| Alerts | `GET /api/v1/alerts`; `GET /api/v1/alerts/{alertId}`; `GET /api/v1/alerts/{alertId}/explanations`; `POST /api/v1/alerts/{alertId}/cases` |
| Cases | `GET /api/v1/cases`; `GET /api/v1/cases/{caseId}`; `GET /api/v1/cases/{caseId}/timeline`; `POST /api/v1/cases/{caseId}/assignments`; `POST /api/v1/cases/{caseId}/acknowledge`; `POST /api/v1/cases/{caseId}/escalate`; `POST /api/v1/cases/{caseId}/resolve`; `POST /api/v1/cases/{caseId}/notes`; `POST /api/v1/cases/{caseId}/review` |
| Notifications/audit | `GET /api/v1/notifications`; `POST /api/v1/notifications/{notificationId}/read`; `GET /api/v1/cases/{caseId}/audit-events` |
| Stretch only | `POST /api/v1/cases/{caseId}/support-requests` |

Member 1 has more routes because many are bounded reads or simulation controls. Member 2 has fewer but more stateful/security-sensitive writes involving transitions, idempotency, audit, notification and RLS. The workload is balanced by implementation difficulty, not raw endpoint count.

No endpoint may transfer, convert, settle, refill, recover, reverse, block, freeze, accuse, or make a fraud decision.

### Cross-member synchronization contract

```text
Member 3 pure engine output
        ↓ (versioned ResultEnvelope + expected tests)
Member 1 validates, persists and exposes the analytical result
        ↓ (versioned AlertCandidate; no case fields)
Member 2 deduplicates and persists the immutable alert,
routes it, and opens/manages a case when required
```

- `ResultEnvelope` contains engine version, input window, quality-assessment IDs, confidence, evidence, and output-specific fields.
- `AlertCandidate` contains alert type, outlet/provider scope, severity, source result IDs, structured explanation variables, and `requires_case`.
- Member 2 never recalculates a projection/anomaly. Member 1 never creates assignments or changes case state. Member 3 never writes HTTP/database integration code.

### Non-overlap rules

1. A task has exactly one owner. Reviewers may comment but do not co-implement it.
2. Members 1 and 2 edit different route modules, migrations, service modules, tests, and minimal UI surfaces according to the endpoint tables above.
3. Member 1 owns analytical-result persistence and read APIs but does not implement Member 3's formulas or Member 2's workflow.
4. Member 2 owns alert/case persistence and RBAC but does not query raw provider data except through Member 1's versioned service contract.
5. Member 3 supplies pure functions, expected outputs, and evaluation tests; Member 3 does not wire HTTP routes, database repositories, or UI components.
6. Contract changes go through Member 1's OpenAPI/contract package and must preserve the previous fixture until both consumers have moved.
7. At each phase boundary, commit or tag the named deliverables before dependent work begins.

### Schema readiness rule

`schema.md` is already defined before Hour 0. The merged Phase 1 reviews, trims, and freezes its MVP subset; it does not redesign the data model. Member 1 owns data/analytics migrations and OpenAPI composition, Member 2 owns identity/workflow/security migrations, and Member 3 owns analytical semantics and expected values. Any later schema change requires a short decision record and coordinated contract version bump.

## 5. Sixteen-Hour Schedule at a Glance

| Clock | Duration | Phase | Member 1 — Data & Intelligence APIs | Member 2 — Coordination & Security APIs | Member 3 — Intelligence/Quality |
|---|---:|---|---|---|---|
| 00:00-02:15 | 2:15 | 1. API/schema contract and scaffolding | Data/intelligence API contract, migrations and app skeleton | Auth/workflow API contract, migrations and RBAC matrix | Engine contracts, scenarios and executable expected results |
| 02:15-05:00 | 2:45 | 2. Foundation APIs | Reference, simulation, ingestion, ledger, dashboard and quality APIs | Demo auth, access scopes, alert/case persistence skeleton | Generator, fault injection, quality engine and tests |
| 05:00-07:30 | 2:30 | 3. Intelligence-to-alert chain | Analytics persistence, run/read APIs and `AlertCandidate` adapter | Immutable alerts, explanations, routing and initial cases | Liquidity and anomaly engines with evidence |
| 07:30-10:00 | 2:30 | 4. Safe coordinated response | Fault controls, degraded read models, data/analytics authorization | Lifecycle, assignments, notes, notification, audit and provider RBAC | Suppression behavior, adversarial and leakage tests |
| 10:00-12:00 | 2:00 | 5. Integration and MVP freeze | Compose/deploy data and intelligence endpoints; thin dashboard | Integrate secure workflow endpoints; thin case console | End-to-end A–D regression and safety suite |
| 12:00-13:30 | 1:30 | 6. Validation and observability | Health, metrics delivery, data/API performance evidence | Workflow/RBAC/audit reliability evidence | Held-out analytics evaluation and metric calculations |
| 13:30-14:30 | 1:00 | 7. Documentation | API/schema/setup and data-flow documentation | Auth/workflow/security and responsible-design documentation | Data simulation, analytics methods, metrics and limitations |
| 14:30-15:30 | 1:00 | 8. Presentation and rehearsal | Data flow and Scenario A/C demo | Coordination and Scenario D demo | Scenario B, metrics, uncertainty and limitations |
| 15:30-16:00 | 0:30 | 9. Final buffer and submission | Build/API/repository submission check | Auth/workflow/access/permissions check | Data/tests/metrics/secret scan |

Total: **16 hours**.

### Workload balance check

Complexity is estimated on a 1–5 scale **within each time block**. Scores measure implementation effort, not business importance. No member differs by more than one point from another member in the same phase.

| Phase | Member 1 | Member 2 | Member 3 | Balance rationale |
|---|---:|---:|---:|---|
| 1 | 5 | 5 | 5 | Two endpoint/migration packages and one executable engine contract package |
| 2 | 5 | 5 | 5 | Data APIs, coordination foundation, and generator/quality foundation |
| 3 | 5 | 5 | 5 | Analytics adapter, alert platform, and two tested engines |
| 4 | 5 | 5 | 5 | Degraded data APIs, secure lifecycle, and adversarial quality work |
| 5 | 4 | 4 | 4 | Endpoint integration, workflow integration, and full regression |
| 6 | 4 | 4 | 4 | Platform performance, workflow reliability, and analytics evidence |
| 7 | 3 | 3 | 3 | Three separate technical documentation packages |
| 8 | 3 | 3 | 3 | Data demo, workflow demo, and evidence presentation |
| 9 | 1 | 1 | 1 | Three bounded final checks |

If a member finishes early, they review another lane or prepare their next-phase fixture; they do not take over another member's implementation. If a task exceeds its estimate, cut its `Should/Stretch` portion before moving ownership.

---

## 6. Detailed Phase Instructions

## Phase 1 — API/Schema Contract and Executable Scaffolding

**Time:** 00:00-02:15  
**Goal:** Finish the first block with runnable service scaffolds, frozen endpoint ownership, migration boundaries, and executable analytical contracts—not only planning artifacts.

### Simultaneous assignments

| Owner | Independent work | Timed output |
|---|---|---|
| **Member 1** | Review and freeze the Member 1 endpoint list; create the modular-monolith/backend skeleton, shared OpenAPI file, Supabase connection/config contract, and separate migration scaffolds for providers/areas/outlets, simulation/ingestion, ledger, data quality, analytics, validation, and read views. Define canonical `ResultEnvelope` ingestion, `AlertCandidate` submission, and validation-metric payload interfaces. | 00:45 endpoint map; 01:30 service + migration scaffold; `P1-M1` runnable data/intelligence API skeleton by 02:15 |
| **Member 2** | Review and freeze the Member 2 endpoint list; scaffold auth/profile, alert, case, notification, and audit route modules plus identity/workflow migrations. Define case transition matrix, provider/outlet access matrix, standard error/idempotency/concurrency behavior, explanation fields, and the `AlertCandidate` consumer contract. | 00:45 endpoint map; 01:30 route + migration scaffold; `P1-M2` runnable coordination/security API skeleton by 02:15 |
| **Member 3** | Freeze Scenarios A–D, deterministic seeds, fault configurations, forecast/anomaly/confidence formulas, held-out labels, metric definitions, and pure-function `ResultEnvelope` examples. Add executable contract tests for normal, shortage, repeated-amount, and stale/conflicting inputs. | 00:45 acceptance matrix; 01:30 result fixtures; `P1-M3` executable engine contract package by 02:15 |

### Synchronization checkpoints

1. **00:45:** confirm endpoint ownership, MVP cuts, schema exceptions, and prohibited actions.
2. **01:15:** Member 3 publishes `ResultEnvelope` v1; Member 1 freezes its persistence adapter shape.
3. **01:30:** Member 1 publishes `AlertCandidate` v1; Member 2 freezes alert/case consumption.
4. **02:00:** freeze OpenAPI v1, migration filenames/table ownership, fixtures, transition matrix, and scenario expectations.
5. **02:15:** all three packages run or validate independently; no unresolved contract mismatch remains.

### Deliverables

- Reviewed `schema.md` with an explicit MVP table/endpoint list and decision record for any exception.
- Runnable backend skeleton with separate Member 1 and Member 2 route/service/repository modules.
- Frozen OpenAPI v1 and canonical dashboard, analytics, alert, and case fixtures.
- Non-overlapping migration ownership; no shared migration file edited by both backend members.
- Executable analytics contract tests and deterministic Scenario A–D expected outputs.
- Thin demo surface plan: dashboard/scenario controls owned by Member 1; alert/case controls owned by Member 2.
- Written 3–5 minute demo sequence and explicit guardrail list.

### Exit gate

- Every mandatory capability maps to an owned endpoint, engine output, table/view, test, minimal demo control, or document.
- Member 3 results can pass Member 1 validation, and Member 1 alert candidates can pass Member 2 validation using fixtures.
- Alerts preserve analytical evidence; cases alone own receiver, owner, notes, transitions, and resolution.
- No planned schema or endpoint transfers money, merges wallets, blocks/freezes users, exposes real identities, or declares fraud.

## Phase 2 — Foundation APIs

**Time:** 02:15-05:00  
**Goal:** Produce working data and coordination API foundations backed by Supabase while Member 3 delivers deterministic inputs and quality results.

### Simultaneous assignments

| Owner | Independent implementation | Prerequisite | Completion handoff |
|---|---|---|---|
| **Member 1** | Apply reference, simulation/ingestion, ledger, and minimum quality migrations. Implement provider/area/outlet reads, scenario run/reset/fault routes, ingestion batch route, append-only balance/transaction persistence, dashboard/transaction/balance-history reads, current quality read, and a thin dashboard/scenario control page. | `P1-M1`; generated payloads from `P1-M3` | `P2-M1` working data-foundation endpoints |
| **Member 2** | Apply identity/access-scope and alert/case skeleton migrations. Implement demo login, `/me`, locale preference, provider/outlet scope middleware, empty authorized alert/case queues, and route-level 404/error behavior that does not leak cross-provider existence. Build only a thin case queue/detail shell against fixtures. | `P1-M2`; scope contract from `P1-M1` | `P2-M2` working auth/workflow foundation |
| **Member 3** | Implement deterministic synthetic generator, fault injection and Data Quality & Confidence Engine as pure modules. Emit `data_quality_assessments`/issues `ResultEnvelope`s and add labeled forecast/anomaly inputs with unit tests for normal, malformed and degraded feeds. | `P1-M3`; frozen ingestion/quality shapes from `P1-M1` | `P2-M3` generator + quality package |

### Integration checkpoint at Hour 4

- Member 3 hands quality payloads to Member 1; Member 1 persists/exposes them without copying engine logic.
- Member 1 supplies outlet/provider identifiers and a versioned authorization lookup contract to Member 2; Member 2 does not query Member 1 repositories directly.
- Member 2 demonstrates that Provider A cannot list Provider B's empty workflow scope even before real alerts exist.
- Contract mismatches are fixed by the owner of the producing contract or module.
- Member 1 verifies append-only observations and confirms the dashboard never returns a blended `total_balance`.

### Exit gate at Hour 5

- One command starts the prototype (Docker or documented local setup); backend reads/writes **Supabase PostgreSQL**.
- The dashboard displays shared cash and **three separate** provider balances from generated data.
- Per-provider data-health state is visible.
- Synthetic scenarios can be selected or replayed deterministically; fault injection is toggleable.
- Demo authentication and provider/outlet authorization middleware work on both endpoint groups.
- No real credentials, names, balances, accounts, or production APIs exist in the repository.

## Phase 3 — Intelligence-to-Alert Chain

**Time:** 05:00-07:30  
**Goal:** Complete the engine → persisted result → immutable alert → routed initial case chain and make every output explainable.

### Actions

| Owner | Independent implementation | Prerequisite | Completion handoff |
|---|---|---|---|
| **Member 1** | Apply analytics migrations; implement liquidity/anomaly run and read endpoints, analytics-run/result persistence, quality links, evidence reads, and the `AlertCandidate` producer. Add only forecast/anomaly panels needed to inspect endpoint output. | `P2-M1`; callable engines from `P2-M3`; `AlertCandidate` contract from `P1` | `P3-M1` intelligence endpoints + alert-candidate adapter |
| **Member 2** | Apply alert, source-link, template, routing, and initial-case migrations. Consume `AlertCandidate`; implement deduplication, immutable alert/explanation persistence, alert list/detail/explanation routes, routing, `POST /api/v1/alerts/{alertId}/cases`, and case list/detail. Add only the alert/case controls needed for the demo. | `P2-M2`; candidate fixtures from `P1-M1` | `P3-M2` routed alert/case endpoints |
| **Member 3** | Implement separate shared-cash/provider burn-rate forecasts with quality-assessment links and confidence bands, plus one near-identical-amount anomaly rule with evidence and suppression disposition. Cover zero burn, replenishment, minimum samples, provider isolation, threshold edges and benign demand. | `P2-M3`; data-access input contract from `P2-M1` | `P3-M3` tested analytics engines |

**Dependency:** Member 1 uses `P1-M3` expected results until `P3-M3` is ready. Member 2 uses frozen `AlertCandidate` fixtures until Member 1's adapter is live. At 06:30 Member 3 hands engines to Member 1; at 06:50 Member 1 hands persisted candidate IDs to Member 2. Each owner replaces only their own stub.

### Deliverables

- Working Liquidity Forecasting Engine with confidence and contributing signals.
- Working Anomaly Detection rule with evidence and `plausible_benign_explanation`.
- Immutable alert records linked to their projection/flag evidence, with routed cases created only for important alerts.
- EN + at least one Bangla/Banglish explanation from templates.
- At least one combined liquidity/anomaly alert.
- Initial analytics evaluation output.

### Exit gate

- A judge can see what may run short, approximately when, why the alert exists, how uncertain it is, and what safe human step is recommended.
- The unusual-activity alert never claims fraud.
- Known synthetic positives trigger; normal cases remain mostly unflagged.

## Phase 4 — Safe Coordinated Response

**Time:** 07:30-10:00  
**Goal:** Demonstrate reliability under imperfect data and a traceable human workflow.

### Actions

| Owner | Independent implementation | Prerequisite | Completion handoff |
|---|---|---|---|
| **Member 1** | Complete fault enable/disable, quality-history, degraded dashboard/projection/anomaly reads and per-endpoint data-scope authorization. Ensure conflicting balances expose last trusted values plus conflict evidence, and suppressed flags remain measurable but never produce an anomaly `AlertCandidate`. | `P3-M1`; degraded envelopes from `P3-M3` | `P4-M1` safe degraded-data APIs |
| **Member 2** | Complete case assignments, acknowledge/escalate/resolve, notes, review, notifications, timeline and audit endpoints plus status history, optimistic locking, idempotency, JWT/RBAC, RLS/grants and cross-provider denial. Complete only the minimal workflow controls for these routes. | `P3-M2`; provider/outlet scope contract from `P2-M1` | `P4-M2` secure coordination APIs |
| **Member 3** | Harden missing/stale/conflicting/insufficient-sample checks. Apply confidence reduction and band widening; retain suppressed evaluations, prevent anomaly alert candidates, and emit data-quality advisory fixtures. Add endpoint-independent adversarial cases plus Scenario C and provider-leakage expectations. | `P3-M3`; result behavior from `P3-M1` and denial contract from `P3-M2` | `P4-M3` degraded-data engine + adversarial suite |

**Dependency:** Member 1 uses Member 3's frozen degraded-result fixtures until the hardened engine lands. Member 2 uses Member 1's stable outlet/provider scope lookup from Phase 2. At 09:15 both endpoint owners publish secured builds; Member 3 runs the same adversarial matrix against both without editing either implementation.

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

## Phase 5 — Integration and MVP Freeze

**Time:** 10:00-12:00  
**Goal:** Compose both endpoint groups and Member 3's engines into one stable backend-heavy product story with only the UI needed to demonstrate it.

### Actions

| Owner | Independent implementation | Prerequisite | Completion handoff |
|---|---|---|---|
| **Member 1** | Compose the application, migrations, Supabase connection, seed/reset, Docker/local startup and Member 1 route modules. Replace data/intelligence fixtures in the thin dashboard, stabilize filters/error responses, and publish the release-candidate runtime. Fix only Member 1 endpoint/integration defects. | `P4-M1`, engines from `P4-M3`, auth middleware contract from `P4-M2` | `P5-M1` runnable release candidate + data demo |
| **Member 2** | Replace workflow fixtures with live alert/case/notification/audit endpoints; finish localized explanation toggle, dashboard-alert-to-case navigation, clean-session login and authorization on every Member 2 route. Fix only coordination/security defects. | `P4-M2`, live candidate IDs from `P4-M1` | `P5-M2` secure workflow demo |
| **Member 3** | Run automated A–D end-to-end regression across both endpoint groups: forecasts, evidence, degraded suppression, alert immutability, lifecycle, provider isolation, no blended totals, case concurrency and safe-language scan. Fix only engine/test-owned defects. | `P4-M3`; Phase 5 release-candidate and secured-route checkpoints; `schema.md` §13 | `P5-M3` MVP regression report |

**Integration order:** Member 1 publishes a release candidate at 11:00. Member 2 integrates only through frozen service/OpenAPI contracts. Member 3 independently validates that same build. Each endpoint owner accepts only reproducible defects in their own routes until the Hour 12 gate.

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

| Owner | Independent validation work | Prerequisite | Evidence ID |
|---|---|---|---|
| **Member 1** | Apply validation/read-model persistence; add structured logs, `/health`, `/metrics`, latency instrumentation and quality-event counts for Member 1 routes. Benchmark average/p95 data/analytics API latency, analytical-result delivery, ingestion reliability and clean setup/migrations. Persist/serve Member 3 metric payloads without recalculating them. | `P5-M1`, metric shape from `P5-M3`; `schema.md` §§11–12 | `P6-M1` data/API performance evidence |
| **Member 2** | Measure alert explanation coverage, case transition correctness, notification delivery, audit completeness, idempotency/concurrency behavior and cross-provider denial for every Member 2 route. Capture safe-language and workflow evidence. | `P5-M2`, adversarial matrix from `P5-M3` | `P6-M2` workflow/security reliability evidence |
| **Member 3** | Freeze held-out labeled data; populate ground-truth/metric shapes and measure forecast error/lead time, anomaly precision/recall/false-positive rate and degraded-input handling. Run secret/real-data/unsafe-action scans and publish signed-off metric payloads to Member 1. | `P5-M3`; metric interface from `P1-M1`; `schema.md` §11 | `P6-M3` analytics/security evidence |

Member 1 only persists/serves Member 3's analytical metric payload; Member 1 does not recalculate it. Member 2 owns workflow/explanation coverage metrics and does not alter engine results.

### Exit gate

- At least three metrics have numeric results, sample sizes, methods, and limitations.
- The demo survives bad-data tests without crashing or producing misleading confidence.
- All high-impact alerts expose evidence and uncertainty.
- No critical safety, privacy, or provider-boundary issue remains.

## Phase 7 — Submission Documentation

**Time:** 13:30-14:30  
**Goal:** Complete every required non-code deliverable.

### Actions

| Owner | Independent documentation work | Prerequisite | Output ID |
|---|---|---|---|
| **Member 1** | Write exact setup/run/migration/seed/environment instructions, OpenAPI usage, data/intelligence endpoint guide, data-flow architecture, performance evidence and demo reset steps. | `P6-M1` | `P7-M1` API/schema/setup docs |
| **Member 2** | Document auth scopes, RLS/RBAC, alert-vs-case separation, routing/lifecycle endpoints, auditability, safe explanation behavior and responsible-design boundaries. | `P6-M2` | `P7-M2` workflow/security/responsibility docs |
| **Member 3** | Write data-generation methodology, deterministic scenarios, validation split, forecast/anomaly/confidence methods, metrics, false-positive risk and analytical limitations. | `P6-M3` | `P7-M3` data/analytics evidence docs |

**Assembly:** Member 1 links the three owned documents and confirms commands/OpenAPI against the release candidate. Content corrections return to the original owner; no one silently rewrites another member's evidence.

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

| Owner | Independent preparation | Prerequisite | Live responsibility |
|---|---|---|---|
| **Member 1** | Validate reset/build/backup; finalize the architecture/API slides and backup captures for dashboard, feed health and forecasts. | `P7-M1` | Present system/API design and demonstrate Scenarios A and C |
| **Member 2** | Finalize auth/provider-boundary, alert/case, audit and responsibility slides plus backup captures. | `P7-M2` | Demonstrate Scenario D and explain security/coordination boundaries |
| **Member 3** | Recheck displayed numbers and prepare forecast, anomaly, confidence, false-positive, metric and limitation answers. | `P7-M3` | Demonstrate Scenario B and present analytics evidence/limitations |

Run two full-team rehearsals at approximately 14:45 and 15:10. Rehearsal is the only shared activity; preparation and artifact ownership remain separate. Stop adding features.

### Exit gate

- The presentation fits the official time limit with a small buffer.
- Every speaker knows the next action and fallback.
- The live demo starts from a known state and ends with a visible resolution.

## Phase 9 — Final Buffer and Submission

**Time:** 15:30-16:00  
**Goal:** Protect the finished submission from last-minute regressions.

### Actions

| Owner | Final non-overlapping check | May fix |
|---|---|---|
| **Member 1** | Release commit/tag, repository access, startup, migrations, `.env.example`, OpenAPI, deployment and actual submission/upload. | Only build/data/API/submission blockers |
| **Member 2** | Demo login, provider-boundary denial, alert/case lifecycle, notifications, audit trail, wording and presentation permissions. | Only auth/workflow/security blockers |
| **Member 3** | Sample data, deterministic reset outputs, tests, metrics, provider-boundary checks, and final secret/real-data scan. | Only analytics/test/data blockers |

At 15:45, Member 1 runs the exact demo once using the frozen build while Members 2 and 3 check their own evidence. Do not refactor or exchange endpoint ownership. Submit early enough to recover from access/network problems and keep the tested local build unchanged.

### Exit gate

- Submission receipt/link is confirmed.
- Repository and presentation permissions work from a non-owner view.
- The final checklist below is entirely checked or any omission is explicitly disclosed.

---

## 7. Milestone Control Board

| Deadline | Non-negotiable milestone | If missed |
|---|---|---|
| Hour 2:15 | Both API skeletons run; endpoint/migration ownership, OpenAPI, engine results, alert-candidate contract, scenarios and fixtures are frozen | Stop all non-contract work; resolve schema/interface mismatches first |
| Hour 5 | Data/quality APIs, thin dashboard, demo auth and provider-scoped empty workflow queues run on synthetic data | Keep all three providers; cut nonessential reads and UI styling |
| Hour 7:30 | Engine → persisted result → immutable explainable alert → routed initial case works | Keep one deterministic forecast and anomaly rule; cut combined/extra alert variants |
| Hour 10 | Confidence fallback, anomaly suppression, case lifecycle, RBAC | Drop filters, localization, and all optional views |
| Hour 12 | Integrated MVP passes full story | Freeze scope; only repair mandatory flow |
| Hour 13:30 | Metrics and safety/reliability evidence captured | Stop feature work; measure the stable build |
| Hour 14:30 | All required repository documents complete | Each member shortens only their owned document to concise factual notes |
| Hour 15:30 | Rehearsed presentation and backup ready | Use screenshots/recording; do not risk untested fixes |
| Hour 16 | Submission confirmed | Submit the last stable build, not a late experimental version |

## 8. Requirement-to-Demo Traceability

| Requirement / System Design feature | Implementation evidence | Demo moment |
|---|---|---|
| Shared cash + separate provider balances [M] | Member 1 ledger/dashboard endpoints | Open dashboard |
| Upcoming shortage + confidence [M] | Member 3 forecast engine → Member 1 projection endpoints | Trigger Scenario A |
| Unusual activity + evidence [M] | Member 3 anomaly engine → Member 1 evidence endpoints | Open alert detail |
| Plausible-benign explanation [E] | Member 3 flag field → Member 1 result → Member 2 alert render | Read alert wording |
| Careful language [M] | Member 2 template/render checks + responsible-design note | Read alert wording |
| Recipient, owner, next step, lifecycle [M/E] | Member 2 alert/case/routing endpoints | Scenario D workflow |
| Missing/late/conflicting fallback [M] | Member 3 quality logic → Member 1 fault/quality/read endpoints | Toggle fault injection (Scenario C) |
| Anomaly suppression under bad data [E] | Member 3 suppression result enforced by Member 1 candidate adapter | Scenario C — no false risk alert |
| Data health per provider [E] | Member 1 data-quality endpoints and dashboard read model | Dashboard health indicators |
| EN + Bangla/Banglish explanations [R/E] | Member 2 template/render and alert explanation endpoints | Toggle language on alert |
| Provider boundaries [M/E] | Member 2 JWT/RBAC/RLS with Member 1 scope contract | Login as Provider A ops; verify B case blocked |
| Meaningful analytics [M] | Member 3 engines exposed through Member 1 APIs | Architecture + metrics slides |
| Auditability [E] | Member 2 append-only audit and timeline endpoints | Review case history |
| ≥3 validation metrics [M/E] | Member 3 calculations served by Member 1 `/metrics` | Metrics slide |
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
