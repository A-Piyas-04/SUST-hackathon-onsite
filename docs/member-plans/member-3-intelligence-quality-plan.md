# Member 3 Detailed Task Plan — Intelligence & Quality

## 1. Mission

You own the analytical meaning and evidence quality of the prototype. Your work must make the following chain deterministic, explainable, testable, and safe:

```text
Synthetic scenario/input
        ↓
Data Quality & Confidence Engine
        ↓
Liquidity Forecast and Anomaly Engines
        ↓ ResultEnvelope
Member 1 validates, persists and exposes the result
        ↓ AlertCandidate
Member 2 creates the immutable alert and manages the case
```

Your job ends at versioned engine outputs, expected results, automated tests, evaluation metrics, and analytical documentation. You do **not** own HTTP endpoints, database migrations/repositories, alert/case persistence, RBAC implementation, or frontend work.

## 2. Non-negotiable outcomes

By Hour 16, your owned work must prove all of the following:

1. The same seed and configuration produce the same synthetic dataset and expected outputs.
2. Shared physical cash and each provider's e-money are analyzed separately.
3. Every projection has confidence, sample count, contributing signals, and a safe non-actionable state when a forecast is invalid.
4. At least one anomaly rule produces structured evidence and a plausible benign explanation.
5. Missing, stale, conflicting, or insufficient data lowers confidence safely.
6. A degraded provider cannot produce a new high-confidence anomaly alert candidate.
7. Scenario A, B, C, and D fixtures are reproducible.
8. Held-out evaluation reports numeric results, sample size, method, and limitations.
9. No output declares fraud, profiles a real person, or recommends blocking/freezing/transferring funds.
10. Member 1 can consume your output without copying your formulas; Member 2 can understand the evidence without recalculating it.

## 3. Ownership boundaries

### You own

- Deterministic synthetic data and scenario configuration.
- Ground-truth labels and tuning/held-out/demo dataset separation.
- Fault-injection behavior and expected data-quality outcomes.
- Data Quality & Confidence Engine.
- Shared-cash and provider e-money liquidity forecasting logic.
- Near-identical-amount anomaly rule and evidence construction.
- Confidence degradation and anomaly-suppression rules.
- Pure-function input/output contracts and fixtures.
- Unit, boundary, adversarial, regression, and analytical-evaluation tests.
- Forecast/anomaly/reliability metric calculations.
- Data-generation, analytical-method, false-positive, and limitation documentation.
- Scenario B and analytical-evidence presentation.

### You do not own

- REST route handlers or OpenAPI ownership — Member 1 or Member 2.
- Supabase migrations, persistence, database views, or repositories.
- `AlertCandidate` production — Member 1.
- Alert deduplication, explanation rendering, routing, cases, notes, audit, notifications, or RBAC — Member 2.
- Dashboard or case-console implementation.
- Fixing another member's code. File a reproducible defect with the failing fixture and expected output.

## 4. Files/artifacts you should own

Use the actual language/framework selected in Phase 1, but preserve these logical boundaries:

```text
intelligence/
  contracts/              # ResultEnvelope and engine input types/schemas
  scenarios/              # A–D and normal scenario definitions
  generator/              # deterministic synthetic generator
  data_quality/            # classification and confidence modifier
  liquidity/               # burn-rate projection and confidence band
  anomaly/                 # near-identical-amount rule and evidence
  evaluation/              # held-out evaluation and metric calculations

tests/intelligence/
  contracts/
  generator/
  data_quality/
  liquidity/
  anomaly/
  integration/
  evaluation/

fixtures/intelligence/
  tuning/
  held-out/
  demo/

docs/member-plans/         # this plan
```

Do not edit Member 1 route/persistence files or Member 2 workflow/security files.

## 5. Contracts to freeze in Phase 1

### 5.1 Engine input contract

Your pure engines should receive normalized values, not database clients or HTTP request objects.

Required input concepts:

- `simulation_run_id`, seed, scenario code, and configuration version.
- Outlet ID and provider/account ID where relevant.
- Normalized transactions with synthetic references, type, status, amount, and timestamps.
- Cash and provider-balance snapshots with observation/receipt timestamps.
- Analysis input-window start/end and `as_of_at`.
- Configured thresholds, minimum sample count, and rule/engine version.
- Current or computed data-quality evidence.

### 5.2 `ResultEnvelope` contract

Every quality, liquidity, and anomaly result handed to Member 1 must contain:

| Field | Requirement |
|---|---|
| `result_type` | `data_quality`, `liquidity_projection`, or `anomaly_flag` |
| `engine_version` | Stable semantic version or commit-compatible identifier |
| `simulation_run_id` | Required |
| `outlet_id` | Required |
| `provider_id` | Required for provider results; null only for shared cash |
| `outlet_provider_account_id` | Required for provider e-money/anomaly results |
| `input_window_start`, `input_window_end`, `as_of_at` | Required |
| `configuration` or `configuration_hash` | Required for reproducibility |
| `quality_assessment_ids` or quality payload refs | Required where applicable |
| `confidence_score` | Range 0–1 |
| `confidence_level` | `high`, `medium`, `low`, or `unavailable` |
| `evidence` / `signals` | Structured, ordered, synthetic-only evidence |
| `created_at` | Required |

Result-specific requirements:

- Quality: `status`, `confidence_modifier`, issue list, sample count, latest source time, summary.
- Liquidity: reserve type, current balance, burn rate, shortage time, lower/upper bounds, sample count, actionable flag, non-actionable reason.
- Anomaly: rule/version, window, disposition, reason code, evidence summary/items, linked synthetic transaction refs, plausible benign explanation, suppression reason.

### 5.3 Compatibility rules

- Member 1 owns the persistence/API schema. You own field meaning and expected values.
- Never silently rename/remove a frozen field. Propose a contract revision to Member 1.
- Additive optional fields are allowed only after fixture and consumer approval.
- Time is UTC ISO 8601; money uses exact decimal representations, not binary floating point.
- Provider results must never contain data from a different provider.

## 6. Analytical rules to freeze

Values below are configuration decisions, not hard-coded constants. Freeze exact values with the team in Phase 1.

### 6.1 Data quality

Classification precedence:

1. `conflicting` — incompatible snapshots or impossible transitions.
2. `missing` — expected feed/batch/required source data absent.
3. `stale` — latest source timestamp exceeds freshness threshold.
4. `fresh` — required data is present, consistent, and within threshold.

The assessment must expose individual issues such as late arrival, missing feed/field, conflicting snapshot, impossible transition, insufficient samples, and malformed payload.

Confidence behavior:

- Start with a configurable feed-status modifier.
- Reduce for low sample count and unstable rate.
- Never increase confidence because data is missing or conflicting.
- `missing` normally makes analytical output unavailable.
- `conflicting` must not silently select a balance as truth.
- Preserve issue evidence and the last trusted value/time for safe display.

### 6.2 Liquidity forecast

- Forecast shared cash independently from each provider e-money reserve.
- Use a transparent recent-window depletion/burn rate; avoid opaque/deep models.
- If depletion rate is zero or negative, return no shortage time.
- If samples are below the configured minimum, return a non-actionable result.
- Apply data-quality modifier to confidence.
- Widen confidence bounds as confidence falls.
- Include contributing signals such as recent cash-out velocity, rate stability, sample adequacy, and feed freshness.

### 6.3 Near-identical-amount anomaly

Evaluate within one outlet, one provider, and one time window. Freeze:

- Eligible transaction types/statuses.
- Time-window length.
- Amount tolerance.
- Minimum matching transaction count.
- Minimum/maximum number of synthetic parties if used.
- Optional velocity threshold.
- Confidence calculation.

Output must include exact matching synthetic transaction references, count, approximate amount cluster, party count, time window, confidence, reason code, and a plausible benign explanation such as event-driven demand.

### 6.4 Suppression

- Retain the computed anomaly evaluation for audit/metrics.
- Set disposition to `suppressed_data_quality` when configured degraded conditions apply.
- Supply a suppression reason and data-quality reference.
- Do not emit an actionable/high-confidence anomaly result that Member 1 could convert to an anomaly `AlertCandidate`.
- A separate data-quality advisory may still be expected.

## 7. Scenario and dataset plan

| Dataset | Purpose | May tune thresholds? | Reported as validation? |
|---|---|---:|---:|
| `tuning` | Develop thresholds and inspect edge cases | Yes | No |
| `held_out` | Final analytical evaluation | No | Yes |
| `demo` | Deterministic Scenarios A–D | No after Hour 10 | Demo evidence only |

