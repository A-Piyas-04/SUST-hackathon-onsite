# Project Progress Checklist
### Codex Community Hackathon — bKash presents SUST CSE Carnival 2026

Use this checklist to track development progress. Items in *italics* under each requirement are suggested sub-tasks added to help you actually satisfy that requirement — check them off as you go, then check the parent requirement once fully done.

---

## A. Functional Requirements

### A.1 Mandatory

- [ ] Show shared physical cash and separate balances for each provider
  - [ ] *Design data model: shared cash pool + per-provider e-money balance fields*
  - [ ] *Build unified dashboard view combining cash + all provider balances*
- [ ] Show which provider or shared cash reserve may face a shortage and approximately when
  - [ ] *Implement demand/burn-rate projection logic (e.g., time-series or rate-based forecast)*
  - [ ] *Display estimated time-to-shortage per provider and for shared cash*
- [ ] Detect at least one type of unusual activity and show why it was flagged
  - [ ] *Choose at least one anomaly pattern (velocity, near-identical amounts, splitting, circular activity, etc.)*
  - [ ] *Implement detection logic (rule-based, statistical, or ML)*
  - [ ] *Attach human-readable reason/evidence to each flag*
- [ ] Use careful language such as "unusual" or "requires review"; do not declare fraud
  - [ ] *Review all alert copy/UI text to remove definitive fraud language*
- [ ] For at least one important alert, show who receives it, who owns it, the recommended next step, and the final status
  - [ ] *Build alert routing logic (who is notified)*
  - [ ] *Build case ownership / assignment mechanism*
  - [ ] *Add recommended next-step field*
  - [ ] *Add status tracking (open / acknowledged / escalated / resolved)*
- [ ] Show lower confidence or a safe fallback when data is missing, late, or conflicting
  - [ ] *Implement data quality checks (missing, delayed, conflicting feeds)*
  - [ ] *Implement confidence scoring or fallback state in UI*
- [ ] Use AI, APIs, analytics, or data processing as a meaningful part of the product
  - [ ] *Identify and implement at least one non-trivial analytics/AI component*
  - [ ] *Document how it's used and why it's meaningful (not decorative)*

### A.2 Recommended

- [ ] Allow users to filter or prioritize by provider, agent, area, or time
- [ ] Provide evidence and a simple history for important alerts
- [ ] Offer clear Bengali, Banglish, or English explanations
- [ ] Show at least one simple Bengali or Banglish alert with situation, evidence, uncertainty, and a safe next step
- [ ] Support provider-specific escalation, case notes, alert history, and coordination while keeping provider boundaries clear

### A.3 Optional

- [ ] Support simulations, peer comparison, relationship views, or cross-provider patterns
- [ ] Independently defined additional fraud/anomaly-detection scenario(s)
  - [ ] *Document chosen pattern, detection approach, and evidence*
  - [ ] *Confirm scenario uses simulated/anonymized data only*
  - [ ] *Confirm anomaly score is NOT presented as proof of fraud*

---

## B. Non-Functional Requirements

- [ ] **Usability** — Provider distinctions, shared cash exposure, and risk signals are easy to understand
- [ ] **Performance** — Core analytical and dashboard interactions are responsive under demonstrated data volume
  - [ ] *Benchmark response times at target data volume*
- [ ] **Reliability** — Provider data failures/inconsistencies do not silently produce confident conclusions
  - [ ] *Test with intentionally broken/missing/delayed provider data*
- [ ] **Explainability** — Every high-impact alert exposes reason, relevant evidence, and uncertainty
- [ ] **Security and privacy** — Synthetic identifiers only; no real credentials, customer identities, or sensitive account data
  - [ ] *Audit dataset for any real/sensitive data leakage*
- [ ] **Fairness and responsible AI** — No unsupported profiling; human review demonstrated for risk judgments
- [ ] **Auditability** — Alerts, ownership changes, acknowledgements, escalations, evidence, and resolutions are traceable
  - [ ] *Implement audit log / activity trail*
- [ ] **Interoperability** — Multiple providers represented without assuming real technical integration

---

## C. Scope & Guardrail Compliance (self-check)

- [ ] At least two logically separate financial service providers simulated
- [ ] No real interoperability, settlement, or conversion between provider wallets implemented
- [ ] No access to production APIs, real customer identities, real balances, or real accounts
- [ ] No automatic blocking, accusation, disciplinary action, or final fraud determination
- [ ] No unauthorized cash movement, wallet refill, transfer, recovery, or reversal
- [ ] No collection of PINs, OTPs, passwords, or private authentication data
- [ ] No claims of regulatory approval or production fraud-detection readiness
- [ ] All risk/anomaly signals framed as advisory, not final decisions

---

## D. Data & Simulation

- [ ] Synthetic / mock / anonymized dataset created (agent & provider IDs, area, time, transaction type, amount, status, balances, event flags, case status)
- [ ] Data generation method documented (how it was created)
- [ ] Assumptions documented
- [ ] Known limitations documented
- [ ] Risk interpretation rule documented (anomaly ≠ fraud; false-positive risk; human review requirement)

---

## E. Required Deliverables

- [ ] **Working prototype**
  - [ ] *Live flow: multi-provider balances visible*
  - [ ] *Live flow: at least one liquidity or anomaly alert triggers*
  - [ ] *Live flow: at least one case is coordinated/escalated end-to-end*
- [ ] **Source repository**
  - [ ] *Source code pushed*
  - [ ] *README written*
  - [ ] *Setup / installation steps documented*
  - [ ] *Environment variable examples (.env.example) included*
  - [ ] *Sample data included*
