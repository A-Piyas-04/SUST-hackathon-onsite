# ADR 0006: Velocity Spike and Balance Inconsistency Anomaly Detectors

## Status

Accepted — 2026-07-12

## Context

The anomaly engine previously implemented only `near_identical_amounts`. The
`anomaly_pattern` enum and schema already defined `velocity_spike` and
`balance_inconsistency`, but no detector code or active seed rules existed.

## Decision

1. **Implementation** — Add `detect_velocity_spike` and
   `detect_balance_inconsistency` in `backend/app/services/anomaly/engine.py`,
   following the same `AnomalyResult` → `ResultEnvelope` → `AlertCandidate`
   pipeline, suppression guardrails, evidence structure, and safe-language
   benign explanations as the existing near-identical detector.

2. **Runner dispatch** — Replace the hardcoded `_active_rule` query with
   `_active_rules` so every `is_active` row in `anomaly_rules` runs
   independently per provider/outlet. No combined risk score is introduced.

3. **Configuration** — Default thresholds live in
   `backend/app/services/analytics/config.py` and are overridden per rule via
   `anomaly_rules.configuration` JSON.

4. **Schema** — No table or column changes. Historical baselines for velocity
   are computed in-memory from the provider-scoped transaction window already
   loaded by the runner. Balance reconciliation uses existing
   `provider_balance_snapshots` and `transactions` (with `transaction_type`).

5. **Migration** — Forward-only seed migration `009_anomaly_velocity_balance_rules.sql`
   inserts active rule rows; `reference_seed.sql` updated for fresh installs.

## Consequences

- Analytics runs may produce up to three independent anomaly flags per provider
  (one per pattern), each with a distinct `pattern` identifier.
- Velocity detection requires sufficient same-hour baseline windows in the
  input data; otherwise it returns `inconclusive`.
- Balance inconsistency confidence decreases as feed staleness increases, framing
  stale conflicts as likely sync delays rather than reviewable integrity issues.
