# System Design Document
## Multi-Provider Agent Liquidity & Coordination Platform
### Codex Community Hackathon — bKash presents SUST CSE Carnival 2026

---

## 0. Design Philosophy

This design targets **"complete and well-engineered," not "maximal."** Every component maps directly to a requirement in the problem statement (Sections 4, 7, 8, 10, 14). Nothing is added that:

- Implies real provider integration, settlement, or fund movement (explicitly out of scope).
- Adds infrastructure complexity (e.g., Kafka clusters, multi-region deployment, microservice sprawl) that a judge cannot verify or that doesn't improve the demonstrated story.
- Duplicates a capability another module already covers.

At the same time, the design avoids the trap of "three cards on a dashboard." Every module exists to make the **liquidity → anomaly → coordination** chain feel connected, explainable, and traceable end-to-end — which is explicitly what Section 12 (Success Criteria) rewards.

**Guiding principles:**
1. **One ledger, provider-separated.** Physical cash is shared; provider e-money balances are logically isolated. No code path merges or converts them.
2. **Every alert carries evidence + confidence.** No black-box scores.
3. **Every alert has an owner and a lifecycle.** Nothing ends as a passive toast notification.
4. **Data quality is a first-class citizen**, not an afterthought — degraded data must visibly degrade confidence, never silently produce a clean-looking dashboard.
5. **Advisory only.** The system recommends; a human acknowledges, escalates, or resolves.

---

## 1. System Architecture Overview

A modular monolith (single deployable backend, cleanly separated internal modules) is used instead of true microservices. This is intentional: it gives full engineering depth (clear module boundaries, independent responsibilities, testability) demonstrable in a hackathon timeframe, **without** operational overhead (service discovery, distributed tracing across network hops, multiple deploy pipelines) that a 2–4 day build cannot responsibly demonstrate as reliable. This keeps Section 8's "Reliability" and "Performance" expectations honest rather than aspirational.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                │
│                                                                            │
│   ┌──────────────────┐  ┌───────────────────┐  ┌───────────────────┐    │
│   │   Agent View      │  │  Operations /      │  │  Risk / Compliance│    │
│   │  (Web, mobile-    │  │  Coordinator View  │  │  Review View      │    │
│   │   responsive)     │  │                    │  │                   │    │
│   └────────┬──────────┘  └─────────┬──────────┘  └─────────┬─────────┘    │
│            │                       │                        │             │
│            └───────────────┬───────┴────────────┬───────────┘             │
│                             │  Role-based UI, shared component library     │
└─────────────────────────────┼──────────────────────────────────────────────┘
                              │  REST/GraphQL API (HTTPS, JWT auth)
