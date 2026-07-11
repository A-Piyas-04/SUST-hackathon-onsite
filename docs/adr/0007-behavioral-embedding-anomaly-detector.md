# ADR 0007: Behavioral Embedding Anomaly Detector

## Status

Accepted — 2026-07-12

## Context

Feature 2 in `docs/AI_ML_FEATURES.md` requires a fourth, independent anomaly
detector that flags transactions sitting unusually far from an outlet's own
historical behavior neighborhood. The three existing rule-based detectors
(near-identical amounts, velocity spike, balance inconsistency) cannot catch
patterns that were never named in advance.

## Decision

1. **Algorithm** — k-nearest-neighbor mean Euclidean distance in a five-dimensional
   feature space (amount, time-of-day, party frequency, provider code, transaction
   type). No autoencoder or offline training step; vectors are computed in-memory
   from the provider-scoped transaction list already loaded by the runner.

2. **Scoping** — Neighborhood history is built strictly from transactions with
   `occurred_at < candidate.occurred_at` within the same outlet/provider account
   list passed to the detector. No cross-outlet or cross-provider comparison.

3. **Cold start** — Below `minimum_history_transactions` (default 10), the
   evaluation is persisted with `disposition=inconclusive` and
   `reason_code=insufficient_history` for metrics/debugging but never alertable.
   This differs from velocity's `persist=False` path and follows the user's
   store-for-metrics requirement plus Liquidity's non-actionable-below-threshold
   spirit.

4. **Evidence** — Alertable candidates must include real nearest-neighbor
   transaction records, not a distance score alone.

5. **Integration** — Same `AnomalyResult` → `ResultEnvelope` → `AlertCandidate`
   pipeline, quality suppression via `_is_degraded_quality`, and pattern tag
   `behavioral_embedding`. No changes to the three existing detector functions.

6. **Schema** — Forward migration `010_behavioral_embedding_anomaly.sql` extends
   the `anomaly_pattern` domain and inserts an active seed rule. No new tables.

## Consequences

- Analytics runs may produce up to four independent anomaly flags per provider
  (one per active pattern).
- Outlets with fewer than 10 prior transactions for a provider produce
  non-actionable insufficient-history flags only.
- Confidence scales with the ratio of candidate distance to the outlet's typical
  neighbor-distance spread, then applies the quality modifier.
