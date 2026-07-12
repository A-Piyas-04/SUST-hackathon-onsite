# Validation evidence

## Scope and release identity

Judge-facing metrics below were **measured** by the Phase 7 held-out harness (`app.services.validation.harness` + `performance`) against frozen Scenario A/B/C runs (seeds `2001` / `2002` / `2003`). They are **not** the fixture-authored moderate-dataset table that previously appeared here.

| Field | Value |
|---|---|
| Implementation revision measured | `8d3600bcdc7a41dc606fff9a0e231240a5851af1` |
| Validation run id | `1b911d32-06ea-4104-b3cb-b949d53b174e` |
| Dataset split | `held_out` |
| Engine version | `validation-v1` |
| Frozen seeds | scenario_a=`2001`, scenario_b=`2002`, scenario_c=`2003` |
| Outlet | `0b000000-0000-0000-0000-000000000001` |
| Generated at (UTC) | `2026-07-12T00:10:10Z` |
| Quality confidence mode | `fixed_formula` (learned calibration artifact temporarily sidelined for this measurement — see note below) |
| Raw artifacts | [`evidence/validation-summary.json`](evidence/validation-summary.json), [`evidence/performance-reliability.json`](evidence/performance-reliability.json) |

Note: with `backend/data/ml/confidence_calibration.json` loaded, quality modifiers on these frozen windows fall below the anomaly suppression threshold and Scenario B is incorrectly marked `suppressed_data_quality`, so precision/recall collapse. The measured run therefore used the fixed quality formula, matching the Docker runtime image (which does not ship that artifact). Re-measure after recalibrating if you want learned-mode numbers.

Re-run from `backend` (local Postgres on port `5433`):

```powershell
python -m app.scripts.validation_cli run
# equivalent: make validate
```

## Measured metrics (held-out harness)

All ratios are shown as percentages for readability but remain stored as ratios. Sample sizes are the denominators used by the harness, not moderate-dataset population counts.

| Metric (code) | Category | Result | Sample | Method | Interpretation and limitation |
|---|---|---:|---:|---|---|
| Anomaly precision (`anomaly_precision`) | Analytics | 100% | 1 predicted-positive cell | `TP / (TP + FP) = 1 / (1 + 0)` | One held-out (scenario × provider) cell was alertable (`requires_review` on Scenario B / bKash). Tiny sample — not a market-rate precision claim. |
| Anomaly recall (`anomaly_recall`) | Analytics | 100% | 1 labeled-positive cell | `TP / (TP + FN) = 1 / (1 + 0)` | The single labeled alertable anomaly cell was detected. Does not establish recall for velocity, balance-inconsistency, or behavioral-embedding detectors. |
| False-positive rate (`anomaly_false_positive_rate`) | Analytics | 0% | 8 labeled-negative cells | `FP / (FP + TN) = 0 / (0 + 8)` | Includes Scenario C’s suppressed data-quality case, which must not alert. Synthetic held-out cells only. |
| Shortage detection lead time (`shortage_lead_time_minutes`) | Analytics | 534.34 minutes | 1 Scenario A shared-cash projection | `projected_shortage_at − as_of_at` | Lead time on the frozen depletion slope, not real demand forecast accuracy. |
| Data-quality incident rate (`data_quality_incident_rate`) | Reliability | 11.11% | 9 provider assessments | `1` stale/missing/conflicting `/ 9` | Scenario C fault injection on synthetic feeds. |
| Alert explanation coverage (`alert_explanation_coverage`) | Reliability | 100% | 2 published alerts | Complete EN sections (situation, evidence, uncertainty, next_step) `/ 2` | Checks non-empty structured text, not linguistic quality. |
| API average latency (`api_avg_ms`) | Performance | 318.67 ms | 90 timed calls | In-process handler timing: 30 iterations × 3 read endpoints | Excludes network/TLS/serialization transport. Not a load test. |
| API p95 latency (`api_p95_ms`) | Performance | 1040.88 ms | 90 timed calls | Same method as average; 95th percentile of the 90 samples | Same in-process limitation; values vary run to run. |

