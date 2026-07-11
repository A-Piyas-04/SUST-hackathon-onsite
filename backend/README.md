# Backend — Multi-Provider Agent Liquidity & Coordination Platform

**Phase 1 owner:** Member 1 — Data & Intelligence APIs.

This is a **decision-support / advisory prototype only**, never a fraud or
financial-action system. See [Hard guardrails](#hard-guardrails) below —
they apply to every file in this repository, not just this phase's.

## Ownership boundary (this phase)

Member 1 owns: reference data, simulation, ingestion, ledger, dashboard
reads, data quality, analytics persistence/adapters, health and metrics
delivery, and the shared OpenAPI file / app composition / DB connection /
startup path — everything under `app/member1/**`, `app/core/**`,
`app/shared/**`, `migrations/001,002,003,005`, `openapi/openapi.yaml`,
`fixtures/**`.

Member 1 does **not** own and has **not** implemented real logic for:
authentication, alert/case workflow, RBAC policy content, or Member 3's
forecast/anomaly formulas. Every one of those seams is an explicit
`# TODO(owner=Member2): ...` / `# TODO(owner=Member3): ...` stub with the
correct interface shape — grep the codebase for `TODO(owner=` to find them
all. `app/member2_stub/README.md`, `migrations/004_coordination.sql`, and
`migrations/006_security.sql` contain only their one-line placeholder, by
design.

## Hard guardrails

Copied verbatim from the Phase 1 task brief (§0) — apply to every file:

1. This is a decision-support / advisory system only. Never create an
   endpoint, table, or field named or capable of: transfer, convert, settle,
   refill, recover, reverse, block, freeze, accuse, or any fraud-decision
   action.
2. Shared physical cash and each provider's e-money balance (bKash, Nagad,
   Rocket) are always separate — never sum, blend, or convert between them
   anywhere, including in views, DTOs, or sample responses.
3. All data is synthetic. Never use real phone numbers, account numbers,
   names, PINs, OTPs, passwords, or credentials, even as placeholder/example
   values.
4. Alerts are immutable evidence; cases are separate mutable workflow
   records (Member 2 owns cases — Member 1 only produces the analytical
   evidence that feeds them).

Verification: `git grep -nE "transfer|convert|settle|refill|recover|reverse|block|freeze|accuse|fraud" -- app migrations openapi fixtures`
should return nothing except explanatory/negative comments (e.g. this
README, or a comment stating no such endpoint exists).

## Prerequisites

