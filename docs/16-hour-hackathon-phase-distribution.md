# 16-Hour Hackathon Phase Distribution

## 1. Objective

Build and demonstrate a safe decision-support prototype for a multi-provider financial-service agent that:

1. Shows one shared physical-cash reserve alongside separate provider e-money balances.
2. Predicts which reserve may run short and approximately when.
3. Detects at least one unusual transaction pattern and explains the evidence.
4. Reduces confidence or falls back safely when source data is missing, delayed, or conflicting.
5. Routes one important alert through assignment, acknowledgement or escalation, and resolution.
6. Uses synthetic data, preserves provider boundaries, and supports human review without declaring fraud or executing financial actions.

The plan deliberately favors a complete, reliable vertical slice over a broad collection of unfinished features.

## 2. Scope Decision Before the Clock Starts

### Committed MVP

- Two logically separate providers, such as Provider A and Provider B.
- One agent/outlet with a shared physical-cash pool.
- Provider-specific electronic balances and transaction streams.
- A unified dashboard with provider, area, and time filters if time permits.
- A simple shortage forecast for shared cash and each provider balance.
- One anomaly category: repeated or near-identical amounts within a short time window, optionally combined with transaction velocity.
- Human-readable alert evidence, uncertainty, and a safe next step.
- Data-quality states for stale, missing, and conflicting feeds.
- One provider-specific case flow: `Open -> Acknowledged -> Escalated or Under Review -> Resolved`.
- An activity trail for alert creation, assignment, status changes, notes, and resolution.
- At least three measured metrics.
- README, architecture diagram, data/simulation note, responsible-design note, and final presentation.

### Stretch Scope Only

- More than two providers or many agents.
- Relationship/network graphs.
- Peer comparison and hotspot maps.
- What-if simulations.
- Multiple anomaly models.
- Video recording.
- Sophisticated machine learning.

Do not begin stretch work until the MVP passes the Hour 12 integration gate.

## 3. Recommended Technical Strategy

Keep the architecture small enough to finish:

```text
Synthetic data generator
        |
        v
Data validation/normalization -> Liquidity forecast + anomaly rules
        |                                  |
        +----------------+-----------------+
                         v
                API or application state
                         |
          +--------------+---------------+
          v                              v
 Unified dashboard                 Alert/case workflow
          |                              |
          +--------------+---------------+
                         v
               Audit log and metrics
```

Suggested analytics:

- **Liquidity forecast:** calculate recent net depletion rate separately for shared cash and each provider balance. Estimate `time_to_shortage = usable_balance / depletion_rate` only when the rate is positive and data quality is acceptable. Show `stable/no shortage projected` when depletion is not occurring.
- **Forecast confidence:** combine feed freshness, sample count, rate stability, and conflicting-balance checks into `High`, `Medium`, or `Low`. Do not show a precise shortage time when confidence is low; show a range or `estimate unavailable—data requires review`.
- **Unusual activity:** flag repeated or near-identical transaction amounts within a defined window when both count and value/velocity thresholds are exceeded. Store the triggering count, time window, involved synthetic IDs, baseline comparison, and possible normal explanations.
- **Safe language:** use `unusual`, `requires review`, `possible liquidity pressure`, and `estimated`. Never use `fraudster`, `fraud confirmed`, or `block account`.

## 4. Role Allocation

For a four-person team, use these parallel lanes:

| Lane | Primary responsibility |
|---|---|
| Product/UX and presentation | Requirements, wireframe, alert wording, demo story, slides, final coordination |
| Frontend | Dashboard, forecast cards, alert evidence, filters, case workflow UI |
| Backend/data | Schemas, synthetic generator, APIs/state, case/audit persistence, data-quality validation |
| Analytics/QA | Forecast, anomaly rules, confidence logic, test scenarios, metrics and reliability evidence |

For fewer people:

- **Three people:** combine Product/UX with Frontend.
- **Two people:** one owns UI/demo; one owns data/backend/analytics. Both test and document.
- **Solo:** follow the phases sequentially, use one application process and local JSON/SQLite data, and omit all stretch work.

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
2. Select the main story:
   - An outlet has shared cash and two separate provider balances.
   - Provider A cash-outs accelerate, creating a projected shared-cash shortage.
   - Several near-identical transactions are flagged as unusual with evidence.
   - A provider feed later becomes stale/conflicting, lowering forecast confidence.
   - The alert is routed to Provider A operations, assigned, acknowledged, reviewed, and resolved.
3. Define the two primary views:
   - Agent/unified operations dashboard.
   - Alert detail and case coordination view.
