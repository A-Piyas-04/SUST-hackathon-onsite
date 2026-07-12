# Multi-Provider Agent Liquidity & Coordination Platform

**Codex Community Hackathon — bKash presents SUST CSE Carnival 2026**

Mobile-financial-service agents often share one physical cash drawer while maintaining separate e-money positions for bKash, Nagad, Rocket, and other providers. This prototype helps an agent and authorized provider teams see possible liquidity pressure, review unusual activity with evidence and uncertainty, and coordinate a human response without blending provider balances or performing financial actions.

## What the prototype does

The connected workflow is:

```text
synthetic provider data
→ normalization and quality assessment
→ shared-cash / provider-e-money ledger separation
→ liquidity and unusual-activity analysis
→ immutable, explainable alert
→ provider-aware mutable case
→ acknowledgement / escalation / review / resolution
→ audit and validation evidence
```

Main capabilities:

- One shared physical cash reserve and separate provider-specific e-money accounts; no blended total.
- Deterministic simulation for normal operation and Scenarios A–D, including degraded feeds.
- Transparent burn-rate liquidity projections with confidence, sample count, and time bounds.
- Four independent unusual-activity detectors: near-identical amounts, velocity spike, balance inconsistency, and provider/outlet-scoped behavioral k-NN distance.
- Quality-aware suppression when input is missing or conflicting.
- Structured English, Bangla, and Banglish alert explanations with situation, evidence, uncertainty, and next step.
- Provider-aware routing, ownership, acknowledgement, escalation, notes, review, resolution, notification, and immutable audit history.
- Application authorization plus PostgreSQL Row Level Security (RLS).
- Deterministic moderate synthetic dataset and measured validation evidence.

### Working prototype: live demo flow

1. Run `docker compose up --build -d`, open `http://localhost:3000`, and sign in as `agent`.
2. Open the dashboard to view one shared physical cash reserve alongside separate bKash, Nagad, and Rocket e-money balances. The system never presents a blended total.
3. Run Scenario B, then open **Alerts** to inspect a liquidity/unusual-activity alert, its evidence, confidence, uncertainty, plausible benign explanation, and suggested human next step.
4. Open the linked **Case**. An authorized provider user such as `bkash_ops` can assign, acknowledge, escalate, add a review/note, and resolve the case. The case status history, notifications, and append-only audit trail show coordinated human escalation rather than automated enforcement.

Scenario A demonstrates hidden shared-cash shortage; Scenario C demonstrates stale, missing, malformed, and conflicting feed handling that reduces confidence and suppresses unsafe alerting; Scenario D demonstrates coordinated closure.

### Source repository and setup

The repository includes a Next.js frontend, FastAPI backend, PostgreSQL migrations and seeds, deterministic sample data, automated tests, Docker configuration, and `backend/.env.example` for environment configuration. The quick-start and manual setup instructions in this README are sufficient to run the prototype; the synthetic dataset is stored under `data/generated/moderate_demo`.

### Architecture diagram

```mermaid
flowchart LR
    UI["Role-aware Next.js interface"] --> API["FastAPI API boundary\nAuth, authorization, request logging"]
    FEEDS["Synthetic bKash / Nagad / Rocket feeds"] --> INGEST["Ingestion, validation, normalization\nand fault injection"]
    INGEST --> LEDGER["PostgreSQL separated ledger\nshared cash + provider e-money"]
    LEDGER --> QUALITY["Data-quality assessment\nfresh / stale / missing / conflicting"]
    QUALITY --> LIQ["Liquidity projection\ntransparent burn-rate model"]
    QUALITY --> ANOM["Unusual-activity detectors\namount, velocity, balance, behavior"]
    LIQ --> ALERT["Immutable explainable alert"]
    ANOM --> ALERT
    ALERT --> CASE["Provider-aware case workflow\nassign, acknowledge, escalate, review, resolve"]
    CASE --> AUDIT["Notifications and append-only audit"]
    API --> LEDGER
    API --> ALERT
    API --> CASE
    LEDGER --> METRICS["Validation results, protected metrics\nhealth and monitoring"]
    QUALITY --> METRICS
    LIQ --> METRICS
    ANOM --> METRICS
```

Provider boundaries are enforced in the API and PostgreSQL Row Level Security. Shared physical cash is kept distinct from each provider's e-money account in tables, views, contracts, and analytics. The analytics layer is deterministic by default; an optional confidence calibrator is used only when a valid, sufficiently supported artifact is available.

### Data and simulation note

All provider, outlet, party, account, transaction, balance, alert, case, and audit records are synthetic and deterministic. The generator creates provider-labelled transactions, shared-cash snapshots, separate provider e-money snapshots, ground-truth labels, and case/audit records for a fixed moderate demonstration dataset. Re-running the generator with its fixed scenario configuration produces the same dataset for repeatable judging.

