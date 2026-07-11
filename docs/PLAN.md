# Multi-Provider Super Agent Prototype — 23-Hour Build Plan (v2)

*Codex Community Hackathon — bKash presents SUST CSE Carnival 2026*

*This version merges the original plan with three improvements adopted from a crosscheck against a separate system-design document: Supabase Postgres with Row Level Security for provider-boundary enforcement, a lightweight role-based access layer, and a metrics feedback loop from resolved cases. The 2-3 pattern anomaly commitment and the hour-by-hour build order are kept as-is, since those were assessed as the stronger part of this plan relative to the alternative design.*

## 1. Plain-Language Restatement

Picture the Eid-market agent shop: one physical cash drawer, but three separate digital wallets — bKash, Nagad, Rocket — that can never be merged or converted into each other. Right now the agent can look at each wallet separately but can't easily answer "will I run out of *something* — cash or a specific provider's balance — in the next few hours?" On top of that, cash-out requests are spiking, and a cluster of near-identical transactions from a handful of accounts looks suspicious — but it could just be normal pre-Eid demand. Nobody has flagged it yet, and even if they did, it's unclear whose job it is to check it out, follow up, and close the loop.

Your prototype needs to do three things without ever touching real money or accusing anyone of fraud: (1) show a unified liquidity picture across cash + all three wallets and warn early about shortages, (2) flag unusual patterns with evidence and an honest confidence level, and (3) route each important alert to a specific human, track whether they acknowledged it, and show when it's resolved.

## 2. Feature List

### Mandatory

**Unified liquidity dashboard** — Shows physical cash balance and each provider's e-money balance side by side, never combined into one number.
- *Logic*: Ingest each transaction event (provider, type, amount, timestamp), maintain running balances per provider + one shared cash balance. Cash-out decreases physical cash and increases the relevant provider's e-money; cash-in increases physical cash and decreases the relevant provider's e-money.
- *Example*: Cash: 45,000 taka | bKash: 12,000 taka | Nagad: 38,000 taka | Rocket: 21,000 taka. Agent sees at a glance that bKash is thin even though total value looks fine.
- *Stakeholders*: Agent, management.
- *Evaluation category*: Problem understanding (15%), UX/explainability (10%).

**Liquidity forecasting / shortage prediction** — Projects when a specific balance will hit zero given recent transaction velocity.
- *Logic*: Take a rolling window (last 15-30 min) of reserve-specific net depletion. Cash-out volume contributes to shared physical-cash depletion while increasing the relevant provider e-money reserve; cash-in contributes in the opposite direction. Linear extrapolation: time_to_zero = current_balance / depletion_rate_per_minute. Wrap with a confidence band based on variance in the window.
- *Example*: Shared-cash depletion driven by bKash cash-outs averages 800 taka/min over the last 20 min; with 12,000 taka physical cash remaining, shortage is approximately 15 minutes away.
- *Stakeholders*: Agent, provider ops, management.
- *Evaluation category*: Innovation/decision value (20%), data & analytical quality (20%).

**Anomaly detection with evidence** — At least one, ideally 2-3 distinct pattern types (full breakdown in Section on Anomaly Detection below). Kept as a core, must-build commitment rather than deferred to stretch goals — this is deliberately more ambitious than "at least one," because Data & Analytical Quality plus Innovation together are 40% of the score and explicitly reward multiple distinguishable anomaly categories, not just checklist compliance.
- *Stakeholders*: Agent, risk/compliance analyst, provider ops.
- *Evaluation category*: Data & analytical quality (20%), innovation (20%).

**Careful risk language** — All anomaly outputs use "unusual," "requires review," "possible" — never "fraud," "confirmed," "blocked."
- *Logic*: Centralize all user-facing anomaly copy through one templating function so no code path can accidentally emit accusatory language.
- *Stakeholders*: All — this is a guardrail, not a feature users request but judges will check.
- *Evaluation category*: Security/fairness/responsible design (5%), problem understanding (15%).

**Alert ownership & status workflow** — For at least one important alert, show who it went to, who owns it, recommended next step, and current status (open/acknowledged/escalated/resolved).
- *Logic*: Alert object has assigned_to, status enum, recommended_action (templated string), history array of status changes with timestamps. Ops user clicks "Acknowledge" and status flips, timestamp logged.
- *Example*: Alert A-104 assigned to "Nagad Area Officer, Dhanmondi", status Acknowledged, next step "Contact agent, confirm cash-out purpose", resolved 12 min later with a case note.
- *Stakeholders*: Provider ops, risk analyst, management.
- *Evaluation category*: Technical implementation (25%), UX/explainability (10%).