| Scenario | Your required fixture behavior | Expected owned result |
|---|---|---|
| Normal | Stable feeds and ordinary demand, including a legitimate high-demand example | Fresh quality; no invalid shortage; no/low anomaly flags |
| A — Hidden shortage | One provider or shared cash depletes despite apparently healthy separate reserves | Correct reserve, estimated shortage time, confidence and signals |
| B — Liquidity + unusual activity | Falling cash plus repeated near-identical transactions from a small synthetic cluster | Projection plus evidence-backed `requires_review` anomaly with benign context |
| C — Delayed/conflicting data | A provider feed is delayed, missing, malformed, or produces conflicting snapshots | Degraded quality, lower/unavailable forecast confidence, suppressed anomaly, data advisory expectation |
| D — Coordinated closure | An important, provider-scoped analytical result suitable for routing | Stable result/candidate fixture; Member 2 owns assignment through resolution |

Every generated record must be synthetic and traceable to scenario, seed, provider, outlet, and run.

## 8. Checkpoint-by-checkpoint plan

### Master checkpoint ledger

This is the quick status sheet to use during the hackathon. Detailed instructions follow it.

| Clock | Your cumulative deliverables by this checkpoint | Required from Members 1/2 at this checkpoint | What you must unlock for the next checkpoint |
|---|---|---|---|
| 00:45 | Acceptance matrix, config keys, dataset split/seed policy, safety assertions | M1 normalized field map; M2 explanation-variable needs | Field meanings and result variants for envelope v1 |
| 01:15 | Previous items + `ResultEnvelope` v1, three valid fixtures, invalid cases, contract tests | M1 persistence-field mapping approval | Stable result fixtures for candidate mapping |
| 01:30 | Previous items + result-to-candidate map and suppression truth table | M1 `AlertCandidate` draft; M2 dedup/render variables | Approved alertability and explanation variables |
| 02:00 | Previous items + A–D/normal configs, expected snapshots, boundary fixtures, label format | M1/M2 contract exception decisions | Final executable Phase 1 package |
| 02:15 | `P1-M3` complete and independently passing | M1 confirms fixture validation; M2 confirms candidate consumption | Generator/quality implementation inputs |
| 04:00 | Deterministic generator, fault transformations, quality classifications and unit tests | M1 ingestion round-trip result; M2 scope matrix for later | Corrected generator/quality contracts |
| 05:00 | `P2-M3`, labeled tuning inputs and assumptions/limitations | M1 engine adapter + quality-ref format | Callable quality engine and forecast/anomaly inputs |
| 06:30 | Callable liquidity/anomaly engines, unit/boundary tests, A/B results | M1 pure-function adapter and serialization round-trip | Engine package/version/config handoff |
| 07:30 | `P3-M3`, persisted-result comparison, Scenario A/B trace, initial tuning metrics | M1 Scenario C fixtures/gating; M2 denial/transition matrix | Degraded fixtures and adversarial expectations |
| 09:15 | Hardened degradation/suppression behavior, Scenario C fixtures, adversarial and language matrix | M1/M2 secured builds, IDs/tokens and documented behavior | Same test matrix runnable against both API groups |
| 10:00 | `P4-M3`, Scenario C proof, leakage results and owned defect list | M1 reset/base URL/release timing; M2 demo users and D flow | A–D E2E assertions and blocker routing |
| 11:00 | Executable A–D regression, reset verification and pre-RC blocker list | M1 release candidate; M2 secured workflow endpoints | Full release-candidate gate |
| 12:00 | `P5-M3`, frozen demo outputs, RC identifier and final regression report | M1 metric interface/storage; M2 coverage/security results | Frozen held-out labels/config and metric scripts |
| 13:00 | Raw held-out results, metric payloads, secret/safety scan | M1 metric round-trip response | Signed-off evidence and limitations |
| 13:30 | `P6-M3`, final metrics/method/sample sizes/limits and human-review statement | M1 deployed metric values; M2 responsibility outline | Data/analytics documentation source material |
| 14:00 | Documentation draft and handoff excerpts for M1/M2 | M1 doc paths; M2 wording constraints | Final consistent Member 3 docs |
| 14:30 | `P7-M3`, final documentation, Scenario B narration and metric slide content | M1 slide/reset format; M2 speaker transition | Rehearsal-ready analytical segment |
| 14:45 | First rehearsed segment and issue list | M1/M2 complete demo sequence | Timing/wording corrections only |
| 15:10 | Corrected second rehearsal inputs | M1/M2 final transitions | Freeze spoken wording and backup evidence |
| 15:30 | Rehearsed Scenario B/metrics segment, verified displayed values and backups | M1 release ID/reset output; M2 final RBAC result | Critical final analytical checks |
| 15:45 | Passing critical-test summary, metrics/expected-output verification and clean scan | M1 frozen final build | Final observation/sign-off; no refactor |
| 16:00 | Final analytical/data sign-off and all Member 3 artifacts present | Submission confirmation from Member 1 | Work complete |