4. Freeze the technology stack, repository conventions, owners, and integration method.
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
   - Shared-cash card.
   - Separate Provider A and Provider B balance cards.
   - Estimated time-to-shortage and confidence on each card.
   - Transaction/liquidity trend.
   - Prioritized alerts.
   - Clear provider colors and labels without implying wallet interoperability.
2. Sketch the alert detail:
   - Situation and severity.
   - Why it was flagged.
   - Evidence and uncertainty.
   - Possible normal explanation.
   - Recipient, owner, recommended safe next step, status, notes, and history.
3. Define minimum entities:
   - `Provider`, `Agent`, `BalanceSnapshot`, `Transaction`, `FeedHealth`, `Alert`, `Case`, and `AuditEvent`.
4. Define provider-separated schemas and response contracts. Include timestamps, synthetic identifiers, data source, and provider scope on relevant records.
5. Define controlled scenarios:
   - Normal operation.
   - Hidden provider shortage.
   - Shared-cash pressure plus repeated-amount activity.
   - Missing/stale/conflicting provider data.
   - Coordinated alert closure.
6. Define thresholds and assumptions in a configuration file rather than scattering constants through code.
7. Create the initial architecture diagram while the design is still simple.

### Deliverables

- Approved low-fidelity screen layout.
- Shared schema/API contract.
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

1. Implement the schemas and synthetic-data generator.
2. Generate at least two providers, shared cash, timestamped balance snapshots, transactions, feed health, and case states.
3. Add deterministic seeds so demo and tests are reproducible.
4. Expose fixtures through a simple API, local service, or application store.

**Frontend lane**

1. Build the dashboard shell and provider-separated balance cards.
2. Add loading, empty, error, and stale-data states from the beginning.
3. Build the alert list and alert-detail/case shell using fixtures.

**Analytics/QA lane**

1. Implement validation for required fields, timestamps, balance conflicts, and provider separation.
2. Write unit tests for normal and malformed samples.
3. Prepare labeled synthetic cases for forecast and anomaly evaluation.

**Product/documentation lane**

1. Start README setup instructions and assumptions.
2. Review all visible wording for advisory language.
3. Maintain requirement-to-evidence mapping.

### Integration checkpoint at Hour 4

- Merge schemas, fixtures, and the first dashboard view.
- Resolve contract mismatches immediately; do not defer them.

### Exit gate at Hour 5

- One command starts the prototype.
- The dashboard displays shared cash and two separate provider balances from generated data.
- Synthetic scenarios can be selected or replayed deterministically.
- No real credentials, names, balances, accounts, or production APIs exist in the repository.

## Phase 4 — Liquidity and Anomaly Analytics

**Time:** 05:00-07:30  
**Goal:** Complete the core decision value and make every output explainable.

### Actions

1. Implement separate depletion rates and shortage estimates for:
   - Shared physical cash.
   - Provider A e-money.
   - Provider B e-money.
2. Prevent invalid forecasts:
   - Never divide by zero.
   - Do not predict shortage for flat or replenishing balances.
   - Do not silently mix providers.
   - Make the forecast window and minimum sample count configurable.
3. Implement repeated/near-identical amount detection:
   - Define time window, amount tolerance, minimum count, and optional value threshold.
   - Compare against a simple recent baseline where feasible.
   - Return a score/category plus structured evidence, not merely a Boolean flag.
4. Connect liquidity and unusual activity in one alert when both affect the same provider/outlet/time window.
5. Generate explanations such as:
   - `Shared cash may run short in approximately 2h 10m if the recent cash-out rate continues.`
   - `Requires review: 7 cash-out requests within 12 minutes had amounts within 1% of each other; this may also reflect normal event-driven demand.`
6. Display safe recommendations such as contacting the outlet, verifying feed health, reviewing transactions, or escalating through the provider's authorized process.
7. Add tests for threshold boundaries, no-depletion conditions, injected anomalies, and normal high-demand periods.

### Deliverables

- Working shortage forecast with evidence and assumptions.
- Working unusual-activity rule with human-readable evidence.
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

1. Implement feed-health checks:
   - Missing feed or required fields.
   - Timestamp older than the configured freshness threshold.
   - Conflicting balance values or impossible transitions.
   - Insufficient samples for forecasting.
2. Map feed health to safe output behavior:
   - Lower confidence.
   - Show the affected provider and data timestamp.
   - Suppress precise forecasts when evidence is insufficient.
   - Recommend checking the source rather than making a financial recommendation.