**Confidence / fallback under bad data** — When provider data is missing, late, or conflicting, show reduced confidence rather than a false "all clear."
- *Logic*: Each provider feed has a last_updated timestamp. If staleness exceeds a threshold (e.g., 2 min), balance display shows a "stale data" badge and any liquidity forecast for that provider is marked "low confidence, data delayed."
- *Stakeholders*: Agent, provider ops, risk analyst.
- *Evaluation category*: Reliability (non-functional), data & analytical quality (20%).

**Provider-boundary access control (new in v2)** — A lightweight role layer so that a Provider A ops user genuinely cannot open a Provider B case, rather than relying only on query-level filtering in application code.
- *Logic*: A small role field on the (simulated) logged-in user — Agent / Provider-A Ops / Provider-B Ops / Provider-C Ops / Risk Analyst / Management — checked at the API layer before returning case or evidence data. Enforced a second time at the database layer via Postgres Row Level Security policies on the cases and transactions tables, keyed on provider_id, so the guarantee doesn't depend on every endpoint remembering to filter correctly.
- *Why it's worth the hours*: this is the exact guardrail Sections 5 and 14 call out most explicitly, and enforcing it at the database layer (not just in application code) is a concrete, demonstrable piece of engineering depth judges can be shown directly — a Provider B ops login simply gets nothing back for a Provider A case.
- *Stakeholders*: Provider ops, risk analyst — this is what makes the "provider separation" guarantee real rather than assumed.
- *Evaluation category*: Security/privacy/fairness (5%), technical implementation (25%).

**AI/analytics as a meaningful product part** — Not just a demo checkbox; the anomaly and forecasting logic is the product's core value, covered by the two features above.

### Recommended

**Filter/prioritize by provider, agent, area, time** — Simple dropdown/filter bar on the dashboard.
- *Logic*: Client-side filter on the already-fetched alert/balance list; no new backend logic needed beyond exposing the fields.
- *Stakeholders*: Provider ops, management.
- *Evaluation category*: UX (10%).

**Evidence + simple history per alert** — Expandable panel per alert showing the underlying transactions/data points that triggered it.
- *Logic*: Each alert stores an evidence list of transaction IDs/snapshots at trigger time. UI renders them as a small table.
- *Stakeholders*: Risk analyst, provider ops.
- *Evaluation category*: Explainability (non-functional), data quality (20%).

**Bengali/Banglish alert text** — At least one alert rendered in Bangla using the illustrative style from Section 11 of the problem statement.
- *Logic*: A translation dict or a small templated Bangla string builder for the top 2-3 alert types.
- *Stakeholders*: Agent (many Bangla-first users).
- *Evaluation category*: UX/explainability (10%), problem understanding (15%).

**Case notes / escalation** — Ops user can type a free-text note and change status to "Escalated to Risk."
- *Logic*: Simple textarea + status dropdown, appended to the history array.
- *Stakeholders*: Provider ops, risk analyst.
- *Evaluation category*: Technical implementation (25%).

**Resolution feedback loop for metrics (new in v2)** — When a case is resolved, the reviewer marks it as "confirmed review-worthy" or "false positive."
- *Logic*: Add a reviewer_verdict field to the case record, set on resolution. Precision/recall and false-positive rate are then computed from two combined sources: the injected synthetic test cases (known ground truth) and these human-marked resolutions from the live demo run itself.
- *Why it's worth adding*: it turns your metrics panel into evidence that the system incorporates real human review outcomes, not just a self-graded synthetic answer key — a stronger story for the "false positives, uncertainty, and data-quality failure modes are acknowledged and tested" success criterion.
- *Stakeholders*: Risk analyst, management, judges reviewing validation evidence.
- *Evaluation category*: Data & analytical quality (20%), presentation and demonstration (5%).

### Optional (only if time remains)

- Peer/cross-agent comparison (e.g., "this agent's Nagad velocity is 3x the area average").
- Simple hotspot view (skip actual maps, use a table with an area column and color badges).
- What-if simulation slider (drag an "expected Eid demand multiplier" and watch forecasted shortage time shift).

## Anomaly Detection: Three Distinct Patterns

Don't build one anomaly score. Build three separate, clearly-labeled detectors, each with its own evidence and its own honest false-positive story.