Endpoints timed: `outlet_dashboard`, `liquidity_projections`, `anomaly_flags`.

## Confusion matrix (held-out anomaly cells)

From the persisted metric `details` on run `1b911d32-06ea-4104-b3cb-b949d53b174e` (9 scenario × provider cells):

| | Predicted requires review | Predicted not reviewable |
|---|---:|---:|
| Labeled unusual / alertable | TP = 1 | FN = 0 |
| Labeled normal / non-alertable | FP = 0 | TN = 8 |

Derived values: precision `1.0`, recall `1.0`, false-positive rate `0.0`.

## Fixture consistency checks (not measured metrics)

The moderate synthetic dataset (`moderate_demo_v1`) still embeds authored metric rows such as precision/recall/FPR `0.8` / `0.8` / `0.1`, plus perfect coverage ratios for audit completeness, provider-denial success, and similar checklist fields. Those values are produced by `generate_moderate_dataset` / `validate_moderate_dataset` from deterministic fixture formulas. They verify that the authored demo population is internally consistent.

They are **not** independent measurements of the live analytics engines on frozen held-out runs, and they must not be cited as measured validation metrics.

| Check | Source | Authored value | What it actually is |
|---|---|---|---|
| Moderate anomaly precision / recall / FPR | `data/generated/moderate_demo/metric_results.csv` | 80% / 80% / 10% | Fixture formula `TP=8/(8+2)` etc. over an authored near-identical-amount population |
| Moderate data-quality handling rate | same CSV | 100% | Authored degraded windows marked safely suppressed |
| Moderate alert explanation coverage | same CSV | 100% | Authored alert rows with explanation fields present |
| Moderate audit completeness | same CSV | 100% | Authored cases with assignment/history/notification/audit rows |
| Moderate provider-denial success | same CSV | 100% | Authored authorization matrix expectations |
| Moderate shortage lead time | same CSV | 180 minutes | Authored median over six labeled shortage rows |

Reproduce the fixture checks with:

```powershell
python -m app.scripts.validate_moderate_dataset
```

## Failure-mode evidence (harness + scenarios)

On the frozen held-out set the harness confirms:

- Scenario B near-identical cluster surfaces as `requires_review` (alertable);
- Scenario C degraded/conflicting feed keeps the same pattern non-alertable (`suppressed_data_quality` path contributes to the TN/FPR denominator);
- Scenario A shared-cash projection yields a finite shortage lead time;
- Published high-impact alerts carry complete English explanation sections;
- Representative read handlers were timed in-process for average and p95 latency.

## Test and verification commands

From `backend`:

```powershell
python -m app.scripts.validation_cli run
python -m app.scripts.validate_moderate_dataset
python -m pytest tests\phase7 -q
python -m app.scripts.safety_scan
```

## Raw evidence

- [Held-out validation summary](evidence/validation-summary.json) — full metric rows, methods, limitations, confusion-matrix details
- [Performance / reliability extract](evidence/performance-reliability.json) — latency + reliability subset
- [Moderate dataset manifest](../data/generated/moderate_demo/manifest.json) — fixture population only
- [Moderate dataset validation report](../data/generated/moderate_demo/validation-report.json) — fixture consistency checks
- [Moderate metric CSV](../data/generated/moderate_demo/metric_results.csv) — authored rows, not harness output

## Interpretation and limitations

These numbers demonstrate measured behavior of the current engines on a **small, frozen, synthetic** held-out split. Precision and recall each rest on a single labeled-positive cell; shortage lead time rests on one Scenario A projection. Perfect explanation coverage describes two published alerts. Latency excludes transport and is not a networked load test. None of this is evidence of production accuracy, provider-network performance, regulatory suitability, demographic fairness, or real-world fraud detection.

The older moderate-dataset 80/80/10 table is retained only as a fixture consistency check above so judges can see why those numbers exist without mistaking them for harness measurements.
