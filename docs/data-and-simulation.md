# Data and simulation

## Synthetic-only statement

All project data is synthetic. It does not contain real customer names, phone numbers, wallet identifiers, balances, transactions, credentials, PINs, OTPs, passwords, private keys, or provider-production data. Provider proportions and behaviors are simulation assumptions, not claims about real market share or provider performance.

The deterministic moderate dataset is stored in [`data/generated/moderate_demo/`](../data/generated/moderate_demo/). Its manifest records fixed identifiers, seeds, row counts, date coverage, assumptions, and SHA-256 hashes.

## Bangladesh-context assumptions

- Currency is BDT and persisted money uses exact decimal values.
- Synthetic demand includes common round amounts, varied non-round amounts, evening periods, weekends, payments, cash-in, cash-out, refunds, and adjustments.
- Activity is modeled in an Asia/Dhaka operating context but stored as UTC `timestamptz` values.
- bKash, Nagad, and Rocket are represented as logically separate providers; no real integration is implied.
- Shared physical cash belongs to an outlet. Provider-specific e-money belongs to one outlet/provider account.

## Current configured database profile

The repository's secret-free audit command was run against the configured Supabase target on 2026-07-12. The full catalog and row-count artifact is [`data/database-audit.json`](data/database-audit.json).

| Item | Audited value |
|---|---:|
| PostgreSQL | 17.6 |
| Applied migrations | 10 (`001–010`); repository migration `011` pending |
| Public relations | 50 |
| Providers | 3 |
| Areas | 8 total: 4 reference hierarchy rows plus 4 moderate-dataset rows |
| Outlets | 7 total: 2 reference outlets plus 5 moderate-dataset outlets |
| Outlet/provider accounts | 19 total: 4 reference plus 15 moderate-dataset accounts |
| Simulation runs | 10 |
| Transactions | 3,645 |
| Shared-cash snapshots | 900 |
| Provider e-money snapshots | 2,701 |
| Quality assessments / issues | 40 / 18 |
| Liquidity projections | 60 |
| Unusual-activity flags | 24 |
| Alerts / cases | 24 / 15 |
| Ground-truth labels / metric rows | 60 / 16 |

Transaction timestamps cover `2026-06-26T01:00:00Z` through `2026-07-04T15:59:00Z` across nine simulated dates. Balance histories extend through `2026-07-04T20:00:00Z`; alerts and case evidence are dated `2026-07-05`.

### Transaction distribution

| Type | Rows | Share |
|---|---:|---:|
| Cash-out | 1,216 | 33.4% |
| Payment | 1,147 | 31.5% |
| Cash-in | 860 | 23.6% |
| Refund | 257 | 7.1% |
| Adjustment | 165 | 4.5% |

| Status | Rows | Share |
|---|---:|---:|
| Completed | 3,200 | 87.8% |
| Failed | 224 | 6.1% |
| Pending | 150 | 4.1% |
| Reversed | 71 | 1.9% |

Percentages are rounded. Transaction status describes a simulated observation; it does not authorize the prototype to reverse a transaction.

## Deterministic generation and reset strategy

The moderate dataset uses master seed `2026071201`. Each scenario has two fixed seeds:

| Scenario | Seeds |
|---|---|
| Normal | `20261001`, `20261002` |
| A | `20262001`, `20262002` |
| B | `20263001`, `20263002` |
| C | `20264001`, `20264002` |
| D | `20265001`, `20265002` |

Generation writes standalone CSV/JSON artifacts and computes their hashes. Validation is read-only. The loader validates first, uses stable UUIDs, inserts in foreign-key order, uses `ON CONFLICT DO NOTHING`, and defaults to a transactionally rolled-back dry run. Committing requires both a development/local/test `APP_ENV` and the explicit `--apply --confirm-development` flags.

Interactive simulation runs store their seed and configuration. The supported reset endpoint resets only one synthetic simulation run. There is deliberately no cleanup mechanism that bypasses append-only ledger or audit protections.

## Scenario definitions

### Normal

Healthy, varied provider activity with fresh feeds and no intentionally injected high-impact condition.

### Scenario A — hidden shared-cash shortage

