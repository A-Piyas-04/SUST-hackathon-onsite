# AI/ML Feature Additions — Design Documentation

*Multi-Provider Agent Liquidity & Coordination Platform*

This document specifies three AI/ML additions selected to satisfy the mandatory AI/ML requirement (Problem_Statement.md, Section 7) without altering the existing rule-based core the system already relies on for explainability. Each feature is additive: it plugs into a slot the architecture already exposes, consumes data the system already produces, and can be removed without breaking any existing module.

None of these features replace or override the deterministic logic already documented in System-Design.md or the analytics engine reference. They sit alongside it.

---

## Feature 1: Learned Confidence Calibration

**Module**: QUALITY
**Replaces**: The fixed penalty formulas in the confidence-modifier pipeline (Step 3 of the existing three-step calculation)
**Type**: Supervised learning (logistic or isotonic regression) on human-labeled feedback

### The Problem With the Current State

Today, each provider's trust score is computed from hand-picked constants:

- Feed status sets a fixed base modifier (fresh = 1.0, stale = 0.6, conflicting = 0.4, missing = 0.0)
- Low sample count applies a fixed ratio penalty
- Rejected events apply a fixed penalty with a hard floor of 0.3

These numbers are reasonable defaults, but nobody has ever confirmed they're the *right* numbers. A stale Nagad feed always costs exactly 40% of trust, whether that staleness has historically correlated with meaningfully worse forecasts or not. The formula cannot learn from experience.

### How It Works

Once the Case module has been in use for a while, every resolved case carries a `case_reviews.was_false_positive` outcome — a human's real judgment on whether an alert (and the confidence level attached to it at the time) was trustworthy. Combined with the injected synthetic ground-truth scenarios from the simulator, this produces a labeled dataset:

| Input Features | Label |
|---|---|
| Feed status, sample count, rejection rate, staleness age | Was the resulting alert/forecast actually reliable? (from `case_reviews` + synthetic ground truth) |

A small logistic regression (or isotonic regression, if a monotonic relationship is preferred) is trained on this dataset. Its output replaces the fixed Step 3 formula: instead of `modifier × (sample_count / min_samples) × rejection_penalty`, the model directly predicts a calibrated confidence modifier from the same inputs.

Critically, this stays fully explainable: a logistic regression's coefficients tell you exactly how much each input contributed to the final score. That breakdown can be shown directly in the evidence panel — e.g., "Confidence lowered primarily due to sample count (contributed -0.31), staleness contributed -0.09" — which is a *stronger* explainability story than the current fixed formula, not a weaker one.

### End-to-End Flow

1. **Data collection (passive, ongoing)**: Every time a case is resolved with a reviewer verdict, the outcome is logged alongside the confidence modifier and quality inputs that were active when the alert fired. No new UI or user action required — this piggybacks on the existing Case workflow.
2. **Training (offline, before or between demo runs)**: A script pulls all `case_reviews` + synthetic ground-truth records, trains the regression model, and saves the fitted coefficients.
3. **Inference (runtime, replaces Step 3)**: When the Quality module runs during an analytics cycle, instead of applying the fixed penalty formulas, it feeds the same inputs (feed status, sample count, rejection rate, staleness) into the trained model and receives a calibrated modifier back.
4. **Consumption (unchanged)**: The Liquidity Engine and Anomaly Engine consume this modifier exactly as they do today — `final_confidence = sample_adequacy × quality_modifier`, non-actionable below threshold, wider uncertainty bands below 1.0. Neither engine needs to know the modifier is now learned rather than fixed.
5. **Display (unchanged, richer)**: The Dashboard's feed-health badge and the alert evidence panel show the same modifier value as before, with an added breakdown of which input contributed how much.

### Improvement Over Current State

- **Before**: A stale feed always costs exactly 40% trust, regardless of whether staleness has actually predicted bad outcomes in this system's own history.
- **After**: The penalty reflects what has actually correlated with real reviewer-confirmed outcomes, and gets more accurate the more the system is used.
- The feature turns an existing, already-required module (Quality/confidence scoring) into a visible example of the system learning from its own operational history — directly strengthening the "false positives, uncertainty, and data-quality failure modes are acknowledged and tested" success criterion, since the model's accuracy against held-out labels becomes a reportable validation metric.

