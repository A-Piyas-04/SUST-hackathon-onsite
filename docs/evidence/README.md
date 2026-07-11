# Phase 7 — Validation & Safety Evidence

Machine-generated evidence for the frozen release-candidate MVP. **Do not
hand-edit** — every number here is produced by the commands below and traces back
to the recorded release-candidate identifier (git commit + contract version +
engine versions) embedded in each artifact.

## Commands

```bash
cd backend
make validate      # held-out evaluation -> validation-summary.json + performance-reliability.json
make safety-scan   # secrets / unsafe-endpoint / prohibited-language -> safety-security-scan.json
```

(`make validate` == `python -m app.scripts.validation_cli run`;
`make safety-scan` == `python -m app.scripts.safety_scan`. Both read the DB
connection from `backend/.env`.)

## Artifacts

| File | Produced by | Contents |
|------|-------------|----------|
| `validation-summary.json` | `make validate` | Latest completed held-out run with every persisted metric (analytics + performance + reliability). |
| `performance-reliability.json` | `make validate` | Performance (latency) and reliability measurements only. |
| `safety-security-scan.json` | `make safety-scan` | Pass/fail per scan, with counts and any explicit waivers. |

## Metric definitions (held-out split, frozen before measurement)

All metrics are computed on the `held_out` scenarios A/B/C (seeds 2001/2002/2003);
`normal` and `scenario_d` (`demo` split) are excluded from reported metrics.

| Code | Category | Definition |
|------|----------|------------|
| `anomaly_precision` | analytics | TP / (TP + FP) over held-out (scenario × provider) anomaly cells; alertable = `requires_review` flag. |
| `anomaly_recall` | analytics | TP / (TP + FN) over held-out labelled anomaly cells. |
| `anomaly_false_positive_rate` | analytics | FP / (FP + TN) over anomaly-negative cells (includes the suppressed data-quality case, which must not alert). |
| `shortage_lead_time_minutes` | analytics | `projected_shortage_at − as_of_at` for the held-out Scenario A shared-cash projection. |
| `data_quality_incident_rate` | reliability | Share of provider feed assessments classified stale/missing/conflicting across held-out runs. |
| `alert_explanation_coverage` | reliability | Published high-impact alerts with a complete EN explanation (situation, evidence, uncertainty, next step) / total. |
| `api_avg_ms`, `api_p95_ms` | performance | In-process latency of the dashboard, liquidity-projections, and anomaly-flags read handlers (excludes network transport). |

Honesty note: metrics are measured on a small synthetic held-out set with a
single anomaly rule. Values (including perfect precision/recall) reflect that
scope and are **not** production evidence. Limitations are recorded per metric in
`validation-summary.json`.

Full prose documentation (data & simulation note, responsible-design note) is a
Phase 8 deliverable.