┌─────────────────────────────▼──────────────────────────────────────────────┐
│                            APPLICATION LAYER (Backend)                     │
│                                                                              │
│  ┌────────────────────┐   ┌─────────────────────┐   ┌────────────────────┐ │
│  │ Provider Feed       │   │ Ledger &             │   │ Auth & Provider-   │ │
│  │ Ingestion &         │──▶│ Aggregation Service   │   │ Boundary Guard     │ │
│  │ Normalization        │   │ (cash + per-provider │   │ (RBAC)             │ │
│  │ (simulated feeds,   │   │  balances, read-only  │   └────────────────────┘ │
│  │  injectable delay/   │   │  unified view)        │                        │
│  │  inconsistency)      │   └──────────┬────────────┘                        │
│  └──────────┬───────────┘              │                                     │
│             │                          ▼                                     │
│             │              ┌──────────────────────┐                          │
│             │              │ Data Quality &        │                          │
│             │              │ Confidence Engine     │                          │
│             │              └──────────┬────────────┘                          │
│             │                         │                                       │
│             ▼                         ▼                                       │
│  ┌────────────────────┐   ┌──────────────────────┐                          │
│  │ Liquidity           │   │ Anomaly Detection     │                          │
│  │ Forecasting Engine  │   │ Engine                │                          │
│  │ (burn-rate /        │   │ (rule-based +         │                          │
│  │  time-series model) │   │  statistical checks)  │                          │
│  └──────────┬───────────┘   └──────────┬────────────┘                        │
│             │                          │                                     │
│             └────────────┬─────────────┘                                     │
│                           ▼                                                  │
│              ┌─────────────────────────────┐                                 │
│              │ Alert & Case Management      │                                 │
│              │ Service (routing, ownership, │                                 │
│              │ ack/escalate/resolve, audit) │                                 │
│              └──────────────┬────────────────┘                                │
│                              │                                                │
│              ┌───────────────┴───────────────┐                               │
│              ▼                                ▼                               │
│  ┌────────────────────────┐      ┌────────────────────────┐                  │
│  │ Explainability &        │      │ Coordination /          │                  │
│  │ Localization Service    │      │ Notification Layer      │                  │
│  │ (EN / Bangla / Banglish)│      │ (simulated in-app +     │                  │
│  │                         │      │  webhook notifications) │                  │
│  └────────────────────────┘      └────────────────────────┘                  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Monitoring & Observability (structured logs, metrics endpoint,       │  │
│  │  latency tracking, data-quality health checks)                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬──────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────────────┐
│                              DATA LAYER                                    │
│  ┌─────────────────────┐   ┌─────────────────────┐   ┌───────────────────┐ │
│  │ Relational DB        │   │ Cache (in-memory)    │   │ Audit / Event Log │ │
│  │ (Supabase PostgreSQL │   │  for live dashboard   │   │  (append-only)    │ │
│  │  agents, balances,   │   │  reads                │   │                   │ │
│  │  transactions, cases)│   │                       │   │                   │ │
│  └─────────────────────┘   └─────────────────────┘   └───────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Breakdown

### 2.1 Provider Feed Ingestion & Normalization
**Purpose:** Simulates independent bKash/Nagad/Rocket data feeds arriving into the system, since real integration is out of scope.

- Generates/accepts synthetic transaction and balance events per provider.
- Normalizes differing provider payload shapes into one internal schema *without merging provider identity or authority*.
- Supports **fault injection**: configurable late arrival, missing fields, conflicting balance snapshots — this directly feeds the Data Quality Engine and enables Scenario C (Section 11).

### 2.2 Ledger & Aggregation Service
**Purpose:** The single unified *view*, never a unified *wallet*.

- Maintains one shared physical-cash figure per agent/outlet.
- Maintains separate current-balance records per provider, per agent.
- Exposes a combined read-only view (cash + Provider A + Provider B + Provider C) for the dashboard — **aggregation is presentational, not custodial.**
- Enforces immutability: no endpoint here can transfer value between providers.

### 2.3 Data Quality & Confidence Engine
**Purpose:** Satisfies the mandatory "safe fallback when data is missing, late, or conflicting" requirement — treated as its own component rather than scattered error handling, because it feeds *both* downstream engines.

- Flags feeds as `fresh`, `stale`, `missing`, or `conflicting`.
- Emits a `confidence` modifier consumed by both the Liquidity and Anomaly engines.
- Drives visible UI states ("provider data delayed — estimate less certain") instead of silently defaulting to stale numbers.

### 2.4 Liquidity Forecasting Engine
**Purpose:** Predicts when shared cash or a specific provider balance will run out.

- Computes a rolling burn rate per provider and for shared cash (e.g., weighted recent cash-out velocity).
- Projects time-to-shortage with a confidence band (wider band when Data Quality Engine reports degraded input).
- Outputs: `{provider, projected_shortage_time, confidence, contributing_signal}`.

### 2.5 Anomaly Detection Engine
**Purpose:** Detects unusual transaction/balance behavior; evidence-first, never a bare score.

- Ships with **one fully-built detection category** (e.g., near-identical repeated amounts from a small account cluster — matches Section 11 Scenario B) plus architecture that cleanly supports adding more (velocity spikes, transaction splitting, circular activity) without redesign.
- Every flag carries: triggering signal(s), the raw evidence (e.g., "5 cash-outs of ~1,000 BDT from 3 accounts in 12 minutes"), a confidence/likelihood — **never a fraud label.**
- Explicitly outputs a `plausible_benign_explanation` field (e.g., "may reflect Eid demand") to satisfy the "distinguish operational spikes from patterns requiring review" objective.