**Pattern 1 — Transaction Velocity Spike**
- *Detects*: Cash-out count/volume for a provider in a short window (e.g., 10 min) exceeding N standard deviations above that agent's historical baseline for the same time-of-day.
- *Why it matters*: Sudden spikes are the first sign of either a legitimate demand surge or someone draining a balance quickly.
- *Evidence shown*: "23 cash-outs in 10 min vs. typical 6 for this hour" plus a small sparkline of the last hour's transaction count.
- *False-positive case*: Pre-Eid or salary-day demand, the scenario explicitly given in Section 11B. The system should label this "Possible normal demand spike (pre-Eid pattern), recommend review before action" rather than treating velocity alone as damning.
- *Confidence*: Based on how far outside the historical distribution it sits — e.g., 2 standard deviations = "moderate," 4+ = "high." Shown as a labeled badge, not a bare number.

**Pattern 2 — Repeated/Near-Identical Amounts**
- *Detects*: Multiple transactions within a short window whose amounts fall within a tight tolerance band (about plus or minus 2%) of each other, especially from a small set of accounts.
- *Why it matters*: Classic signature of either structured/split transactions or an automated script — but also just how round-number cash-outs naturally cluster (people withdraw 2,000, 5,000, 10,000 taka disproportionately).
- *Evidence shown*: Table of the clustered transactions — amounts, account IDs (synthetic), timestamps.
- *False-positive case*: Round-number bias is universal in cash transactions — everyone withdraws in 500/1,000/5,000 taka increments, especially around a holiday when many people withdraw the same "Eid shopping budget." Explicitly document that near-identical amounts alone are weak evidence and should combine with velocity or account-diversity signals before being treated as review-worthy.
- *Confidence*: Weight by how few distinct accounts are involved relative to transaction count — many accounts hitting the same round number is low-confidence; few accounts repeating identical non-round amounts is higher-confidence.

**Pattern 3 — Balance Inconsistency / Data Conflict**
- *Detects*: Provider-reported balance doesn't reconcile with the sum of logged transactions since the last known-good balance (ledger drift), or two data feeds for the same agent disagree.
- *Why it matters*: This is the Scenario C case — not fraud at all, but a data-quality problem that must not be silently swallowed into a confident-looking dashboard.
- *Evidence shown*: "Expected balance 12,000 taka based on transaction log; provider feed reports 9,400 taka — 2,600 taka unexplained since 3:40 PM."
- *False-positive case*: Feed delay or an out-of-band manual adjustment (agent physically added cash) not yet logged in the system — clearly state this is a data-quality flag, not a wallet-integrity accusation.
- *Confidence*: Directly tied to feed staleness — the more stale the second feed, the more this is framed as "likely a sync delay" rather than "requires review."

Each detector runs independently and reports independently — never merged into a single opaque "risk score." The dashboard shows them as separate tagged alerts (Velocity / Amount-Pattern / Data-Conflict) so a risk analyst can see which kind of evidence they're reviewing.

## 3. System Components

| Component | Responsibility | Explicitly Does NOT |
|---|---|---|
| Data simulator | Generates synthetic agent/provider transaction streams, including injected anomaly scenarios and Eid-demand noise | Touch any real API, real customer, or real balance |
| Ingestion layer (FastAPI endpoint or scheduled job) | Receives/pulls simulated events, writes to per-provider transaction tables | Merge provider balances into one number at storage level |
| Liquidity engine | Computes running balances, rolling velocity, shortage forecast + confidence per provider/cash | Recommend or execute any cash movement |
| Anomaly engine (3 detectors) | Runs velocity, amount-pattern, and balance-conflict checks independently; emits tagged, evidenced alerts | Declare fraud or auto-block any account |
| Alert/case management service | Creates alert records, assigns owner, tracks status transitions, stores case notes, captures reviewer verdict on resolution | Auto-resolve or auto-escalate without a human action |
| Coordination workflow engine | Maps alert type to responsible stakeholder role (agent/ops/risk) per the hierarchy in Section 5 | Allow one provider's ops team to see another provider's case data |
| Auth & provider-boundary guard (new in v2) | Assigns a role to each simulated login; checks role against provider_id at the API layer and via Postgres Row Level Security at the database layer | Grant any role cross-provider read/write access, regardless of UI state |
| Agent-facing UI | Unified cash + balance view, plain-language alerts (including Bangla) | Show internal risk-analyst-only fields (e.g., raw evidence tables) |
| Ops-facing UI | Alert queue, filters, evidence panels, acknowledge/escalate/resolve actions | Execute any financial action |
| Audit/logging store | Every alert, status change, and acknowledgement timestamped and stored immutably | Get edited/deleted — append-only |

## 4. Data Flow

