# ADR 0005 — Enforcing "every published alert cites ≥1 analytical/quality source"

- **Status:** Accepted
- **Phase:** 1
- **Relates to:** `docs/schema.md` §10.2, §13.11; task §7 (alerts)

## Context

`schema.md` §13.11 mandates: "Every published alert cites at least one projection,
anomaly flag, or data-quality assessment." The three source links live in separate
join tables (`alert_liquidity_projections`, `alert_anomaly_flags`,
`alert_quality_assessments`), so a plain per-row `CHECK` on `alerts` cannot express
"a row exists in at least one of three child tables". A naive `NOT NULL` cannot model
the one-of-three, cross-table requirement, and a row-insert trigger on `alerts` would
fire before any child link can be inserted.

## Decision

Model **publication** explicitly and enforce the rule at publication time:

- `alerts.state` starts `active` only once published. A **`CONSTRAINT TRIGGER`
  (`DEFERRABLE INITIALLY DEFERRED`)** on `alerts` validates, at transaction commit,
  that any alert whose `state = 'active'` has at least one row across the three source
  link tables. Inserting an alert and its source link(s) in the same transaction
  passes; committing an active alert with no source link raises an error.
- The same deferred check also enforces §10.2's rule that an anomaly flag with
  `disposition = 'suppressed_data_quality'` **cannot** be linked to an `anomaly` or
  `combined` alert (validated on the `alert_anomaly_flags` insert trigger as well, so
  the violation is caught immediately).

## Consequences

- **Compatibility:** Fully implements §13.11 and §10.2 at the database layer; no change
  to `schema.md`'s table shapes. The application still owns higher-level publication
  workflow, but the DB is the backstop.
- **Security/safety:** An alert cannot become active (and thus route a case) without
  cited evidence; suppressed anomalies cannot masquerade as anomaly-alert sources.
- **Operational note:** Because the check is deferred, producers must insert the alert
  and its source links within one transaction. This is documented for Phase 5.
- **Rollback:** The constraint trigger is additive and can be dropped in a forward
  migration if the publication model changes.