The implemented Scenario A is an adaptation of the official hidden-shortage example. Heavy bKash cash-out demand decreases shared physical cash while bKash e-money rises. The system must show the shared-cash projection and provider balances separately, including shortage timing and confidence, without presenting a combined total.

This demonstrates the reserve-separation problem but is not a provider-e-money shortage; that difference from the illustrative official wording is intentional and documented.

### Scenario B — liquidity pressure with unusual activity

Falling shared cash is paired with a provider-scoped repeated/near-identical amount cluster. Analytics persist structured evidence, confidence, exact transaction links, and a plausible benign explanation. Alert publication remains advisory and requires human review.

### Scenario C — degraded or conflicting data

The scenario includes delayed input, missing feed, missing field, malformed payload, and conflicting balance observations. Quality status and issue evidence are persisted. Missing/conflicting quality reduces confidence; otherwise detectable unusual activity is retained as suppressed evidence and cannot create a high-confidence anomaly alert.

### Scenario D — coordinated response and closure

The moderate dataset contains provider-aware cases with assignment, status history, acknowledgement, escalation, notes, reviews, resolution summaries, notifications, and audit events. The API scenario regression builds this workflow from a Scenario B alert because case behavior is driven by an alert rather than a separate analytical pattern.

## Fault injection

| Fault | Effect |
|---|---|
| `delay` | Moves receipt time later than source observation time. |
| `missing_feed` | Produces a provider window with no usable feed sample. |
| `missing_field` | Creates input that normalization rejects for an absent required value. |
| `malformed_payload` | Preserves a rejected ingestion event without creating a ledger row. |
| `conflicting_balance` | Preserves multiple provider balances for the same account/time and exposes conflict state. |

## Balance and ledger generation

Transactions have positive amounts and explicit type/status. For the simulated agent ledger, cash-out decreases shared physical cash and increases the relevant provider e-money balance; cash-in does the inverse. Payment/refund/adjustment observations follow the generator's documented synthetic direction rules. Every provider row must match one outlet/provider account, while shared-cash rows cannot carry a provider identifier.

Balance snapshots are append-only. Conflicting snapshots remain side by side so quality logic and read models can distinguish the last trusted balance from untrusted candidates.

## Ground truth and unusual-activity generation

Two validation runs are included: one `demo` split and one `held_out` split. Together they contain 60 labels for shortage, unusual activity, normal behavior, and data-quality incidents. Metric rows are duplicated by split; final reported values use the held-out run.

The moderate population contains 24 near-identical-amount flags:

- 10 `requires_review`
- 5 `suppressed_data_quality`
- 4 `dismissed_benign`
- 3 `inconclusive`
- 2 `confirmed_unusual`

Benign-lookalike cases deliberately create false positives and dismissed outcomes. The dataset does not currently provide equally sized evaluation populations for velocity, balance-inconsistency, or behavioral-embedding detectors, even though those detectors exist in the runtime.

## Reproduction

From `backend` with the Python environment active:

```powershell
python -m app.scripts.generate_moderate_dataset
python -m app.scripts.validate_moderate_dataset
python -m app.scripts.load_moderate_dataset
```

Apply only to an explicitly disposable/development database:

```powershell
python -m app.scripts.load_moderate_dataset --apply --confirm-development
```

Refresh the configured database audit without printing credentials:

```powershell
python -m app.scripts.audit_database
```

## Evidence and limitations

- Dataset manifest: [`data/generated/moderate_demo/manifest.json`](../data/generated/moderate_demo/manifest.json)
- Dataset validation: [`data/generated/moderate_demo/validation-report.json`](../data/generated/moderate_demo/validation-report.json)
- Loader report: [`data/generated/moderate_demo/apply-report.json`](../data/generated/moderate_demo/apply-report.json)
- Current database audit: [`docs/data/database-audit.json`](data/database-audit.json)
- Metric interpretation: [`validation-evidence.md`](validation-evidence.md)

Limitations:

- All distributions, behaviors, balances, labels, and outcomes are authored simulation assumptions.
- The date window, outlet count, and provider count are small compared with production networks.
- Stored moderate metrics are deterministic fixture evidence, not an independent field evaluation.
- The configured database contains repository data through migration `010`; migration `011` and the similar-case seed corpus were not present at audit time.
- No real provider interface, customer identity, geographic behavior, regulatory rule, or production baseline is represented.