The simulations model four situations: hidden shared-cash depletion (A), falling cash with unusual repeated amounts (B), degraded data feeds (C), and an escalated case that receives human closure (D). Fault injection can simulate delayed feeds, missing feeds/fields, malformed payloads, and conflicting balance observations. Invalid input is retained as ingestion evidence but does not create trusted ledger rows.

Assumptions and limitations: this is not a real provider integration; demand is represented by a transparent recent-window burn-rate model, not a production forecast; labels and cases are synthetic; the provider/outlet population is intentionally small; and results do not establish real-world fraud accuracy, fairness, regulatory compliance, or production capacity.

### Validation evidence

The Phase 7 held-out validation harness measured frozen synthetic Scenario A/B/C runs (seeds `2001`, `2002`, and `2003`) using engine version `validation-v1`. These are measured results, not the authored fixture-consistency values embedded in the sample dataset.

| Measured metric | Result | Sample and method | Interpretation / limit |
|---|---:|---|---|
| Anomaly precision | 100% | 1 predicted-positive scenario-provider cell; `TP / (TP + FP)` | The one alertable Scenario B cell was correct; sample is too small for a production claim. |
| Anomaly recall | 100% | 1 labelled-positive cell; `TP / (TP + FN)` | Detects the held-out repeated-amount anomaly only; it does not establish recall for every detector. |
| False-positive rate | 0% | 8 labelled-negative cells; `FP / (FP + TN)` | Includes the safely suppressed degraded-data Scenario C path. |
| Shortage detection lead time | 534.34 minutes | 1 Scenario A shared-cash projection; projected shortage time minus observation time | Demonstrates lead time on a frozen synthetic depletion slope, not demand-forecast accuracy. |
| Data-quality incident rate | 11.11% | 1 degraded assessment out of 9 provider assessments | Scenario C injection only; not a field reliability rate. |
| API average / p95 latency | 318.67 ms / 1040.88 ms | 90 in-process handler calls: 30 iterations across 3 read endpoints | Excludes network/TLS/transport and is not a load test. |

Validation also confirmed complete English explanation sections for 2 of 2 published high-impact alerts. Reproduce the checks with `python -m app.scripts.validation_cli run`, `python -m app.scripts.validate_moderate_dataset`, `python -m pytest tests\phase7 -q`, and `python -m app.scripts.safety_scan` from `backend`.

### Responsible design

This prototype is advisory decision support, not an automated decision-maker. It uses synthetic data only; contains no real customer identities, PINs, OTPs, passwords, private keys, or provider credentials; and does not expose one provider's confidential data to another. Users receive evidence, confidence, data-quality context, a plausible benign explanation, and a suggested review step. A flag means an unusual pattern requires review; it is not proof of fraud or misconduct.

Human review is required for case outcomes. Missing, stale, conflicting, or insufficient data reduces confidence; liquidity projections can become non-actionable, and unusual-activity results can be suppressed rather than published. Benign demand spikes, repeated round amounts, delayed feeds, and synchronization failures can resemble suspicious activity, so reviewers must consider context and provider procedures before taking any external action.

The prototype intentionally cannot transfer, convert, settle, refill, recover, reverse, block, or freeze funds; access real provider APIs or customer accounts; accuse an agent or customer; make a final fraud determination; or automatically execute a recommendation or case outcome. It is not production-, regulatory-, security-, privacy-, or fairness-assessed.


## Technology

| Layer | Current implementation |
|---|---|
| Frontend | Next.js 16.2.10, React 19.2.4, TypeScript, Tailwind CSS 4, TanStack Query 5 |
| Backend | Python/FastAPI modular monolith, SQLAlchemy async, Pydantic 2 |
| Analytics | Deterministic rules, burn-rate forecast, scikit-learn calibration/retrieval utilities |
| Database | PostgreSQL 15+ / Supabase PostgreSQL; local container uses PostgreSQL 16 |
| Runtime images | Python 3.13 and Node.js 22 |
| Verification | Pytest, Playwright, deterministic dataset validator, safety scan, SonarQube workflow |

## Repository layout

```text
backend/                     FastAPI application, migrations, seeds, analytics, tests
frontend/                    Next.js role-aware web interface and Playwright demo spec
data/generated/moderate_demo Deterministic synthetic dataset and validation manifest
docs/                        Documentation, contracts, evidence, and architecture diagram
```

## Quick start with Docker

Prerequisites: Docker Desktop with Compose.

```powershell
docker compose up --build -d
docker compose ps
```

Compose starts PostgreSQL on `localhost:5433`, applies migrations and reference seeds, bootstraps demo data, then starts:

- Frontend: <http://localhost:3000>
- API health: <http://localhost:8000/health>
- OpenAPI UI: <http://localhost:8000/docs>