## Phase 1 — API/Schema Contract and Executable Scaffolding

**Time:** 00:00–02:15  
**Phase output:** `P1-M3` executable engine contract package.

### 00:00–00:45 — Acceptance and configuration freeze

Tasks:

1. Review `schema.md` §§4, 7, 9, 11, 13, 17 and the final phase distribution.
2. Convert Scenarios A–D into explicit input conditions and expected outcomes.
3. Define engine/rule versions and configuration keys.
4. Freeze tuning, held-out, and demo split policy.
5. Define minimum safety assertions and prohibited language.

Deliverables at 00:45:

- Scenario acceptance matrix.
- Draft configuration manifest.
- Dataset split policy and seed list.
- Safety assertion list.
- List of unresolved contract questions for Member 1.

Prerequisites needed from others for 00:45:

- Member 1: normalized transaction/balance field map and supported decimal/time representation.
- Member 2: no dependency yet; only confirm which evidence/explanation variables alerts require.

Prerequisites you must provide for the next checkpoint:

- Result types, expected quality statuses, confidence semantics, and evidence field meanings.

### 00:45–01:15 — `ResultEnvelope` v1

Tasks:

1. Define shared envelope and quality/liquidity/anomaly payload variants.
2. Create one valid example for each result type.
3. Create invalid contract cases: cross-provider IDs, missing confidence, binary float money, missing benign explanation, and missing suppression reason.
4. Write executable schema/contract tests.

Deliverables at 01:15:

- `ResultEnvelope` v1 schema/types.
- Three valid result fixtures.
- Contract-validation test suite.
- Engine-version/configuration-hash convention.

Prerequisites needed from others:

- Member 1: confirmation that every envelope field maps to persistence or an intentional transient field.

Prerequisites you provide for 01:30:

- Stable result fixtures Member 1 can use to define `AlertCandidate` and persistence adapters.

### 01:15–01:30 — Candidate compatibility review

Tasks:

1. Review Member 1's mapping from results to `AlertCandidate`.
2. Confirm that candidate generation uses persisted result IDs rather than copied/recalculated evidence.
3. Identify which results are alertable, advisory-only, or suppressed.

Deliverables at 01:30:

- Result-to-candidate mapping table.
- Alertability/suppression truth table.
- Approved explanation variables required from analytical output.

Prerequisites needed from others:

- Member 1: `AlertCandidate` draft.
- Member 2: required structured variables for alert rendering and deduplication.

### 01:30–02:00 — Executable scenarios and expected results

Tasks:

1. Create compact deterministic inputs for normal and Scenarios A–D.
2. Add expected output snapshots for quality, forecast, and anomaly behavior.
3. Add boundary fixtures: exact freshness threshold, minimum samples, zero rate, tolerance boundary, and minimum anomaly count.
4. Confirm provider isolation in every fixture.

Deliverables at 02:00:

- Scenario configuration files and deterministic seed list.
- Expected result snapshots.
- Boundary-test fixtures.
- Held-out label format.

### 02:00–02:15 — Phase gate

Deliverables completed so far:

- Acceptance matrix, configs, dataset splits, envelope v1, result fixtures, candidate mapping, executable contract/boundary tests.

Verify before exit:

- Contract tests pass independently of database/API code.
- Member 1 can validate all result fixtures.
- Member 2 can render/deduplicate a candidate fixture without asking for formula details.
- No contract contains case owner/status fields or unsafe financial actions.

Prerequisites you need for Phase 2:

- From Member 1: final normalized ingestion input contract and directory/module integration point.
- From Member 2: frozen explanation-variable list only; Phase 2 engine work should not depend on case implementation.

Prerequisites you provide for Phase 2:

- `P1-M3`, generator configs, quality expected outputs, and labeled forecast/anomaly inputs.

Fallback if late:

- Keep one outlet, three providers, four scenario configs, one quality rule set, one forecast method, and one anomaly rule. Cut extra pattern categories first.

## Phase 2 — Foundation APIs

**Time:** 02:15–05:00  
**Phase output:** `P2-M3` deterministic generator + Data Quality package.

### 02:15–04:00 — Generator and quality engine

Tasks:

1. Implement deterministic provider transactions and cash/provider-balance snapshots.
2. Attach simulation run, provider, outlet, synthetic party, observation, and receipt metadata.
3. Implement fault transformations for delay, missing feed, missing field, conflicting balance, and malformed payload.
4. Implement quality classification, issue evidence, sample count, last-source time, confidence modifier, and summary.
5. Ensure conflicting snapshots remain present and identifiable.
6. Add unit/property-style invariants for determinism and provider separation.

Deliverables at Hour 4:

- Generator produces identical output for identical seed/config.
- Normal and A–D input fixtures can be generated.
- Quality engine produces fresh/stale/missing/conflicting outcomes.
- Member 1 receives quality `ResultEnvelope` fixtures and generator payloads.

Prerequisites needed from Member 1 by Hour 4:

- Confirm generated payloads pass ingestion validation.
- Confirm persisted/retrieved quality results preserve all evidence fields.
- Return contract errors as fixtures, not ad-hoc field requests.

Prerequisites needed from Member 2:

- None for implementation. Request only a cross-provider denial test token/scope matrix for later adversarial testing.

### 04:00–05:00 — Foundation hardening and next-engine inputs

Tasks:

1. Fix only generator/quality contract defects.
2. Generate labeled tuning inputs for forecast/anomaly development.
3. Add tests for malformed input, timestamp threshold, conflicting values, missing fields, impossible transitions, and insufficient samples.
4. Record known generator assumptions and limitations.

Deliverables at Hour 5:

- `P2-M3` generator + quality package.
- Passing generator/quality tests.
- Tuning fixtures for Phase 3.
- Quality payloads persisted and displayed through Member 1 endpoints.
- Assumption/limitation notes started.

Prerequisites you need for Phase 3:

- From Member 1: stable engine input adapter and confirmation of quality-assessment reference format.
- From Member 2: no runtime dependency; candidate fixture remains sufficient.

Prerequisites you provide for Phase 3:

- Callable quality engine, labeled forecast/anomaly inputs, quality IDs/payload refs, tuning config, and expected boundary results.

Exit criteria:

- Same seed/config is byte-equivalent or semantically identical.
- No real identity-like values exist.
- Provider B transactions cannot appear in Provider A engine input.
- A missing/conflicting feed cannot be classified fresh.

## Phase 3 — Intelligence-to-Alert Chain

**Time:** 05:00–07:30  
**Phase output:** `P3-M3` tested liquidity and anomaly engines.

### 05:00–06:30 — Core engines

Liquidity tasks:

1. Implement transparent recent-window depletion rate.
2. Produce separate shared-cash and provider e-money projections.
3. Handle zero/negative depletion and insufficient samples safely.
4. Apply quality modifier and compute confidence level/bounds.
5. Emit ordered contributing signals.

Anomaly tasks:

1. Implement near-identical-amount matching within one provider/outlet/window.
2. Produce evidence items and linked transaction references.
3. Calculate confidence and disposition.
4. Require plausible benign explanation for actionable flags.
5. Add threshold/boundary and normal-demand tests.

Deliverables at 06:30 handoff:

- Callable forecast and anomaly engines.
- Passing unit/boundary tests.
- `ResultEnvelope` outputs for normal, A, and B.
- Initial analytical evaluation on tuning data only.

Prerequisites needed from Member 1:

- Engine-call adapter invokes pure functions without database objects.
- Persisted result round-trip retains decimal precision, timestamps, evidence order, and quality links.

Prerequisites you provide Member 1:

- Package entry points, versions, config, fixtures, expected results, and failure behavior.

### 06:30–07:30 — Integration verification

Tasks:

1. Compare Member 1 persisted/read results with your expected snapshots.
2. Verify Member 1 candidate mapping does not change confidence/evidence.
3. Verify Member 2 alert fixture renders evidence/uncertainty/benign context without formula duplication.
4. Add regression tests for any integration serialization defect.

Deliverables at Hour 7:30:

- `P3-M3` signed-off engines.
- Evidence-complete Scenario B result.
- Correct Scenario A shortage result.
- Result → persisted result → candidate → alert trace with stable IDs.
- Tuning-only metric snapshot and known-error list.

Prerequisites you need for Phase 4:

- From Member 1: persisted Scenario C quality/result fixtures and candidate-gating behavior.
- From Member 2: provider-scope denial matrix and legal case-transition matrix for test expectations.

Prerequisites you provide for Phase 4:

- Degraded-input fixtures, hardened engine baseline, and expected suppression/advisory truth table.

Exit criteria:

- Zero/replenishing balances do not produce false shortage times.
- Provider balances are never mixed.
- Actionable anomaly results always include evidence and benign context.
- No engine output contains `fraud`, `block`, `freeze`, or financial-action advice.