1. **Simulator to Ingestion**: Simulator emits a transaction event (agent_id, provider, type, amount, timestamp, area) to a FastAPI events endpoint, writing into Supabase Postgres.
2. **Ingestion to Balance store**: Backend updates the per-provider balance table and the shared cash table. Provider boundary enforced at two layers: application-level filtering by provider_id, and Postgres Row Level Security policies on the underlying tables so no query, even a buggy one, can return another provider's rows.
3. **Balance store to Liquidity engine**: On each update (or every few seconds), the liquidity engine recomputes rolling velocity and re-forecasts shortage time per provider and cash. Writes forecast plus confidence to a forecasts table.
4. **Balance/transaction store to Anomaly engine**: All three detectors run independently over the same transaction stream, each writing to its own alerts table row tagged with detector type, evidence (transaction IDs), and confidence.
5. **Alerts to Coordination engine**: New alert triggers a rule lookup (alert type + provider maps to responsible role) and creates a case record: assigned_to, status "open", recommended_action (templated text).
6. **Case to Dashboards**: Agent UI polls a per-agent dashboard endpoint (balances, forecasts, plain-language alerts). Ops UI polls an ops dashboard endpoint (case queue, evidence, filters) scoped by the logged-in role, so a Provider A ops session's queue never includes Provider B cases.
7. **Ops action to Case update**: Ops user clicks Acknowledge/Escalate/Resolve, which patches the case record — status and history updated, audit log entry appended. On Resolve, the ops user also marks a reviewer_verdict ("review-worthy" or "false positive"), which feeds the metrics panel.
8. **Provider separation enforcement**: At every boundary above, data is tagged by provider_id and no query joins across providers except at the shared-cash aggregation point, which only ever shows a sum of physical cash, never a sum or conversion of e-money balances. This is enforced redundantly, once in application code and once in the database via RLS, so the guarantee doesn't rest on a single layer.

## 5. Suggested Architecture & Stack

**Layers:**
- **Data/simulation**: Python script generating synthetic events on a timer, seeded with a few injected anomaly scenarios (matching Scenarios A-D) plus background "normal Eid noise."
- **Backend/API**: FastAPI — a stack you already have deep, recent fluency in. Single service, a few routers: events, dashboard-agent, dashboard-ops, cases, auth.
- **Storage**: Supabase Postgres, not SQLite. This is a change from v1 of this plan: given you already have working familiarity with Supabase (used it with pgvector on a recent project), the setup-time cost is low, and it gives you Row Level Security as a database-enforced guarantee for the provider-boundary requirement — a stronger, more auditable claim than application-code filtering alone. Use SQLAlchemy against the Supabase connection string, same as your usual FastAPI setup.
- **Analytics/detection**: Plain Python (pandas or even just lists/dicts) for rolling windows, z-scores, and the forecast math. No ML model needed or expected — the rubric rewards evidence and honest uncertainty, not model sophistication.
- **Auth**: Lightweight — a simulated login that just sets a role on the session (no need for full OAuth); RLS policies key off that role. Enough to demonstrate the guardrail without burning hours on a real auth provider.
- **Alerting/coordination**: Just backend logic plus REST endpoints; no separate message broker needed at this scale.
- **Frontend**: Next.js (App Router) — direct fit for your existing skillset. Routes for agent view and ops view, plus a simple role switcher for the demo (acting as three different logged-in users). Poll every 3-5 seconds with fetch — skip WebSockets, not worth the setup time for a 23-hour clock, and polling is indistinguishable in a live demo.
- **Monitoring/logging**: Structured console logs plus the audit table itself doubles as traceability evidence for judges.

**Why this stack**: every piece is something you've shipped working code in within the last few weeks (FastAPI, Next.js, SQLAlchemy, Supabase). Nothing here requires learning a new tool under time pressure — the risk budget goes entirely into getting the three anomaly detectors and the coordination workflow demonstrably correct, which is where the rubric weight actually sits (25% plus 20% plus 20% equals 65% of total score across technical implementation, innovation, and data quality). The RLS layer adds real engineering depth for a small, fixed setup cost rather than an open-ended one.

## 6. MVP Prioritization (23 Hours Left)

**Build First (Hours 1-10)** — unlocks checklist items 1, 2, 3, 4, 5, 9 and the Mandatory functional row, plus roughly 45% of evaluation weight (technical implementation + data quality portions):
- Supabase project setup + schema (agents, provider_balances, transactions, forecasts, alerts, cases, audit_log) — budget 30-45 min given existing familiarity.
- Data simulator with realistic multi-provider transactions, Eid-demand noise, and 2-3 injected anomaly scenarios.
- Balance tracking (cash + 3 providers) and the liquidity forecast with confidence.
- Must-build anomaly detectors: Velocity Spike and Repeated/Near-Identical Amounts. These two alone satisfy "at least one anomaly category" with real margin, and together let you demo Scenario B directly.
- Careful-language templating for all alert copy.