### 2.6 Alert & Case Management Service
**Purpose:** The coordination backbone — turns detections into a trackable human workflow.

- Alert creation from Liquidity Engine and Anomaly Engine outputs.
- Routing rule engine: maps alert type + provider + area → responsible stakeholder (agent, field officer, provider ops, risk analyst) per the role hierarchy in Section 5.
- Case lifecycle: `open → acknowledged → (escalated) → resolved`, each transition timestamped and attributed.
- Case notes and evidence history retained per case (Section 4 optional objective, promoted here to core because it's cheap to build and directly strengthens Auditability).

### 2.7 Explainability & Localization Service
**Purpose:** Converts structured alert data into human language, in English, Bangla, and Banglish, from templates — not free-form generation, to keep output predictable and auditable.

- Template fills: situation, evidence, uncertainty, safe next step (mirrors the illustrative Bangla alerts in Section 11).
- Same underlying alert object renders in all three languages consistently — one source of truth.

### 2.8 Coordination / Notification Layer
**Purpose:** Delivers the alert to the routed stakeholder.

- Simulated in-app notification (primary, always demoable live).
- Optional webhook/email simulation stub to show the design *could* extend to real channels, without claiming real integration.

### 2.9 Auth & Provider-Boundary Guard
**Purpose:** Enforces Section 5/14's hardest constraint: providers must never see or act on another provider's confidential case data.

- Role-based access control: Agent / Field Officer / Provider-A Ops / Provider-B Ops / Risk Analyst / Management.
- Provider Ops roles are scoped so a Provider A user cannot open a Provider B case, even though both appear in the agent's combined dashboard.

### 2.10 Monitoring & Observability
**Purpose:** Turns Section 8's "Performance/Reliability" expectations into demonstrable evidence for Section 10's "Validation evidence" deliverable.

- Structured request logs, per-endpoint latency, and a `/health` + `/metrics` style summary.
- Data-quality event log (how often feeds were late/missing/conflicting during the demo run) — directly usable as a validation metric.

---

## 3. Data Flow

### 3.1 Narrative Flow (steady state)

1. **Ingestion** — Simulated provider feeds (transactions + balance snapshots) arrive continuously into the Ingestion layer, tagged by provider and agent/outlet.
2. **Quality tagging** — Each incoming batch is stamped `fresh/stale/missing/conflicting` by the Data Quality Engine before anything downstream touches it.
3. **Ledger update** — Valid events update the shared cash figure and the relevant provider's balance in the Ledger & Aggregation Service.
4. **Parallel analysis** — On each ledger update (or on a scheduled tick):
   - The **Liquidity Engine** recomputes burn rate and shortage projection for the affected provider and for shared cash.
   - The **Anomaly Engine** re-evaluates recent transactions against its detection rules for that agent/provider/area.
5. **Confidence adjustment** — Both engines pull the current data-quality confidence modifier and attach it to their output.
6. **Alert generation** — If a projection crosses a shortage threshold, or an anomaly rule fires, the Alert & Case Management Service creates a case, applies the routing rule, and assigns an owner.
7. **Explanation rendering** — The Explainability Service turns the case's structured evidence into an EN/Bangla/Banglish message.
8. **Delivery** — The Coordination layer pushes the alert to the assigned stakeholder's dashboard (and simulated notification channel).
9. **Human action** — The stakeholder acknowledges, adds case notes, escalates (if needed, to Risk/Compliance or up the hierarchy), or resolves.
10. **Audit** — Every transition (created → acknowledged → escalated → resolved) is appended to the immutable audit/event log.
11. **Feedback loop** — Resolved cases (especially those marked "false positive" by a reviewer) feed back into a metrics store used for the Anomaly Precision/Recall and False-Positive Rate validation metrics.

### 3.2 Flow Diagram

```
[Simulated Provider Feeds: bKash / Nagad / Rocket]
                 │
                 ▼
      [Ingestion & Normalization] ──────────► [Data Quality & Confidence Engine]
                 │                                          │
                 ▼                                          │ (confidence signal)
       [Ledger & Aggregation]                                │
        (cash + per-provider                                 │
             balances)                                       │
                 │                                            │
     ┌───────────┴────────────┐                               │
     ▼                        ▼                                │
[Liquidity Engine]     [Anomaly Detection Engine] ◄─────────────┘
     │                        │
     └───────────┬────────────┘
                 ▼
     [Alert & Case Management]
        (routing + ownership)
                 │
      ┌──────────┴───────────┐
      ▼                       ▼
[Explainability /      [Coordination /
 Localization]          Notification]
      │                       │
      └───────────┬───────────┘
                  ▼
     [Role-based Dashboards]
   (Agent / Ops / Risk / Mgmt)
                  │
                  ▼
        [Human Action: ack /
         escalate / resolve /
             case notes]
                  │
                  ▼
        [Audit Log] ──► [Metrics Store] ──► [Validation Evidence / Dashboards]
```

### 3.3 Degraded-Data Flow (Scenario C path)

```
Provider feed delayed/conflicting
        │
        ▼
Data Quality Engine flags "stale/conflicting"
        │
        ├──► Liquidity Engine widens confidence band / marks projection "low confidence"
        │
        └──► Anomaly Engine suppresses new high-confidence flags for affected provider,
             surfaces a "data issue" advisory instead of a risk alert
        │
        ▼
Dashboard clearly shows: "Provider X data delayed — figures may be outdated"
(provider balances kept separate; no blended/misleading number shown)
```

---

## 4. Key Data Entities (conceptual)

| Entity | Key Fields |
|---|---|
| `Agent/Outlet` | agent_id, area, physical_cash_balance, active_providers[] |
| `ProviderBalance` | agent_id, provider_id, current_balance, last_updated, feed_status |
| `Transaction` | txn_id, agent_id, provider_id, account_ref (synthetic), type, amount, timestamp, status |
| `LiquidityProjection` | agent_id, provider_id (or "shared_cash"), projected_shortage_time, confidence, signal_summary |
| `AnomalyFlag` | flag_id, agent_id, provider_id, pattern_type, evidence[], confidence, plausible_benign_explanation |
| `Case/Alert` | case_id, source (liquidity/anomaly), owner, status, routing_history[], notes[], created_at, resolved_at |
| `AuditEvent` | event_id, case_id, actor, action, timestamp |

---

## 5. Feature List

Features are grouped by module and tagged with priority inherited from the problem statement (**[M]**andatory, **[R]**ecommended, **[O]**ptional) plus **[E]**ngineering-depth features added to make the product feel complete without exceeding scope.

### 5.1 Unified Visibility
- **[M]** Combined agent view: shared cash + each provider's balance, clearly separated (never summed into one blended figure).
- **[R]** Filter/prioritize by provider, agent, area, or time.
- **[E]** Multi-agent overview for Operations/Management (Section 5 "Management" stakeholder need).

### 5.2 Liquidity Intelligence
- **[M]** Per-provider and shared-cash shortage projection with estimated time window.
- **[M]** Confidence indicator on every projection.
- **[R]** Contributing-signal breakdown (why the projection says what it says).
- **[O]** What-if simulation (e.g., "what if cash-out demand doubles for the next hour").

### 5.3 Anomaly & Risk Detection
- **[M]** At least one fully implemented anomaly pattern with evidence trail.
- **[M]** Careful, non-accusatory language throughout ("unusual," "requires review").
- **[R]** Evidence + short history attached to each anomaly alert.
- **[E]** Plausible-benign-explanation field alongside every anomaly flag.
- **[O]** Second/third anomaly pattern (e.g., transaction splitting, circular activity) if time allows.
- **[O]** Cross-provider relationship view using simulated identifiers.

### 5.4 Coordination & Case Management
- **[M]** For each important alert: assigned receiver, owner, recommended next step, current status.
- **[R]** Case notes and alert history, provider-boundary-respecting.
- **[E]** Full case lifecycle (open → acknowledged → escalated → resolved) with timestamps.
- **[E]** Routing rules aligned to the agent → field officer → area manager → central ops hierarchy (Section 5).
- **[O]** Nearby-agent support discovery (e.g., "Agent X 400m away has surplus cash").

### 5.5 Data Quality & Trust
- **[M]** Confidence/fallback state shown when data is missing, late, or conflicting.
- **[E]** Configurable fault injection for live demo of Scenario C.
- **[E]** Visible "data health" indicator per provider feed.

### 5.6 Explainability & Localization
- **[R]** English explanations for every alert.
- **[R]** At least one Bengali/Banglish alert with situation, evidence, uncertainty, and next step.
- **[E]** Consistent multi-language rendering from one structured alert object (no drift between languages).

### 5.7 Security, Privacy & Responsible Design
- **[M]** Synthetic identifiers only; no real credentials or account data anywhere in the system.
- **[M]** No automatic blocking, accusation, or financial action anywhere in the codebase.
- **[E]** Role-based access control enforcing provider data boundaries.
- **[E]** "Responsible-design note" content generated directly from documented guardrails (Section 14), not written after the fact.

### 5.8 Observability & Validation
- **[M]** Analytics/AI meaningfully embedded (liquidity forecasting + anomaly detection, not decorative).
- **[E]** `/metrics` endpoint or dashboard panel showing: forecast error on held-out simulated data, shortage detection lead time, anomaly precision/recall against injected test cases, false-positive rate, alert explanation coverage, API latency, and data-quality incident counts — directly supplying the ≥3 required validation metrics (Section 10) with headroom to report more.
- **[E]** Structured audit log covering every ownership change, acknowledgement, escalation, and resolution.

### 5.9 Presentation-Ready Artifacts
- **[M]** Architecture diagram (this document, Section 1).
- **[M]** Data & simulation note (how synthetic data/scenarios were generated — separate short doc, generated from Section 4 of this design).
- **[M]** Responsible-design note (derived from Section 5.7 above).
- **[R]** Short demo video walking through Scenarios A–D.

---

## 6. Recommended Tech Stack (lightweight, justified)

| Layer | Suggestion | Why |
|---|---|---|
| Frontend | React (or Next.js) + Tailwind | Fast to build role-based views; component reuse across Agent/Ops/Risk dashboards. |
| Backend | Node.js (Express/NestJS) or Python (FastAPI) | Either supports clean modular boundaries matching Section 2; FastAPI eases the anomaly-detection/statistics work if Python libraries are wanted. |
| Database | PostgreSQL via **Supabase** | Same relational integrity for ledger/case data and audit trails; managed Postgres with SQL migrations, connection pooling, and optional Row Level Security for provider-boundary enforcement. Connect from the backend via `DATABASE_URL` (pooler) or the Supabase JS client — do not commit project keys. |
| Cache (optional) | Redis or in-memory | Only if dashboard read latency needs it under demo load — not required for a small simulated dataset. |
| Analytics/Anomaly | Python (pandas/scikit-learn) or hand-rolled statistical rules in the backend language | Keep it explainable — simple, well-validated statistical rules often score better on "explainability" than an opaque model for this problem. |
| Auth | JWT-based RBAC | Simple, sufficient to demonstrate provider-boundary enforcement. |
| Deployment | Single containerized app (Docker) | Easy to run for judges from the README; avoids unnecessary infra claims. |

---

## 7. Explicitly Excluded (kept out of scope on purpose)

- Real bKash/Nagad/Rocket API integration or credentials of any kind.
- Any endpoint capable of moving money, blocking a user, or freezing funds.
- Multi-service/distributed architecture (Kafka, service mesh, multi-region) — not needed to prove the concept and not fully demonstrable/reliable within a hackathon build.
- Free-form LLM-generated financial recommendations without a template/evidence structure behind them (keeps explainability and auditability guarantees intact).
- Deep learning anomaly models without labeled data to validate against — favored transparent statistical/rule-based detection instead, matching the "explainable, not a black box" requirement.