## Phase 4 — Safe Coordinated Response

**Time:** 07:30–10:00  
**Phase output:** `P4-M3` hardened degraded-data behavior + adversarial suite.

### 07:30–09:15 — Degradation and adversarial behavior

Tasks:

1. Harden missing/stale/conflicting/insufficient-sample behavior.
2. Verify forecast confidence falls or becomes unavailable as configured.
3. Verify confidence bounds widen under degraded but usable data.
4. Retain anomaly evaluations while marking them suppressed.
5. Emit data-quality advisory expectations instead of risk-alert expectations.
6. Build provider-leakage, cross-outlet, malformed-ID, stale-token, invalid-transition, duplicate-request, and concurrent-case test expectations for both API owners.
7. Add a safe-language scan over result/evidence fixtures.

Deliverables at 09:15:

- Hardened degraded-result fixtures.
- Scenario C expected sequence.
- Adversarial API expectation matrix for Members 1 and 2.
- Safe-language test.

Prerequisites needed from Member 1 at 09:15:

- Secured degraded data/analytics endpoints.
- Last-trusted-balance/conflicting-candidate representation.
- Confirmation suppressed results cannot create anomaly candidates.

Prerequisites needed from Member 2 at 09:15:

- Secured auth/alert/case endpoints.
- Demo role tokens/scopes.
- Legal transition and cross-provider denial behavior.

### 09:15–10:00 — Run the same matrix against both endpoint groups

Rules:

- Do not fix Member 1 or Member 2 code.
- Report each defect with request/input, seed, expected result, actual result, severity, and owning member.
- Re-run only after the owner provides a new build/commit.

Deliverables at Hour 10:

- `P4-M3` degraded-data package and adversarial report.
- Passing Scenario C engine expectations.
- Confirmed anomaly suppression and data-advisory behavior.
- Cross-provider leakage test results.
- Prioritized reproducible defect list.

Prerequisites you need for Phase 5:

- From Member 1: release-candidate time, reset command, base URL, seeded IDs, and scenario-run instructions.
- From Member 2: demo-login users/tokens and complete Scenario D API sequence.

Prerequisites you provide for Phase 5:

- A–D expected outputs, end-to-end assertions, safe-language rules, provider-isolation matrix, and open defect list.

## Phase 5 — Integration and MVP Freeze

**Time:** 10:00–12:00  
**Phase output:** `P5-M3` MVP regression report.

### 10:00–11:00 — Prepare and smoke-test regression

1. Convert A–D expectations into one repeatable end-to-end suite.
2. Include database/API-visible assertions without coupling to internal repositories.
3. Cover reset determinism, no blended total, forecast/evidence fields, alert immutability, case lifecycle, provider denial, idempotency/concurrency, and safe language.
4. Run smoke checks against the latest builds while Member 1 prepares the release candidate.

Deliverables at 11:00:

- Executable A–D regression suite.
- Known-state seed/reset verification.
- Blocker list split by Member 1, Member 2, and Member 3 ownership.

### 11:00–12:00 — Release-candidate gate

Run in this order:

1. Reset and seed.
2. Normal baseline.
3. Scenario A forecast.
4. Scenario B anomaly + combined evidence.
5. Scenario C degraded quality + suppression.
6. Scenario D login → alert → case → assign → acknowledge → escalate → note → resolve → audit.
7. Cross-provider access denial.
8. Repeat selected POSTs to verify idempotency and stale case version conflict.

Deliverables at Hour 12:

- `P5-M3` regression report with pass/fail per invariant.
- Exact release-candidate identifier tested.
- Final blocker list and retest evidence.
- Frozen demo expected-output sheet.

Prerequisites you need for Phase 6:

- From Member 1: frozen metric payload interface, validation persistence/endpoint readiness, and release candidate.
- From Member 2: workflow/explanation coverage results and final security test evidence.

Prerequisites you provide for Phase 6:

- Frozen held-out configuration, ground-truth labels, metric-calculation scripts, regression report, and tested engine versions.

Hard rule:

- Do not tune thresholds using held-out failures after Hour 12. If a true implementation bug is fixed, document and rerun the full held-out evaluation consistently.

## Phase 6 — Validation and Observability

**Time:** 12:00–13:30  
**Phase output:** `P6-M3` signed-off analytics/security evidence.

### 12:00–13:00 — Held-out evaluation

Calculate at minimum:

- Anomaly precision = `TP / (TP + FP)`.
- Anomaly recall = `TP / (TP + FN)`.
- False-positive rate = `FP / (FP + TN)`.
- Forecast error, preferably MAE in minutes on shortage cases, or shortage detection lead time.
- Data-quality handling rate = correctly degraded/suppressed failure cases divided by defined failure cases.

For every metric include:

- `metric_code`, numeric value, unit, sample size.
- Dataset split, seed set, engine/rule version, configuration hash.
- Method and confusion-matrix/raw summary where relevant.
- Honest limitations and synthetic-data caveat.

Tasks:

1. Run once on the frozen held-out set.
2. Save raw result summaries and metric payloads.
3. Verify Member 1 persists/serves values unchanged.
4. Run repository/data scans for real identities, credentials, prohibited actions, and unsafe language.

Deliverables at 13:00:

- Raw held-out results.
- Metric payloads with methods/sample sizes/limitations.
- Security/safety scan report.

### 13:00–13:30 — Evidence sign-off

1. Reconcile displayed `/metrics` values against your payloads.
2. Provide Member 2 analytical caveats for responsible-design documentation.
3. Capture a concise metric table and one failure-mode example for presentation.

Deliverables at Hour 13:30:

- `P6-M3` signed-off analytical metrics.
- Ground-truth and evaluation method summary.
- False-positive and human-review statement.
- Limitations list.
- Proof that Member 1 did not recalculate your metrics.

Prerequisites you need for Phase 7:

- Member 1: final documentation paths and actual deployed metric response.
- Member 2: responsible-design section outline and wording constraints.

Prerequisites you provide for Phase 7:

- Final data-generation method, scenario configs, metrics table, limitations, false-positive risk, and human-review boundary.

## Phase 7 — Documentation

**Time:** 13:30–14:30  
**Phase output:** `P7-M3` data/analytics evidence documentation.

Write concise factual sections covering:

1. Synthetic generation method and deterministic seeds.
2. Fields/volumes and provider separation.
3. Scenario A–D definitions and expected outputs.
4. Fault injection and data-quality rules.
5. Forecast method, confidence, invalid-forecast behavior, and limitations.
6. Anomaly rule, evidence, benign context, false-positive risk, and human-review boundary.
7. Tuning versus held-out validation split.
8. Metrics with method, sample size, values, and limitations.
9. Explicit statement: anomaly is not proof of fraud.

Checkpoint at Hour 14:00:

- Send Member 1 setup-relevant seed/evaluation commands and Member 3 doc links.
- Send Member 2 human-review, false-positive, privacy, and prohibited-action caveats.

Deliverables at Hour 14:30:

- `P7-M3` complete documentation package.
- Documentation values exactly match `/metrics` and tested release candidate.
- No unsupported production/regulatory claim.

Prerequisites you need for Phase 8:

- Member 1: final slide format and demo reset sequence.
- Member 2: speaker transition into/out of Scenario B and the responsibility section.

Prerequisites you provide for Phase 8:

- Scenario B narration, metric slide content, exact numbers, one limitations statement, and backup evidence captures.

## Phase 8 — Presentation and Rehearsal

**Time:** 14:30–15:30  
**Phase output:** Rehearsed analytical segment and verified results.

### 14:30–14:45 — Prepare

- Recheck every displayed forecast, confidence, evidence count, and metric.
- Prepare a short explanation of the burn-rate forecast.
- Prepare a short explanation of why the repeated-amount pattern was flagged.
- State the plausible benign explanation and human-review boundary.
- Prepare answers on false positives, degraded data, held-out evaluation, and limitations.

### 14:45 rehearsal 1

Deliverables/checkpoint:

- Scenario B completes from a known state.
- Your segment fits its allocated time.
- Transitions from Member 1 and to Member 2 are clear.
- Record only blocking presentation/data inconsistencies; do not add features.

### 15:10 rehearsal 2

Deliverables/checkpoint:

- Final spoken wording.
- Final displayed values checked against `P6-M3`.
- Backup screenshot/result payload ready.
- Confirm who answers analytics, confidence, false-positive, and limitation questions.

Deliverables at Hour 15:30:

- Rehearsed Scenario B and metrics segment.
- Verified backup analytical evidence.
- No mismatch between demo, documentation, and metric payload.

Prerequisites you need for Phase 9:

- Member 1: frozen release identifier and final reset output.
- Member 2: final access/RBAC check result.

Prerequisites you provide for Phase 9:

- Final expected-output checksum/summary, passing test report, metric payload, and secret/safety scan instructions.