3. Implement the case lifecycle:
   - Alert created and routed to the correct provider operations role.
   - Owner assigned.
   - Acknowledgement recorded.
   - Note or evidence added.
   - Escalation to risk/review or operational follow-up when appropriate.
   - Resolution status and resolution note recorded.
4. Write every action to an append-only activity trail with actor, timestamp, previous state, new state, and provider scope.
5. Ensure users in one provider context cannot appear to control another provider's balance or decision.
6. Add one concise Bengali or Banglish alert containing situation, evidence, uncertainty, and a safe next step if the team can validate the wording.

### Deliverables

- Low-confidence/stale/conflicting data states.
- Provider-aware routing and ownership.
- Visible end-to-end case history and final status.
- Tests for invalid state changes and cross-provider leakage.

### Exit gate at Hour 10

- Scenario C visibly lowers or withdraws confidence instead of presenting a confident forecast.
- Scenario D can be completed entirely through the UI/API without editing data manually.
- Alert creation, assignment, acknowledgement, escalation, notes, and resolution are traceable.

## Phase 6 — UX Integration and MVP Freeze

**Time:** 10:00-12:00  
**Goal:** Turn separate features into one clear, stable product story.

### Actions

1. Integrate all live data and remove placeholder content from the demo path.
2. Prioritize the dashboard by urgency and estimated shortage time.
3. Add filters for provider and time; add agent/area filters only if the data model already supports them cleanly.
4. Standardize severity, provider colors, status labels, timestamps, units, and number formatting.
5. Make uncertainty visible next to the prediction, not hidden in a tooltip or documentation.
6. Add clear navigation from dashboard alert to evidence and from evidence to case actions/history.
7. Test the complete story from a fresh setup and clean browser/session.
8. Fix only issues that block comprehension, correctness, safety, or the demo.

### Deliverables

- Stable integrated MVP.
- Complete story covering scenarios A through D, whether as separate fixtures or one sequence.
- Feature freeze and tagged/demo-ready commit.

### Hour 12 hard gate

The following must work before any stretch feature is considered:

- Shared cash plus at least two separate provider balances.
- Forward shortage estimate with confidence.
- One evidence-backed unusual-activity alert.
- Missing/stale/conflicting-data fallback.
- Recipient, owner, next step, acknowledgement/escalation, and final status.
- Audit trail.
- Careful human-review language and provider boundaries.

If any item fails, spend all remaining development time on it and cut recommended/optional features.

## Phase 7 — Validation, Reliability, and Safety QA

**Time:** 12:00-13:30  
**Goal:** Produce credible measured evidence and eliminate high-risk failures.

### Required metrics

Measure at least three; the recommended set covers analytics, performance, and reliability:

1. **Analytics:** anomaly precision, recall, and false-positive rate on labeled synthetic scenarios. State sample size and injection method.
2. **Performance:** average and p95 processing/API/dashboard latency at a documented number of agents and transactions.
3. **Reliability/explainability:** percentage of high-impact alerts containing reason, evidence, uncertainty, and recommended next step; target 100% for the demo set.
4. **Optional liquidity metric:** shortage lead-time error or balance/demand forecast error on held-out synthetic scenarios.
5. **Optional failure metric:** percentage of missing/stale/conflicting inputs that correctly produce degraded confidence; target 100% for defined failure cases.

### Actions

1. Freeze a labeled validation dataset separate from threshold-tuning examples.
2. Run repeatable evaluation and save raw outputs or screenshots.
3. Test intentionally missing, delayed, malformed, and conflicting provider data.
4. Test normal event-driven demand to expose false positives.
5. Verify no unsupported profiling or final fraud judgment appears.
6. Audit the repository for real credentials, identities, account data, and unsafe actions.
7. Verify setup on a clean environment or teammate machine.
8. Record limitations honestly; do not inflate simulated results into production claims.

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
   - Setup/run steps.
   - Environment variables and `.env.example`.
   - Demo scenario instructions.
   - Test and metric commands.
2. Finalize the architecture diagram with interfaces, backend, data flow, analytics, monitoring, provider boundaries, and case coordination.
3. Write the data and simulation note:
   - Generation method and deterministic seed.
   - Fields, volumes, and scenarios.
   - Assumptions and injected anomalies.
   - Validation split.
   - Known limitations.
4. Write the responsible-design note:
   - Synthetic data and privacy.
   - Anomaly is not proof of fraud.
   - False-positive risk and human review.
   - Provider separation.
   - Actions intentionally not performed.
5. Add metric results with methods and limitations.
6. Confirm sample data and source code are committed and setup instructions are reproducible.