- Python 3.12+
- Docker Desktop (for local Postgres — see [Database](#database) below)

## Setup

```bash
cd backend
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Windows: Copy-Item .env.example .env
```

`.env` is git-ignored; `.env.example` documents every variable name with a
comment and no real values (guardrail #3 extends to config too).

## Database

**Local dev (this phase):** a Docker Postgres container, started via
`docker-compose.yml`, on **host port 5433** (not 5432 — chosen to avoid
colliding with any native Postgres already running on your machine).

```bash
docker compose up -d
python migrations/run_migrations.py
python scripts/seed_demo_data.py   # optional: one demo outlet + calm baseline balances
```

**Supabase (later phases):** swap `DATABASE_URL` / `MIGRATIONS_DATABASE_URL`
in `.env` for the Supabase pooled connection string (async driver prefix
`postgresql+asyncpg://` for `DATABASE_URL`, plain `postgresql://` for
`MIGRATIONS_DATABASE_URL`) — no code changes needed, `run_migrations.py`
works against either target.

`run_migrations.py` applies `migrations/*.sql` in numeric filename order,
tracks applied filenames in a `schema_migrations` table, is idempotent
(safe to re-run), and prints which migrations are pending before applying:

```bash
python migrations/run_migrations.py --check   # list pending only, apply nothing
python migrations/run_migrations.py           # apply all pending migrations
```

## Running the server

```bash
uvicorn app.main:app --reload --port 8000
```

- `GET /health` — liveness + DB connectivity check.
- `GET /docs` — interactive OpenAPI docs (Swagger UI), generated live from the same routes as `openapi/openapi.yaml`.
- `GET /openapi.json` — live schema; regenerate the frozen YAML file anytime with `python scripts/export_openapi.py`.

## Migration / table ownership map

| File | Owner | Contents |
|---|---|---|
| `001_foundation.sql` | Member 1 | enums (as text+CHECK), `areas`, `providers` (seeded bKash/Nagad/Rocket), `outlets`, `outlet_provider_accounts` |
| `002_simulation_and_ledger.sql` | Member 1 | `simulation_scenarios/runs`, `fault_injections`, `ingestion_batches/events`, `transactions`, `cash_balance_snapshots` (no `provider_id`, ever), `provider_balance_snapshots` (conflicting rows allowed), integrity triggers |
| `003_intelligence.sql` | Member 1 | `data_quality_assessments/issues`, `analytics_runs`, `liquidity_projections` (+signals/quality join), `anomaly_rules` (only `near_identical_amounts` seeded active), `anomaly_flags/evidence_items/flag_transactions` |
| `004_coordination.sql` | **Member 2** | reserved placeholder only — do not implement here |
| `005_validation_and_reads.sql` | Member 1 | `validation_runs`, `ground_truth_labels`, `metric_results`, and every read view (`v_latest_cash_balance`, `v_latest_provider_balances`, `v_current_feed_health`, `v_latest_liquidity_projections`, `v_outlet_dashboard`, `v_validation_summary`); `v_case_timeline` stubbed as a `-- TODO` comment (unions Member 2's tables) |
| `006_security.sql` | **Member 2** | reserved placeholder only — do not implement here |

## Decision records (deviations from docs/schema.md, documented per file)

1. `simulation_runs.started_by_user_id` and `validation_runs.created_by_user_id`
   are plain nullable `uuid` columns **without** a foreign key to `app_users`
   in this phase — `app_users` is Member 2's table and doesn't exist yet.
   `# TODO(owner=Member2)` marks both spots.
2. `ingestion_batches.provider_id` is required (schema.md lists no
   "nullable" on this column), so shared-cash balance snapshots use
   `source_kind IN ('seed','derived')` and are written directly, skipping
   an ingestion batch/event, rather than inventing an unmodeled "cash
   provider". `cash_balance_snapshots.ingestion_event_id` being nullable
   supports exactly this.
3. `anomaly_flags.plausible_benign_explanation` is required whenever
   `disposition <> 'suppressed_data_quality'` (schema.md invariant #9 says
   "when actionable"; `suppressed_data_quality` is the one disposition
   that's explicitly non-actionable per invariant #10).
4. `v_outlet_dashboard` does not join alerts (Member 2's table doesn't exist
   yet) — the API layer adds `"alerts": []` itself, matching the task's own
   allowance ("empty array is fine now").

No other deviations from `docs/schema.md`.

## Canonical seam contracts (Pydantic + fixtures)

Three contracts are the seams between Member 1, Member 2, and Member 3 —
defined in `app/member1/adapters/`, with one example fixture each in
`fixtures/`:

- **`ResultEnvelope`** (Member 3 → Member 1): `result_envelope.py`. Discriminated
  union on `engine` (`liquidity | anomaly | data_quality`), each variant
  mapping 1:1 onto its persistence table from `docs/schema.md` §9.
- **`AlertCandidate`** (Member 1 → Member 2): `alert_candidate.py`. No
  `status`/`owner`/`assignment` field exists on this model — enforced by
  construction, not just convention.
- **Validation-metric payload** (`/metrics`, `/api/v1/validation/results`):
  `validation_payload.py`.

Run `python scripts/verify_fixtures.py` to check all five fixture files
against their Pydantic contracts, and to prove the exit-gate requirement
that a hand-written `ResultEnvelope` fixture can be turned into a valid
`AlertCandidate` without touching any Member 2/3 file:

```bash
python scripts/verify_fixtures.py
```

## Demo control plan (thin controls to build in later phases)

The endpoints already exist to support these controls once a UI/CLI wraps
them — no backend redesign needed:

- **Start scenario**: `POST /api/v1/simulations/runs` with a `scenario_code`
  from `GET /api/v1/simulations/scenarios` (`normal`, `scenario_a..d`).
- **Toggle a fault live**: `POST .../faults` to create one, `PATCH
  .../faults/{faultId}` to enable/disable it — drives Scenario C (missing/
  conflicting feed) live during a demo.
- **Reset**: `POST /api/v1/simulations/runs/{runId}/reset`.
- **Feed synthetic data**: `POST /api/v1/ingestion/batches`.
- **Trigger analytics (until Member 3's real engine lands)**: `POST
  /api/v1/internal/analytics/{liquidity,anomalies}/run` with a hand-built
  `ResultEnvelope`-shaped body — returns the validated envelope plus the
  derived `AlertCandidate`.

## Demo sequence draft (3-5 minutes)

1. **Boot** (30s) — `uvicorn app.main:app`; show `GET /health` returning `ok`
   with a live DB check.
2. **Unified visibility** (45s) — `GET /outlets/{id}/dashboard`: point out
   the shared-cash object and the three separate bKash/Nagad/Rocket
   provider objects — never a blended total.
3. **Liquidity intelligence** (45s) — `GET .../liquidity-projections`;
   show a projected shortage with `confidence_level` and
   `non_actionable_reason` when flat.
4. **Data quality honesty** (45s) — `GET .../data-quality`; toggle a fault
   (`POST .../faults`, `PATCH .../faults/{id}`), show the status flip to
   `stale`/`conflicting`.
5. **Anomaly suppression under bad data (Scenario C)** (45s) — POST an
   anomaly `ResultEnvelope` with `disposition=suppressed_data_quality` to
   `/internal/analytics/anomalies/run`; show `requires_case: false` in the
   derived `AlertCandidate` — a degraded feed cannot manufacture a new
   high-confidence alert.
6. **Contract, not vibes** (30s) — open `/docs` or `openapi/openapi.yaml`;
   show Member 2's placeholder paths already reserved and versioned.

## Exit-gate checklist (Phase 1)

- [x] Every Member 1 capability maps to a real endpoint/table/view or an
      explicit `# TODO(owner=...)` stub.
- [x] A hand-written `ResultEnvelope` fixture produces a valid
      `AlertCandidate` fixture without touching Member 2/3 files (`python
      scripts/verify_fixtures.py`).
- [x] No endpoint/table/column/enum value transfers money, merges wallets,
      blocks/freezes a user, exposes a real identity, or declares fraud.
- [x] `app/member2_stub/`, `004_coordination.sql`, `006_security.sql`
      contain only their placeholder line.
- [x] Server boots, migrations apply against local Postgres, `/health` and
      several GET routes verified — see verification log in the phase
      report.
