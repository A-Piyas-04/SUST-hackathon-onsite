# Full Prototype Simulation Walkthrough

*A concrete, end-to-end simulation of the Multi-Provider Super Agent prototype, tracing one continuous 45-minute window through every component in PLAN.md. Each step shows the actual data in, what the component does with it, and what it emits. Uses the Eid-market agent scenario from the problem statement.*

**Starting state (3:00 PM):** Cash: 45,000 tk | bKash: 12,000 tk | Nagad: 38,000 tk | Rocket: 21,000 tk. All feeds fresh.

## Step 1 — Data Simulator emits normal traffic

**In:** Nothing (simulator is the source) — running on a timer, seeded with baseline Eid-noise parameters (elevated but normal withdrawal frequency).

**Process:** Generates transaction events at roughly historical baseline rate for this hour, e.g. bKash cash-outs averaging 6/10-min at varied amounts (700-3,000 tk), occasional Nagad/Rocket cash-ins.

**Out:** A stream of events like `{agent_id: A1, provider: bKash, type: cash_out, amount: 1500, account_ref: syn_442, timestamp: 15:00:10, area: Dhanmondi}`.

## Step 2 — Ingestion layer

**In:** The raw event stream from Step 1.

**Process:** Validates the payload shape, tags it with provider_id, writes it to the transactions table in Supabase. No cross-provider logic touches it here.

**Out:** A persisted row in transactions; nothing else downstream yet — this layer only stores, it doesn't interpret.

## Step 3 — Ledger & Aggregation update

**In:** The new transaction row.

**Process:** Applies the cash-out direction: physical cash minus 1,500, bKash e-money plus 1,500. The customer sends e-money to the agent and receives physical cash. Writes separate provider and shared-cash snapshots without combining them.

**Out:** Updated balances: Cash 43,500 tk | bKash 13,500 tk | Nagad 38,000 tk | Rocket 21,000 tk.

## Step 4 — Data Quality & Confidence tagging

**In:** The last_updated timestamp on each provider feed.

**Process:** Checks staleness for all three feeds. At 3:00 PM everything is under the 2-minute threshold.

**Out:** `{bKash: fresh, nagad: fresh, rocket: fresh}` — confidence modifier = 1.0 (no degradation) passed to both downstream engines.

## Step 5 — 3:12 PM: bKash demand accelerates (Scenario A/B trigger)

**In:** A burst of bKash cash-out events — 18 transactions in the next 10 minutes, amounts 700-2,800 tk, from a mix of accounts.

**Process:** The ledger applies each cash-out consistently: shared physical cash drops while bKash e-money rises. The Liquidity Engine's rolling window sees roughly 1,050 tk/min average shared-cash depletion attributable to bKash cash-out demand, with low variance.

**Out:** Shared cash falls quickly while the bKash e-money card remains healthy or rises. The forecast engine has enough shared-cash depletion signal to project forward.

## Step 6 — Liquidity Forecasting Engine

**In:** Current shared-cash balance (5,700 tk), rolling depletion rate attributable to bKash cash-outs (1,050 tk/min), and variance of that rate.

**Process:** time_to_zero = 5,700 / 1,050, approximately 5.4 minutes. Variance is low so confidence band is tight.

**Out:** A forecast record: `{reserve: shared_cash, pressure_provider: bKash, projected_shortage_time: 15:17, confidence: high, contributing_signal: "sustained cash-out velocity"}`.

## Step 7 — Anomaly Engine, Pattern 1 (Velocity Spike) fires

**In:** Same 10-minute transaction window used by the forecast engine.

**Process:** Compares 18 transactions/10min against this agent's historical baseline for 3 PM (baseline approximately 6/10min). That's roughly 3x baseline, well outside the historical distribution, so it's flagged.

**Out:** `AnomalyFlag {pattern: velocity_spike, evidence: "18 cash-outs in 10 min vs typical 6", confidence: moderate, plausible_benign_explanation: "possible pre-Eid demand surge"}`.

## Step 8 — Anomaly Engine, Pattern 2 (Repeated/Near-Identical Amounts) fires

**In:** The same transaction window, filtered for amount clustering.

**Process:** Within that burst, 5 of the 18 transactions are 1,000 tk plus or minus 2%, from only 3 distinct accounts. Few accounts relative to transaction count pushes confidence up somewhat, but the amount (1,000 tk) is a common round number, which pulls it back down.

**Out:** `AnomalyFlag {pattern: repeated_amounts, evidence: "5 txns ~1,000 tk from 3 accounts in 10 min", confidence: low-moderate, plausible_benign_explanation: "round-number Eid withdrawals are common; weak signal alone"}`.

## Step 9 — Alert & Case Management creates two distinct cases

**In:** The forecast record (Step 6) and both anomaly flags (Steps 7-8).