**Build Second (Hours 10-19)** — unlocks checklist items 6, 7, 8, 10 and the remaining roughly 40% weight (coordination, UX, explainability, security):
- Alert/case model with assignment, status, and one full acknowledge-to-resolve cycle wired end to end (Scenario D), including the reviewer_verdict field on resolution.
- Lightweight role/session layer plus Row Level Security policies on cases and transactions tables — this is the single most time-boxed new item versus v1 of this plan; budget no more than 90 minutes, since it's a small number of policies keyed on one column (provider_id).
- Agent UI + Ops UI (basic but clean — use shadcn/ui components if using React to save styling time), including a simple role switcher for the demo.
- Evidence panel per alert.
- Stretch-but-recommended anomaly detector: Balance Inconsistency. This is your Scenario C and it's cheap to build (just a diff check between two numbers) relative to its payoff — treat it as "build if hours 1-10 finished on schedule," not a true stretch goal.
- At least one Bangla alert string.

**Only If Time Remains (Hours 19-23)** — polish plus remaining checklist items:
- Filters by provider/area/time.
- Case notes free-text field.
- Metrics panel combining injected-ground-truth precision/recall with the live reviewer_verdict feedback loop, plus false-positive rate on your Eid-noise transactions and API latency average — directly satisfies "at least three metrics measured" with a stronger story than synthetic-only evaluation.
- Architecture diagram, README, and responsible-design note (don't skip these — they're explicit deliverables worth real points and take under an hour to write well).

Note: 1 hour was already gone from the 24 at the time this plan was written, so the ranges above assume you're starting "Build First" right away. If the RLS setup runs long, cut it back to application-layer filtering only and note the simplification in your responsible-design doc — don't let it eat into Build Second's core coordination workflow, which carries more evaluation weight.

## 7. Guardrail Checklist

Before your demo, confirm your prototype does none of the following:
- Converts, merges, or nets one provider's e-money against another's.
- Touches any real API, real customer identity, or real balance.
- Labels anything "confirmed fraud," "blocked," or takes any automatic account action.
- Requests or stores PINs, OTPs, passwords, or other credentials.
- Lets one provider's ops view see another provider's case/evidence data (verify this at both the API response and, if built, the RLS policy level).
- Auto-escalates or auto-resolves a case without an explicit human action.
- Claims regulatory approval or "production-ready" fraud detection anywhere in copy or docs.

## 8. Demo Script Skeleton

1. Open on the unified agent dashboard — cash + 3 provider balances, calm and healthy-looking at a glance.
2. Narrate Scenario A — point to shared physical cash sliding down under heavy bKash cash-out demand while the bKash e-money balance remains healthy; forecast panel shows "about 20 min to shared-cash shortage, high confidence" with the Bangla alert rendered live.
3. Transition into Scenario B — show the Velocity Spike alert firing alongside the liquidity pressure, and the Repeated-Amounts alert firing separately and distinctly (two tagged alert types, not one blended score). Explicitly say out loud: "this could just be pre-Eid demand — here's why we're not calling it fraud," pointing to the false-positive framing in the alert copy.
4. Cut to the Ops dashboard — show the case queue, click into one alert, show the evidence table, click Acknowledge, add a case note, then Resolve, marking it "review-worthy" or "false positive" — narrating the ownership/escalation path from Section 5's hierarchy.
5. Switch the role/login to a different provider's ops account and show that the just-resolved case (and its evidence) is not visible from that account — the concrete demonstration of the provider-boundary guardrail.
6. Briefly show Scenario C — a deliberately stale/conflicting feed, and show the dashboard degrading to "low confidence" rather than a false all-clear.
7. Close honestly — state your measured metrics (precision/recall blending injected cases and live reviewer verdicts, false-positive rate on Eid-noise, latency), and explicitly name what the prototype does not do (no real integration, no fraud determination, no automatic action). This closing honesty is directly graded under both data quality and responsible design.

Highest-leverage build target with the clock running: get the velocity + amount-pattern detectors plus one full alert lifecycle solid before touching anything in the "only if time remains" tier. The RLS/role layer is worth the roughly 90 minutes it costs, but not more than that — if it stalls, fall back to application-layer filtering and keep moving.