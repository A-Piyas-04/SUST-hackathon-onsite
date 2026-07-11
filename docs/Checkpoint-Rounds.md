# Checkpoint Judging Prep — Round 1 (Hour 3) and Round 2 (Hour 10.5)

*Based on the MVP prioritization in PLAN.md, mapped against the two mid-build judging checkpoints ahead of final judgment at hour 24.*

## Round 1 — Hour 3 (~2 hours of actual build time in)

### 1. Realistic build state

Hour 3 is roughly 2 hours past your effective start (1 hour was already gone before the 23-hour clock began). Against the MVP prioritization in PLAN.md, hour 3 sits inside the very start of "Build First" (Hours 1-10). Assuming normal pace with some slippage — setup always eats more time than planned — here's what's genuinely likely to exist:

- Supabase project created, core schema in place (agents, provider_balances, transactions; forecasts/alerts/cases tables may just be stubs).
- Data simulator running and producing plausible multi-provider transaction events (bKash/Nagad/Rocket), possibly still command-line only, not fully wired through the API.
- A basic ingestion endpoint receiving events and writing real rows to the DB.
- A rough dashboard shell showing cash + 3 provider balances updating from real data — this is the most important thing to have working, even if styling is ugly.
- **Not yet working, realistically**: liquidity forecasting, any anomaly detector, alerting, RBAC, Bangla copy. That's fine — none of that was scheduled to be done this early.

Don't fight this. If you're roughly here, you're on pace, not behind.

### 2. What to actually demo

The smallest coherent slice: **live, real (not mocked) data flowing from simulator to ingestion to unified balance dashboard**, with cash and each provider's e-money balance shown separately, never summed into one figure.

Don't attempt Scenario A, B, C, or D live — none of the analytical layer exists yet, and forcing a scenario you can't back with real logic will look worse than not showing one. If you want to reference a scenario, do it verbally over the architecture diagram ("this is where Scenario A's shortage forecast will plug in") rather than trying to fake it live.

### 3. What judges are likely evaluating at this stage

At hour 3, judges know every team is mid-build. They're not grading completeness — they're grading **Problem Understanding and Ecosystem Relevance (15%)** and early signs of **Technical Implementation** direction (part of the 25%), specifically:
- Do you actually understand the multi-provider, provider-boundary, three-connected-problems framing, or are you building a generic dashboard?
- Is there a real, running technical foundation (actual data flowing) versus slides and intentions?

Innovation (20%), Data Quality (20%), and Coordination (part of 25% + UX 10%) aren't realistically gradable yet and you shouldn't pretend otherwise. Lead with problem understanding; use the working simulator plus dashboard as proof you're not just talking.

### 4. What to say if something isn't built yet

Be direct and specific rather than vague:

> "The three-problem chain — liquidity, anomaly, coordination — is fully scoped and the architecture is locked. Right now you're seeing the foundation: real synthetic transactions flowing into separated provider balances, no blending, ever. The forecasting and anomaly layers are next — they read directly off this same ledger, which is why we built the ledger and provider separation first, since everything downstream depends on it being correct."

This frames the sequencing as deliberate engineering discipline, not delay. Naming the next two things you're building (forecast, anomaly) shows a plan, not scrambling.

### 5. Pre-checkpoint checklist (10-15 min before Round 1)

- Simulator running and actively emitting events — restart it fresh 5 minutes before so the dashboard shows live movement, not stale numbers.
- Dashboard loads with no console errors; hard-refresh once to confirm.
- Have the architecture diagram (even hand-drawn/rough) open in a second tab — this is your main visual aid since the product itself is thin.
- One-sentence versions ready for: the problem, the three provider boundary rule, and what's built vs. next.
- Know your own numbers — if asked "how many transactions per second," don't guess live; know the actual figure from your simulator config.

---

## Delta: What Must Change From Round 1 to Round 2

By hour 10.5 you're at the tail end of "Build First" and well into "Build Second." Judges should see clear forward motion on the same three-problem chain, not a repeat of the balance dashboard with new colors. Concretely, between the two checkpoints you need to add:
- The liquidity forecast with a visible confidence indicator — turns the static balance view into decision-support.
- At least one, ideally two, anomaly detectors actually firing on real evidence with false-positive framing — this is the single biggest visible jump, since it didn't exist at all in Round 1.
- The beginning of the coordination layer — even a partial alert record with an assigned owner, even if acknowledge/escalate/resolve isn't fully wired yet.