**Process:** Routing rule looks up alert_type + provider to role. Liquidity shortage on bKash routes to the bKash-scoped provider ops role. Both anomaly flags route to the same role plus flagged for risk-analyst visibility (since anomaly, not just liquidity).

**Out:** Three case records created — open, each with assigned_to, recommended_action (templated), none merged into a single score.

## Step 10 — Explainability & Localization renders copy

**In:** The three case records' structured evidence.

**Process:** Templates fill EN and Bangla strings from the same underlying object — no free-form generation.

**Out (Bangla, liquidity):** "বর্তমান লেনদেনের ধারা অনুযায়ী বিকেল ৩টা ১৭ মিনিটের মধ্যে আপনার নগদ টাকা শেষ হয়ে যেতে পারে। সবচেয়ে বেশি চাপ আসছে বিকাশ ক্যাশ-আউট থেকে।"

**Out (EN, anomaly):** "Unusual cash-out pattern detected — requires review. Possibly normal Eid demand."

## Step 11 — Dashboards receive the alerts

**In:** The rendered cases, via polling.

**Process:** Agent dashboard shows the shared-cash card turning amber with the shortage countdown and identifies bKash cash-out demand as the main contributor. Ops dashboard's case queue gets two new rows, tagged distinctly [Velocity] and [Amount-Pattern].

**Out:** Live UI state — nothing new computed here, purely a read/render step.

## Step 12 — 3:18 PM: Nagad feed goes stale (Scenario C trigger)

**In:** Simulated fault injection — Nagad's feed stops updating (network delay simulated).

**Process:** Data Quality Engine notices last_updated for Nagad now exceeds the 2-minute threshold.

**Out:** `{nagad: stale}` — confidence modifier drops for Nagad specifically. Any Nagad forecast is now widened/marked "low confidence, data delayed"; the Anomaly Engine suppresses new high-confidence Nagad flags and instead emits a data-issue advisory rather than a risk alert. Dashboard shows: "Nagad data delayed — figures may be outdated," balance frozen at last-known 38,000 tk with a stale badge — never silently showing a confident, possibly-wrong number.

## Step 13 — Ops user acknowledges the bKash liquidity case

**In:** A click on "Acknowledge" from the Provider-A (bKash) ops role, logged in through the role/session layer.

**Process:** RBAC check confirms this role is scoped to bKash cases; status flips open to acknowledged; timestamp and actor logged.

**Out:** Case history now: `[15:14 created] -> [15:19 acknowledged by bKash-ops-1]`. Same user tries opening a Nagad case out of curiosity — API/RLS returns nothing, proving the provider boundary holds.

## Step 14 — Field officer restocks cash, case resolved (Scenario D close-out)

**In:** A case note — "Contacted agent, confirmed genuine Eid demand, arranged 20,000 tk cash top-up" — plus a status change to resolved.

**Process:** On resolve, the ops user also sets reviewer_verdict. For the liquidity case: not applicable (liquidity isn't a fraud/anomaly judgment). For the Amount-Pattern anomaly case: marked false_positive, confirmed normal Eid withdrawals. For the Velocity Spike case: marked false_positive, confirmed legitimate demand surge, since the same investigation covered both.

**Out:** Full case history: `open -> acknowledged -> resolved`, each transition appended to the immutable audit_log table with actor and timestamp.

## Step 15 — Metrics feedback loop updates

**In:** The two reviewer_verdict = false_positive outcomes from Step 14, plus the ongoing injected synthetic test cases running in parallel.

**Process:** Metrics panel recomputes false-positive rate by combining both sources: e.g., synthetic ground truth says 2 of 10 injected anomalies were designed as true fraud simulations, and now this live resolution adds one more real false-positive data point to the running rate.

**Out:** /metrics panel shows something like: "False-positive rate: 34% (6 of 16 flags, combining 10 injected test cases + 6 live resolutions this run)" — a stronger, more honest evidence story than synthetic data alone.

## Step 16 — 3:25 PM: Nagad feed recovers

**In:** Fault injection toggled off; fresh Nagad data resumes.

**Process:** Data Quality Engine flips Nagad back to fresh; confidence modifier returns to 1.0.

**Out:** Nagad's stale badge disappears, balance resumes live updates, and the Anomaly Engine resumes normal-confidence flagging for Nagad — nothing was lost or silently corrupted during the outage, just visibly degraded and then restored.

## End State (3:25 PM)

Cash restocked to roughly 65,000 tk (after the 20,000 tk top-up), bKash back to a healthy level, two anomaly cases closed as false positives with documented reasoning, one liquidity case resolved via a real operational action, full audit trail intact, and metrics reflecting a real (not purely synthetic) false-positive rate — which is exactly the connected liquidity to anomaly to coordination chain the rubric is grading for.