---

## Feature 2: Embedding-Based Behavioral Anomaly Detector

**Module**: ANALYZE (Anomaly Engine)
**Adds to**: The existing rule-based detectors (velocity spike, near-identical amounts, balance inconsistency) as a fourth, independent pattern
**Type**: Unsupervised learning (vector similarity / nearest-neighbor distance, or a lightweight autoencoder)

### The Problem With the Current State

The existing three anomaly detectors are strong, but each one only catches what it was explicitly written to catch. A transaction that doesn't match any named rule — but still doesn't look like anything this particular outlet normally does — currently passes through undetected. Rule-based detection is precise but has a fixed blind spot: it can't catch a pattern nobody thought to name in advance.

### How It Works

Every transaction is converted into a small feature vector: amount, time-of-day, party/account frequency for that outlet, provider, and transaction type. Over time, each outlet builds up a "neighborhood" of what its typical transactions look like as vectors in this feature space.

For each new transaction, the system computes its distance to that outlet's typical neighborhood — using k-nearest-neighbor distance, or the reconstruction error from a simple autoencoder trained on that outlet's normal history. A transaction sitting unusually far from the outlet's typical pattern gets flagged, exactly the same way the existing three detectors flag their specific patterns — as a `ResultEnvelope`, then an `AlertCandidate`, following the identical pipeline the other three already use.

The key design choice that keeps this consistent with the existing anomaly philosophy: **the evidence shown is the nearest historical neighbors themselves**, not an opaque distance score. The alert says "this transaction sits unusually far from this outlet's typical bKash pattern — here are the 3 closest historical transactions for comparison," so a reviewer can see *why* it looked odd by comparing it directly, the same way they'd review evidence for any of the other three patterns.

### End-to-End Flow

