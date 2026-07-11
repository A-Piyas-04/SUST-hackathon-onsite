# Moderate synthetic dataset profile

## Purpose and safety

This deterministic dataset supports the Multi-Provider Agent Liquidity & Coordination Platform demo with synthetic Bangladesh-context bKash, Nagad, and Rocket activity. It contains no real identity, phone, wallet, merchant, credential, or provider-production data. Provider shares and behavioral patterns are simulation assumptions, not market-share claims. It represents advisory observations only and performs no transfer, settlement, refill, recovery, reversal, account blocking, or fund freezing.

## Database audit

The audit is at `docs/data/database-audit.json`. The configured Supabase database reported PostgreSQL 17.6, 43 public tables, 7 views, 473 columns, all catalog constraints/triggers/functions/indexes/grants/RLS policies, and migrations 001–008 with matching runner status. Operational tables were empty before seeding. Existing reference rows were preserved: 3 providers, 5 scenarios, 4 areas, 2 outlets, 4 accounts, 9 users/scopes, 1 anomaly rule, and 5 routing rules. The idempotent reference seed was rerun to add four localized explanation templates missing from the older live reference-seed state.

The physical schema follows `schema.md` through migration 006. Additions are the migration-007 `coordination_idempotency_keys` replay-defense table and migration-008 dashboard last-trusted/conflict view correction. The remote physical schema now matches repository migration head; no missing/renamed seed-target columns or weakened constraints were found. Applied migrations were not edited. Safe insertion order is encoded in `load_moderate_dataset.py` from reference entities through validation metrics.

## Dataset design

- Master seed: `2026071201`.
- Scenario seeds: normal `20261001/20261002`; A `20262001/20262002`; B `20263001/20263002`; C `20264001/20264002`; D `20265001/20265002`.
- Fixed UTC range: `2026-06-26T00:00:00Z` through `2026-07-05T00:00:00Z`; Asia/Dhaka demand hours are converted to UTC.
- Scope: 5 synthetic outlets, 4 synthetic areas, exactly 3 providers, and 15 separate outlet/provider accounts.
- Activity: 3,645 transactions; 900 shared-cash snapshots; 2,701 provider e-money snapshots. Payment/refund activity, evenings, weekends, common BDT values, and a broad non-round amount range are included.
- Scenarios: 2 immutable completed runs for each of normal and A–D. Scenario C includes delay, missing feed/field, conflicts, and malformed payload. Scenario D includes assignments, acknowledgement, escalation, notes, review, resolution, notification, and audit history.
- Analytics/workflow: 40 quality assessments, 18 issues, 60 projections, 24 anomaly flags, 24 typed-source alerts, 15 cases, 60 labels, and 16 metric rows across two validation runs.

Exact per-file counts and SHA-256 hashes are in `data/generated/moderate_demo/manifest.json`. Validation results are in `data/generated/moderate_demo/validation-report.json` (64 passed, 0 failed).

## Commands

Run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.audit_database
.\.venv\Scripts\python.exe -m app.scripts.generate_moderate_dataset
.\.venv\Scripts\python.exe -m app.scripts.validate_moderate_dataset
.\.venv\Scripts\python.exe -m app.scripts.load_moderate_dataset
.\.venv\Scripts\python.exe -m app.scripts.load_moderate_dataset --apply --confirm-development
```

The loader validates first, defaults to a rolled-back dry-run, requires `APP_ENV=development|local|test` plus explicit confirmation to commit, uses stable UUIDs and transactional `ON CONFLICT DO NOTHING`, preserves unrelated data, and reports inserted/skipped/conflicted rows. No cleanup script is supplied because ledger/workflow tables are append-only and their protections must not be bypassed.

## Validation and evidence

Validation checks provider/outlet/account consistency, exact decimals, UTC timestamps, reference syntax, scenario/fault coverage, separate reserves, preserved conflicts, quality suppression, analytical reproducibility, typed alert sources, legal case history/current state/current owner, notification/audit scope, safe language, and stable file hashes. Metrics are deterministic formulas recorded in each metric's method/details; precision and recall are 0.8 from TP=8, FP=2, FN=2; FPR is 0.1 from FP=2, TN=18; coverage/completeness/denial metrics are evidence ratios; shortage lead time is the documented median of six labelled results.

Existing `docs/evidence` metrics were inspected but not imported: their seeds (2001–2003), release commit, engine versions, and small held-out population do not match this dataset's seeds/configuration/population. They remain valid evidence for their original harness only.

## Verification status and limitations

An isolated PostgreSQL 16 database applied migrations 001–008 and reference seeds, passed a full dry-run, then committed all generated rows. A second commit inserted zero and skipped every row, proving idempotency. The repository's view/RLS/append-only suite passed 22/22 against that populated database.

The configured Supabase target was audited but not populated. An orphaned, uncommitted earlier loader session was identified through `pg_stat_activity`, safely terminated after strict PID/state/age/query checks, and rolled back by PostgreSQL. Migration 008 and the current idempotent reference seed were applied. A subsequent complete remote dry-run inserted every generated row through all deferred constraints and rolled back successfully. The commit guard then refused application because `backend/.env` declares `APP_ENV=production`; the task permits development Supabase application only. No remote population is claimed. Remote API/frontend non-empty-state verification and post-seed provider A/B checks remain pending until the target is explicitly and truthfully classified as development.