If Round 2 looks like "the same dashboard, more polished," that reads as no progress on the parts that carry the most weight (Innovation 20%, Data Quality 20%). If it shows forecast plus anomaly evidence live, that's a legible, honest trajectory toward the full submission checklist.

---

## Round 2 — Hour 10.5

### 1. Realistic build state

Hour 10.5 sits right at the boundary where PLAN.md's "Build First" (Hours 1-10) should be wrapping and "Build Second" (Hours 10-19) is starting. With normal slippage, a realistic honest state looks like:

- Balance dashboard fully live (carried over from Round 1, now polished).
- Liquidity forecast with confidence band working for at least one or two providers — possibly not perfectly tuned, but functionally real.
- **Velocity Spike detector** working end-to-end: evidence shown, false-positive framing present, confidence badge.
- **Repeated/Near-Identical Amounts detector**: likely either working but rough, or partially built (detection logic done, evidence UI not finished). This is the realistic slippage point — don't assume both are fully polished.
- Balance Inconsistency (3rd pattern) — probably not started; that's fine, it was always "if hours 1-10 finished on schedule."
- Alert/case model: likely just a data model with an "open" status and an assigned owner field populated — full acknowledge to escalate to resolve lifecycle is probably not wired yet, since that's early Build Second work.
- RBAC/RLS, Bangla copy, filters: not started — all correctly scheduled later or as stretch.

### 2. What to actually demo

The smallest coherent slice now: **Scenario A into Scenario B, live.** Show the liquidity forecast catching shared physical cash sliding toward shortage under one provider's heavy cash-out demand, with a stated confidence level. Then show the Velocity Spike anomaly firing on the same underlying transaction stream — explicitly narrate that this is the same data, same agent, two distinct engines (forecast + anomaly) both reading it, which is exactly the "connected chain, not three cards on a dashboard" story the rubric rewards.

If the second detector (Repeated Amounts) is working even roughly, show it as a second, separately tagged alert — this is your strongest single moment to demonstrate you're not doing single-pattern anomaly detection. If it's not stable enough to demo live, don't force it — describe it accurately (see point 4) rather than risk a crash on stage.

Don't attempt full Scenario D (coordination) live if the lifecycle isn't wired — showing an alert with an owner field populated is enough; you don't need acknowledge/resolve working yet to make the point that ownership routing exists.

### 3. What judges are likely evaluating at this stage

By hour 10.5, judges shift toward **Innovation and Decision Value (20%)** and **Data & Analytical Quality (20%)** — this is exactly where the forecast-plus-anomaly demo earns points, since it's the first point where real analytical output exists. They'll also start probing **Technical Implementation (25%)** for actual integration depth (is this really wired end-to-end, or three disconnected scripts?) — which is why showing forecast and anomaly firing off the same live transaction stream matters more than showing either in isolation.

Coordination/UX (part of 25% + 10%) is not expected to be complete yet at this checkpoint — judges scoring reasonably will expect that to mature toward final judgment, not be finished at the halfway mark.

### 4. What to say if something isn't built yet

Be specific about exactly what's live versus in progress, and tie it back to your own priority order so it reads as intentional sequencing, not gaps:

> "Two anomaly patterns are live right now — velocity spikes and repeated-amount clustering — both with evidence and an explicit false-positive framing, since we treat neither as proof of fraud. A third pattern, balance inconsistency for Scenario C, is scoped and next. On coordination: the alert already carries an assigned owner from our routing rules; the acknowledge-and-resolve workflow is what we're wiring right now, since we deliberately built the analytical engines first — an alert with no real evidence behind it isn't worth routing to anyone."

This makes the missing piece (full case lifecycle) sound like a natural next step off a working analytical core, not a missed deadline.

### 5. Pre-checkpoint checklist (10-15 min before Round 2)

- Reset the simulator/data to a known-good state that reliably triggers both the forecast shortage and at least one anomaly pattern — don't rely on random timing to produce the right conditions live.
- Confirm both anomaly detectors independently, in isolation, right before the demo — if one is flaky, decide now whether to show it or describe it, don't decide live on stage.
- Have the evidence panel and confidence badges actually populated with real numbers you can read off, not placeholders.
- Rehearse the exact transition line from liquidity forecast into anomaly alert — this connective narration is what turns "two features" into "one story," and it's the single easiest thing to under-rehearse.
- Prepare one honest, pre-written sentence for the coordination-layer status (see point 4) so you're not improvising it under time pressure.
- If you built any part of RBAC/RLS or Bangla copy ahead of schedule, decide in advance whether it's stable enough to show — a working stretch item shown confidently helps; a half-working one shown nervously hurts.