1. **Feature extraction (runtime, per transaction)**: As each normalized transaction arrives from LEDGER, the anomaly engine computes its feature vector alongside the existing rule checks — this runs in parallel with, not instead of, the three existing detectors.
2. **Neighborhood comparison**: The vector is compared against that specific outlet's historical transaction vectors (built up from the outlet's own transaction history, never across outlets — preserving the same provider/outlet separation principle used everywhere else in the system).
3. **Distance scoring and threshold check**: If the distance exceeds a threshold (tunable, and itself feedable through the same Quality-derived confidence suppression logic the other detectors use — a low-confidence feed suppresses this detector's alerts too, exactly as it does for the other three), a candidate anomaly is generated.
4. **Evidence assembly**: The candidate is packaged with its nearest historical neighbors as evidence, a plausible-benign-explanation field (e.g., "could reflect a new but legitimate customer pattern"), and a confidence level based on how far outside the neighborhood the transaction sits.
5. **Publication (unchanged)**: The candidate flows through ALERT exactly like the other three patterns — deduplicated, frozen as an immutable alert, explained through the same template system, tagged distinctly as its own pattern type so it never merges into another detector's evidence.
6. **Human review (unchanged)**: Appears in the Case module exactly like any other anomaly alert, reviewed and resolved the same way, feeding the same `case_reviews` feedback loop that Feature 1 depends on.

### Improvement Over Current State

- **Before**: Detection is limited to three specifically-named patterns. Anything that doesn't match velocity spikes, near-identical amounts, or balance conflicts is invisible to the system, however unusual it may genuinely be.
- **After**: A fourth, independent detector catches "doesn't look like this outlet's normal behavior" cases that don't fit any predefined rule — without replacing or weakening the existing three, and without introducing an opaque risk score, since the evidence shown is always concrete historical comparisons.
- This is also the clearest, most literal answer to a "where is the ML" question, since the existing three detectors are statistical/rule-based rather than learned — this is the one addition that is unambiguously a machine-learning technique (vector similarity / distance-based outlier detection) rather than threshold logic.

---

## Feature 3: RAG Similar-Case Retrieval

**Module**: CASE
**Adds to**: The evidence shown when a case is opened from an alert
**Type**: Retrieval-augmented context (embedding similarity search over past resolved cases — no generation involved)

### The Problem With the Current State

Right now, when a reviewer opens a case, they see the evidence for *that* alert in isolation. If a nearly identical situation was already reviewed and resolved as a false positive last week, the current reviewer has no way to know that unless they happen to remember it themselves. Institutional memory about what's "normal for this outlet" or "already reviewed and dismissed" isn't surfaced anywhere.

### How It Works

Each resolved case's notes and resolution summary (`case_notes`, `case_reviews.summary`) are embedded into a vector representation as soon as the case is resolved. When a new anomaly alert is published and a case is opened from it, the system embeds the new case's evidence summary the same way and retrieves the most similar past cases by vector distance — a straightforward similarity search, with no text generation involved anywhere in the process.

The retrieved cases are shown as-is: their outcome, their resolution summary, and how similar they were. This is pure retrieval — the system is not summarizing, paraphrasing, or generating anything; it is surfacing existing human-written records that already exist in the database.

### End-to-End Flow

1. **Indexing (passive, on every case resolution)**: When a case is resolved, its evidence summary and resolution text are embedded and stored alongside the existing case record — no new user action, just an additional write at a step that already happens.
2. **Query (runtime, when a case is opened)**: When an ops user opens a case from a newly published alert, the new case's evidence summary is embedded the same way.
3. **Retrieval**: A similarity search runs against the index of previously resolved cases, scoped to the same provider (preserving the provider-boundary principle — a bKash case never retrieves a Nagad case as a similar match) and returns the closest matches, e.g., the top 3.
4. **Display**: The case view shows a "Similar past cases" panel alongside the existing evidence: each retrieved case's outcome (e.g., "resolved as normal demand" or "confirmed review-worthy"), its resolution summary, and how similar it was.
5. **Human decision (unchanged)**: The reviewer still performs every existing action — acknowledge, note, escalate, resolve — exactly as before. The retrieved cases are additional context displayed alongside the existing evidence panel, never a decision made on the reviewer's behalf.

### Improvement Over Current State

- **Before**: Each case is reviewed in isolation. A pattern that's been seen and dismissed multiple times before provides no benefit to the next reviewer who encounters it.
- **After**: A reviewer opening a new case immediately sees how similar situations were handled before, turning the system's own operational history into a visible, reusable resource — directly reinforcing the false-positive-awareness story the rubric explicitly rewards, since "3 similar past cases, 2 resolved as normal Eid demand" makes that awareness concrete and evidenced rather than asserted in a document.
- This is the cheapest of the three to build (no model training required, just embedding + similarity search over data the system is already storing) and has no dependency on the other two features, so it can be built independently.

---

## Summary Comparison

| Feature | Module | Technique | Data Required | Replaces or Adds To | Effort |
|---|---|---|---|---|---|
| Learned Confidence Calibration | QUALITY | Supervised regression | `case_reviews` + synthetic ground truth | Replaces fixed penalty formula | Low-medium |
| Embedding-Based Anomaly Detector | ANALYZE | Vector similarity / distance-based outlier detection | Per-outlet transaction history | Adds a 4th independent detector | Medium |
| RAG Similar-Case Retrieval | CASE | Embedding similarity search (retrieval only, no generation) | `case_notes` + `case_reviews` text | Adds a context panel to case view | Low |

## Guardrails Preserved by All Three

- No feature makes a decision, transitions a case state, or takes any action a human hasn't explicitly triggered.
- No feature merges provider data — the anomaly detector's neighborhood is per-outlet, and the case retrieval search is scoped per-provider.
- No feature generates free-form text presented as system output — Feature 3 is pure retrieval, Feature 1 and 2 only ever affect a numeric score or evidence selection.
- Every feature degrades gracefully if removed: the system's existing rule-based logic continues to function identically without any of the three in place.
- All three keep the evidence-first principle: a score or flag is never shown without the underlying data that produced it (regression coefficients, nearest neighbors, or retrieved case records, respectively).

## Suggested Build Priority

1. **Learned Confidence Calibration** — cheapest to justify, reuses existing feedback data, strengthens an already-mandatory module.
2. **Embedding-Based Anomaly Detector** — highest differentiation value, most unambiguous "this is ML" answer.
3. **RAG Similar-Case Retrieval** — cheapest to build, independent of the other two, strong false-positive-awareness narrative.

Build in this order if time is constrained; each is independently valuable and none depends on the others being complete first.