### Exit gate

- A reviewer can run the prototype from the README.
- All seven required deliverables are present.
- Documentation matches the actual implementation; no production-readiness or regulatory claims are made.

## Phase 9 — Presentation and Rehearsal

**Time:** 14:30-15:30  
**Goal:** Present the complete decision-support story clearly and on time.

### Suggested presentation flow

1. **Problem and stakes:** one shared cash pool, separate provider balances, and fragmented coordination.
2. **Users:** agent, provider operations, risk/review, and management.
3. **Live scenario:** unified balance view and hidden shortage.
4. **Decision value:** forecast, confidence, unusual-activity evidence, and possible normal explanation.
5. **Reliability:** stale/conflicting feed lowers confidence.
6. **Coordination:** route, assign, acknowledge, escalate/review, resolve, and show audit history.
7. **Architecture:** explain provider boundaries and meaningful analytics.
8. **Evidence:** show three measured metrics.
9. **Responsibility:** synthetic data, human review, false positives, and prohibited actions.
10. **Limitations and next steps:** be specific and credible.

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
| Hour 5 | Runnable dashboard with synthetic multi-provider data | Reduce to two providers and one agent; use local fixtures |
| Hour 7:30 | Forecast and explainable anomaly work | Simplify to deterministic rate forecast and one rule |
| Hour 10 | Confidence fallback and case lifecycle work | Drop filters, localization, and all optional views |
| Hour 12 | Integrated MVP passes full story | Freeze scope; only repair mandatory flow |
| Hour 13:30 | Metrics and safety/reliability evidence captured | Stop feature work; measure the stable build |
| Hour 14:30 | All required repository documents complete | Assign one owner and use concise factual notes |
| Hour 15:30 | Rehearsed presentation and backup ready | Use screenshots/recording; do not risk untested fixes |
| Hour 16 | Submission confirmed | Submit the last stable build, not a late experimental version |

## 8. Requirement-to-Demo Traceability

| Requirement | Implementation evidence | Demo moment |
|---|---|---|
| Shared cash and separate provider balances | Unified dashboard cards backed by provider-scoped records | Open dashboard |
| Upcoming shortage and approximate time | Depletion rate, estimate/range, confidence, and evidence | Trigger hidden-shortage scenario |
| Unusual activity and reason | Repeated-amount/velocity rule with structured evidence | Open alert detail |
| Careful language | Copy review and responsible-design note | Read alert wording |
| Recipient, owner, next step, final status | Provider routing and case state machine | Assign, acknowledge, escalate/review, resolve |
| Missing/late/conflicting fallback | Feed-health validation and low-confidence state | Switch to bad-feed scenario |
| Meaningful analytics/data processing | Forecast, anomaly evaluation, and confidence pipeline | Architecture and metrics slides |
| Explainability and auditability | Evidence panel and activity trail | Review case history |
| Provider boundaries | Provider-scoped data and actions; no conversion feature | Architecture and UI labels |
| At least three metrics | Saved evaluation and performance results | Metrics slide |
| Safety/privacy/human review | Synthetic IDs, advisory outputs, no automated action | Responsible-design slide |

## 9. Final Submission Checklist

### Prototype

- [ ] At least two provider contexts are visibly and logically separate.
- [ ] Shared physical cash and each provider balance are displayed together.
- [ ] A provider or shared-cash shortage is projected with approximate timing.
- [ ] Forecast uncertainty/confidence is visible.
- [ ] At least one unusual pattern is detected with evidence and possible normal context.
- [ ] Alert wording says `unusual` or `requires review`, never confirmed fraud.
- [ ] Bad input lowers confidence or suppresses the estimate safely.
- [ ] One alert shows recipient, owner, next step, acknowledgement/escalation, and resolution.
- [ ] Alert and case changes are traceable in history.

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
- [ ] Source repository with README, setup steps, `.env.example`, and sample data.
- [ ] Architecture diagram with analytics, monitoring, boundaries, and coordination flow.
- [ ] Data and simulation note.
- [ ] Validation evidence.
- [ ] Responsible-design note.
- [ ] Final presentation with a rehearsed live demo and backup.

## 10. Definition of Success

At Hour 16, the strongest achievable submission is not the one with the most screens. It is the one that reliably demonstrates this complete chain:

> Separate provider data and shared cash -> forward liquidity insight -> explainable unusual-activity evidence -> visible uncertainty -> provider-aware human ownership -> traceable resolution.

Every feature, document, metric, and presentation choice should strengthen that chain.