Stop without deleting the database volume:

```powershell
docker compose down
```

## Manual setup

Prerequisites:

- Python 3.11–3.13
- Node.js 22 (Node.js 20+ is expected to work)
- PostgreSQL 15+ or a Supabase PostgreSQL project

Create the Python environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
```

Create the backend environment file:

```powershell
Copy-Item backend\.env.example backend\.env
```

Set either `DIRECT_DATABASE_URL` or `DATABASE_URL` in `backend/.env`. For local PostgreSQL on port 5432:

```env
APP_ENV=development
DIRECT_DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/liquidity_platform
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/liquidity_platform
DEMO_AUTH_ENABLED=true
```

For Supabase, copy the current direct or session-pooler PostgreSQL URL from the project dashboard. Keep `SUPABASE_SERVICE_ROLE_KEY`, database passwords, and connection strings on the backend only; never expose them through `NEXT_PUBLIC_*` variables.

Apply the complete forward-only migration chain and idempotent seeds:

```powershell
cd backend
python migrations\run_migrations.py status
python migrations\run_migrations.py apply
python migrations\run_migrations.py seed
```

Start the API:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend proxies `/api/*` and `/health` to `http://localhost:8000` by default. Set `API_PROXY_TARGET` only when the backend uses another address.

## Deterministic dataset and demo data

Generate and validate the standalone moderate dataset without database writes:

```powershell
cd backend
python -m app.scripts.generate_moderate_dataset
python -m app.scripts.validate_moderate_dataset
python -m app.scripts.load_moderate_dataset
```

The loader defaults to a transactionally rolled-back dry run. To commit it to an explicitly development-classified database:

```powershell
python -m app.scripts.load_moderate_dataset --apply --confirm-development
```

For a small interactive demo bootstrap:

```powershell
python -m app.scripts.bootstrap_demo --outlet-id 0b000000-0000-0000-0000-000000000001
```

Reset one synthetic simulation run through the supported workflow:

```powershell
python -m app.scripts.simulation_cli reset --run-id <RUN_UUID>
```

The project intentionally provides no command that bypasses append-only protections to erase historical ledger or case evidence.

## Demo identities

The login screen requests a seeded synthetic identity; there are no real passwords or secrets.

| Login key | Scope |
|---|---|
| `agent` / `agent2` | One assigned outlet |
| `bkash_ops`, `nagad_ops`, `rocket_ops` | One provider |
| `area_manager` | bKash in one synthetic area |
| `risk_analyst` | bKash review scope |
| `management` | Aggregate management views; not a provider wildcard |
| `admin` | Demo setup and internal controls |

## Demonstration scenarios

| Scenario | Implemented demonstration |
|---|---|
| A — hidden shortage | bKash cash-out demand depletes shared physical cash while bKash e-money rises; reserves remain separate. |
| B — liquidity pressure with unusual activity | Repeated amounts and falling cash produce evidence-backed output with a plausible benign explanation. |
| C — degraded/conflicting data | Delay, missing data, malformed input, and conflicting balances reduce confidence and suppress unsafe alerting. |
| D — coordinated closure | A provider-aware case is assigned, acknowledged, escalated/reviewed, resolved, and audited. |

The judge demo flow above is the connected walkthrough. It can be reset with the supported simulation reset command shown in the dataset section.

## Verification commands

Run from `backend` unless stated otherwise:

```powershell
python -m pytest tests -q
python -m app.scripts.validate_moderate_dataset
python -m app.scripts.safety_scan
python -m app.scripts.generate_openapi
```

Frontend checks:

```powershell
cd frontend
npm run lint
npx tsc --noEmit
npx playwright test
```

The generated API contract is [docs/openapi/openapi.v1.json](docs/openapi/openapi.v1.json). A concise guide is in [docs/api-reference.md](docs/api-reference.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Data and simulation](docs/data-and-simulation.md)
- [Validation evidence](docs/validation-evidence.md)
- [Responsible design](docs/responsible-design.md)
- [API reference](docs/api-reference.md)
- [Canonical schema](docs/schema.md)
- [Official problem statement](docs/Problem_Statement.md)

## Responsible-use boundary and limitations

This is a synthetic-data, advisory prototype. It cannot transfer or convert balances, settle funds, refill wallets, reverse real transactions, block users, freeze funds, accuse an agent or customer, or make a final fraud determination. It does not connect to real provider APIs and is not production- or regulatory-ready.

Current limitations include synthetic-only validation, simple forecasting assumptions, a modest deterministic evaluation population, demo authentication, no current production load test, and a browser E2E script that requires re-verification against the latest UI. The configured Supabase audit on 2026-07-12 found migration `011_case_similar_embeddings.sql` pending; run the documented migration command before demonstrating similar-case retrieval.