- [ ] **Architecture diagram**
  - [ ] *Main interfaces shown*
  - [ ] *Backend components shown*
  - [ ] *Data flow shown*
  - [ ] *Analytics/AI services shown*
  - [ ] *Monitoring shown*
  - [ ] *Provider boundaries shown*
  - [ ] *Alert coordination flow shown*
- [ ] **Data and simulation note** (write-up of how synthetic data/scenarios were created, assumptions, limitations)
- [ ] **Validation evidence** — at least 3 measured metrics (analytics, performance, and/or reliability)
  - [ ] *Metric 1 chosen and measured: __________*
  - [ ] *Metric 2 chosen and measured: __________*
  - [ ] *Metric 3 chosen and measured: __________*
- [ ] **Responsible-design note** (privacy, human review, false positives, advisory boundaries, what the prototype intentionally does NOT do)
- [ ] **Final presentation**
  - [ ] *Problem statement covered*
  - [ ] *Users/stakeholders covered*
  - [ ] *Story-driven live demo prepared*
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

- [ ] Scenario A — Hidden provider shortage
- [ ] Scenario B — Liquidity pressure with unusual activity
- [ ] Scenario C — Cross-provider or data inconsistency
- [ ] Scenario D — Coordinated response and closure

---

## H. System Design Feature List

Features grouped by module from the System Design document. Tags: **[M]** Mandatory, **[R]** Recommended, **[O]** Optional, **[E]** Engineering-depth.

### H.1 Unified Visibility

- [ ] **[M]** Combined agent view: shared cash + each provider's balance, clearly separated (never summed into one blended figure)
- [ ] **[R]** Filter/prioritize by provider, agent, area, or time
- [ ] **[E]** Multi-agent overview for Operations/Management

### H.2 Liquidity Intelligence

- [ ] **[M]** Per-provider and shared-cash shortage projection with estimated time window
- [ ] **[M]** Confidence indicator on every projection
- [ ] **[R]** Contributing-signal breakdown (why the projection says what it says)
- [ ] **[O]** What-if simulation (e.g., "what if cash-out demand doubles for the next hour")

### H.3 Anomaly & Risk Detection

- [ ] **[M]** At least one fully implemented anomaly pattern with evidence trail
- [ ] **[M]** Careful, non-accusatory language throughout ("unusual," "requires review")
- [ ] **[R]** Evidence + short history attached to each anomaly alert
- [ ] **[E]** Plausible-benign-explanation field alongside every anomaly flag
- [ ] **[O]** Second/third anomaly pattern (e.g., transaction splitting, circular activity) if time allows
- [ ] **[O]** Cross-provider relationship view using simulated identifiers

### H.4 Coordination & Case Management

- [ ] **[M]** For each important alert: assigned receiver, owner, recommended next step, current status
- [ ] **[R]** Case notes and alert history, provider-boundary-respecting
- [ ] **[E]** Full case lifecycle (open → acknowledged → escalated → resolved) with timestamps
- [ ] **[E]** Routing rules aligned to the agent → field officer → area manager → central ops hierarchy
- [ ] **[O]** Nearby-agent support discovery (e.g., "Agent X 400m away has surplus cash")

### H.5 Data Quality & Trust

- [ ] **[M]** Confidence/fallback state shown when data is missing, late, or conflicting
- [ ] **[E]** Configurable fault injection for live demo of Scenario C
- [ ] **[E]** Visible "data health" indicator per provider feed

### H.6 Explainability & Localization

- [ ] **[R]** English explanations for every alert
- [ ] **[R]** At least one Bengali/Banglish alert with situation, evidence, uncertainty, and next step
- [ ] **[E]** Consistent multi-language rendering from one structured alert object (no drift between languages)

### H.7 Security, Privacy & Responsible Design

- [ ] **[M]** Synthetic identifiers only; no real credentials or account data anywhere in the system
- [ ] **[M]** No automatic blocking, accusation, or financial action anywhere in the codebase
- [ ] **[E]** Role-based access control enforcing provider data boundaries
- [ ] **[E]** "Responsible-design note" content generated directly from documented guardrails, not written after the fact

### H.8 Observability & Validation

- [ ] **[M]** Analytics/AI meaningfully embedded (liquidity forecasting + anomaly detection, not decorative)
- [ ] **[E]** `/metrics` endpoint or dashboard panel showing: forecast error on held-out simulated data, shortage detection lead time, anomaly precision/recall against injected test cases, false-positive rate, alert explanation coverage, API latency, and data-quality incident counts
- [ ] **[E]** Structured audit log covering every ownership change, acknowledgement, escalation, and resolution

### H.9 Presentation-Ready Artifacts

- [ ] **[M]** Architecture diagram (System Design, Section 1)
- [ ] **[M]** Data & simulation note (how synthetic data/scenarios were generated)
- [ ] **[M]** Responsible-design note (derived from H.7 guardrails)
- [ ] **[R]** Short demo video walking through Scenarios A–D

---

## I. Final Submission Checklist (from problem statement Section 16)

- [ ] At least two provider contexts represented distinctly
- [ ] Shared cash and provider-specific balances demonstrated
- [ ] Forward-looking liquidity insight demonstrated
- [ ] At least one anomaly category demonstrated with evidence
- [ ] Human-review and careful risk language included
- [ ] At least one alert demonstrates routing, ownership, acknowledgement or escalation, and a visible resolution status
- [ ] Repository, data, README, and architecture complete
- [ ] At least three metrics measured and explained
- [ ] Failure, uncertainty, and false-positive considerations shown
- [ ] Safety, privacy, boundaries, and limitations stated
- [ ] Final presentation ready
