# Validation evidence

## Scope and release identity

The current judge-facing metrics come from the deterministic moderate synthetic dataset, not the older Phase-7 harness artifacts that previously existed under `docs/evidence/`. Those older artifacts used different seeds, a smaller population, and an earlier implementation revision and are not reported here.

| Field | Value |
|---|---|
| Implementation revision audited | `f6a53ddcbd699ce21d19b67b0039ba85b7ce0b1e` |
| Dataset | `moderate_demo_v1` |
| Generator / validation version | `1.0.0` / `1.0.0` |
| Master seed | `2026071201` |
| Reported split | `held_out` |
| Held-out validation run | `0914e3ae-f814-5dfa-bcef-dddf836e89f6` |
| Engine version stored with metrics | `validation-1.0.0` |
| Manifest SHA-256 recorded by validator | `8aa0153fbbb88ac0f7b55c01ffbca3d506329dd269153d3e52a331d95284b62a` |
| Dataset validation result | 64 passed, 0 failed |

The same eight metric definitions also exist on the `demo` split. Values below are reported only from the held-out run to avoid presenting duplicated metric rows as additional evidence.

## Measured metrics

All ratios are shown as percentages for readability but remain stored as ratios.

| Metric (code) | Category | Result | Sample | Method | Interpretation and limitation |
|---|---|---:|---:|---|---|
| Anomaly precision (`anomaly_precision`) | Analytics | 80% | 10 predicted-positive cases | `TP / (TP + FP) = 8 / (8 + 2)` | Two review flags were benign lookalikes. Synthetic near-identical-amount population only. |
| Anomaly recall (`anomaly_recall`) | Analytics | 80% | 10 labeled-positive cases | `TP / (TP + FN) = 8 / (8 + 2)` | Two injected positives were not surfaced as reviewable. Does not establish recall for all four runtime detectors. |
| False-positive rate (`anomaly_false_positive_rate`) | Analytics | 10% | 20 labeled-negative cases | `FP / (FP + TN) = 2 / (2 + 18)` | Demonstrates deliberate benign-lookalike testing; population is authored synthetic data. |
| Shortage detection lead time (`shortage_detection_lead_time`) | Analytics | 180 minutes | 6 actionable shortage labels | Median time between actionable detection and labeled shortage | Shows early warning in the generated scenarios, not real forecast accuracy. |
| Data-quality handling rate (`data_quality_handling_rate`) | Reliability | 100% | 10 degraded windows | `10` safely suppressed/non-actionable windows `/ 10` | Validates the authored failure cases; it is not an availability measure. |
| Alert explanation coverage (`alert_explanation_coverage`) | Explainability | 100% | 24 alerts | Alerts with complete English explanation `/ 24` | Checks presence of structured explanation fields, not linguistic quality or user comprehension. |
| Audit completeness (`audit_completeness`) | Reliability | 100% | 15 cases | Cases with assignment, status history, notification, and audit evidence `/ 15` | Deterministic case fixtures; no claim about production durability. |
| Provider-denial success (`provider_denial_success_rate`) | Security/reliability | 100% | 6 expected denials | Expected cross-provider denials observed `/ 6` | Small deterministic authorization matrix; not a penetration test. |

Every stored metric carries the limitation: “Synthetic deterministic population; not representative of provider market behavior.”

## Confusion matrix

The held-out near-identical-amount evaluation uses:

| | Predicted requires review | Predicted not reviewable |
|---|---:|---:|
| Labeled unusual | TP = 8 | FN = 2 |
| Labeled normal/benign | FP = 2 | TN = 18 |

Derived values are precision `0.8`, recall `0.8`, and false-positive rate `0.1`. The false positives are intentional: the platform is expected to surface unusual activity for human review, not assert wrongdoing.

## Failure-mode evidence

The dataset validator checks:

- delay, missing feed, missing field, malformed payload, and conflicting-balance coverage;
- preservation of conflicting snapshots;
- suppression reasons and reduced confidence under degraded quality;
- rejection of malformed input without ledger creation;
- separate shared-cash and provider-e-money histories;
- typed alert source links and plausible benign explanations;
- legal case transitions, current owner/state agreement, and required resolution summaries;
- opaque synthetic references and prohibited-language absence; and
- deterministic file hashes and metric recomputation.

The current database contains 40 quality assessments, 18 issues, 24 unusual-activity flags, 24 alerts, 15 cases, 57 audit events, 60 labels, and 16 metric rows across demo and held-out runs.

## Performance evidence

No API average or p95 latency number is reported for the current moderate dataset and implementation revision. The removed earlier performance artifact measured an older build with a different validation population and excluded network transport. The repository still contains performance test code, but a current, controlled benchmark was not executed during this documentation audit. This remains a submission gap rather than a value to infer or reuse.

## Test and verification commands

From `backend`:

```powershell
python -m app.scripts.validate_moderate_dataset
python -m pytest tests\unit tests\contracts -q
python -m app.scripts.safety_scan
python -m app.scripts.audit_database
```

During this audit:

- moderate dataset validation: `64 passed, 0 failed`;
- backend unit and contract tests: `64 passed`;
- configured database health: connected and schema-ready through migration `010`;
- migration status: repository migration `011` pending on the configured Supabase target.

The repository contains 276 backend test functions, including schema/RLS, ingestion, analytics, coordination, scenario, validation, and responsible-design suites. This count describes source coverage; it is not a claim that all 276 were re-executed during the documentation audit.

## Raw evidence

- [Dataset manifest](../data/generated/moderate_demo/manifest.json)
- [Dataset validation report](../data/generated/moderate_demo/validation-report.json)
- [Metric rows](../data/generated/moderate_demo/metric_results.csv)
- [Ground-truth labels](../data/generated/moderate_demo/ground_truth_labels.csv)
- [Loader apply report](../data/generated/moderate_demo/apply-report.json)
- [Current database audit](data/database-audit.json)
- [Current safety scan](evidence/safety-security-scan.json)
- [Schema/RLS verification directory](verification/README.md)

## Interpretation and limitations

The evidence is sufficient to demonstrate measured behavior for the hackathon prototype, including more than the required three metrics. It is not evidence of production accuracy, provider-network performance, regulatory suitability, demographic fairness, or real-world fraud detection. The evaluation population is deterministic, authored, small, and dominated by one unusual-activity pattern. Perfect coverage ratios describe fixture completeness, not general system reliability.