## Phase 9 — Final Buffer and Submission

**Time:** 15:30–16:00  
**Phase output:** Final analytical/data sign-off.

### 15:30–15:45 — Final checks

- Run deterministic reset and compare key outputs to the frozen expected sheet.
- Run the smallest critical test set: quality degradation, Scenario A forecast, Scenario B anomaly, Scenario C suppression, provider isolation, safe language.
- Verify metric endpoint values and sample sizes.
- Run final scan for secrets, real data, unsafe actions, and definitive fraud language.
- Confirm sample data and engine configs are included.

Deliverables at 15:45:

- Final Member 3 sign-off or exact blocker statement.
- Passing critical-test summary.
- Metric and expected-output verification.
- Clean safety/secret scan.

### 15:45–16:00 — Submission support

- Observe Member 1's exact final demo; compare outputs without modifying the frozen build.
- Answer only analytical/data questions.
- Fix only a critical Member 3 engine/test/data defect, then require the affected regression to rerun.
- Do not refactor, retune thresholds, change seeds, or add scenarios.

Final deliverables:

- `P1-M3` through `P7-M3` artifacts present.
- Tested engine/config versions recorded.
- Final metrics, limitations, and responsible-use statements present.
- Submission analytical results match the frozen release candidate.

## 9. Test matrix

| Area | Minimum tests |
|---|---|
| Determinism | Same seed/config same records; different seed changes generated values without changing schema |
| Provider separation | No mixed provider window; provider/account/outlet IDs consistent; shared cash has no provider ID |
| Quality | Fresh, exact stale boundary, stale, missing feed, missing field, conflict, malformed, insufficient samples, impossible transition |
| Forecast | Known depletion, shared cash, each provider, zero rate, replenishment, minimum samples, low confidence, widened bounds, decimal precision |
| Anomaly | Known positive, below minimum count, exact amount tolerance, outside tolerance, window boundary, normal event-demand negative, evidence refs, benign explanation |
| Suppression | Stale/missing/conflicting cases; retained evaluation; suppression reason; no anomaly candidate; data advisory expected |
| Contracts | Required fields, enums, score range, timestamp format, provider consistency, result version, unknown additive fields |
| E2E | A–D, reset/replay, alert immutability, case flow visibility, provider denial, no blended total |
| Safety | Prohibited wording/actions, identity-like values, secrets/credentials, production-readiness claims |
| Evaluation | Tuning/held-out isolation, metric formulas, zero-denominator behavior, sample size, method, limitations |

## 10. Defect reporting template

Use this when another member's integration fails your expectation:

```text
Title:
Owner: Member 1 / Member 2 / Member 3
Release/commit:
Scenario + seed:
Input/request:
Expected result:
Actual result:
Failed invariant/test:
Severity: blocker / high / normal
Reproduction command/steps:
Evidence file:
Retest required:
```

Do not report “analytics broken” without a deterministic input and expected output.

## 11. Cut order if behind

Cut in this order without weakening mandatory safety behavior:

1. Additional anomaly patterns beyond near-identical amounts.
2. What-if, relationship, peer, and nearby-agent analysis.
3. Sophisticated forecasting; keep deterministic recent-window depletion.
4. Extra contributing signals; retain at least the essential reason and quality signal.
5. Extra scenario variants; retain normal and A–D.

Never cut:

- Provider separation.
- Confidence and invalid-forecast behavior.
- Evidence and plausible benign explanation.
- Missing/stale/conflicting fallback.
- Anomaly suppression under degraded data.
- Held-out evaluation integrity.
- Human-review/advisory language.

## 12. Personal completion checklist

- [ ] `ResultEnvelope` v1 frozen and consumed by Member 1.
- [ ] Normal and Scenarios A–D deterministic.
- [ ] Generator and fault injection tested.
- [ ] Quality engine emits fresh/stale/missing/conflicting with evidence.
- [ ] Shared cash and all three providers forecast separately.
- [ ] Zero/replenishing/insufficient-sample forecasts safe.
- [ ] Near-identical anomaly evidence complete.
- [ ] Plausible benign explanation always present when actionable.
- [ ] Degraded anomaly evaluations suppressed and retained.
- [ ] Provider isolation and safe-language tests pass.
- [ ] A–D release-candidate regression passes.
- [ ] Held-out metrics include value, sample size, method, and limitations.
- [ ] Data/simulation and analytics documentation complete.
- [ ] Scenario B and metrics presentation rehearsed.
- [ ] Final engine/config versions and expected outputs recorded.
