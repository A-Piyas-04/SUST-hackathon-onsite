# Multi-Provider Agent Liquidity & Coordination Platform

Decision-support prototype for multi-provider mobile-money agents. Shared physical cash and separate provider e-money reserves are never blended.

## Repository layout

```
backend/     FastAPI modular monolith + PostgreSQL schema (Phases 1–2)
frontend/    Thin Next.js shell (Phase 2 scaffold; feature UI in Phase 6)
docs/        Authoritative schema, phase plan, OpenAPI baseline
```

Authoritative data contract: [`docs/schema.md`](docs/schema.md).

## Quick start (local)

### Docker (whole project)

Build and start PostgreSQL, apply migrations and reference seeds, then bootstrap
deterministic demo data (normal + scenarios A/B/C: analytics, published alerts,
and a routed case), and run the API and frontend:

```bash
docker compose up --build -d
docker compose ps
```

Open http://localhost:3000. The API health endpoint is available at
http://localhost:8000/health and PostgreSQL is exposed on host port `5433`.

To stop the stack, run `docker compose down`. Add `--volumes` only when you
also want to delete the local database data.

The browser only talks to the frontend origin; the Next server proxies
`/api/*` and `/health` to the backend over the Compose network, so the app
also works when opened from another device (e.g. `http://<your-lan-ip>:3000`).

To build and run only the frontend image, pass the backend address the proxy
should target (defaults to `http://backend:8000`, the Compose service):

```bash
docker build --build-arg API_PROXY_TARGET=http://host.docker.internal:8000 -t liquidity-frontend ./frontend
docker run --rm -p 3000:3000 liquidity-frontend
```

If browsers should instead call a separately exposed backend origin directly,
set `NEXT_PUBLIC_API_BASE_URL` before building the Compose stack.

### 1. Database

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# For local Postgres (recommended for development):
# DIRECT_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/liquidity_platform

make db-up
make migrate
make seed
```

### 2. Backend API

```bash
cd backend
make server
# Health: http://localhost:8000/health
```

### 3. Frontend shell

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
# http://localhost:3000 — shows backend connectivity status
```

### 4. Tests and OpenAPI

```bash
cd backend
make test
make openapi
# OpenAPI artifact: docs/openapi/openapi.v1.json
```

## Command reference

| Command | Purpose |
|---|---|
| `make db-up` | Start local Postgres (port 5433) |
| `make migrate` | Apply schema migrations |
| `make seed` | Load reference/demo seeds |
| `make server` | Run FastAPI app |
| `make test` | Run all backend tests |
| `make test-contracts` | Run contract fixture tests only |
| `make verify` | Run Phase 1 schema/RLS tests |
| `make openapi` | Generate OpenAPI baseline |

## Phase status

- **Phase 1:** Complete — full PostgreSQL schema, migrations, seeds, RLS tests.
- **Phase 2:** Complete — app foundation, v1 contracts, `/health`, auth boundary stubs, OpenAPI baseline, frontend shell.
- **Phase 3+:** Business features (ingestion, ledger, analytics, alerts/cases) are stubbed with `501 not_implemented`.

## Safety guardrails

- Advisory decision-support only — no transfers, settlements, freezes, or fraud verdicts.
- Provider reserves (bKash, Nagad, Rocket) remain separate from shared physical cash.
- Synthetic/demo data only.

See [`docs/Problem_Statement.md`](docs/Problem_Statement.md) and [`docs/16-hour-hackathon-phase-distribution.md`](docs/16-hour-hackathon-phase-distribution.md).
