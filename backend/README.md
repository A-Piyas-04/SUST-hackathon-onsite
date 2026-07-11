# Backend — Phase 1 Schema + Phase 2 Application Foundation

Authoritative PostgreSQL / Supabase schema and a runnable FastAPI modular monolith for the **Multi-Provider Agent Liquidity & Coordination Platform**.

The authoritative contract is [`docs/schema.md`](../docs/schema.md). Phase plan: [`docs/16-hour-hackathon-phase-distribution.md`](../docs/16-hour-hackathon-phase-distribution.md).

## Layout

```
backend/
  app/
    main.py                 # Application factory + uvicorn entry
    core/                   # config, logging, errors, auth, middleware
    db/                     # async engine, sessions, health checks
    contracts/v1/           # Frozen Pydantic seam contracts
    services/               # AlertCandidate adapter (Phase 2); stubs for Phase 3+
    api/                    # /health + versioned stub routers
    scripts/generate_openapi.py
  migrations/               # Phase 1 SQL chain + run_migrations.py
  seeds/reference_seed.sql
  tests/
    contracts/              # Contract fixture validation
    app/                    # Health + auth boundary tests
    (schema tests)          # Phase 1 constraints, RLS, views
  Makefile  .env.example  requirements.txt  pytest.ini
```

## Configuration

Copy `backend/.env.example` to `backend/.env`. Required:

- `DIRECT_DATABASE_URL` (preferred) or `DATABASE_URL`
- Phase 2 app vars: `LOG_LEVEL`, `CORS_ORIGINS`, `DEMO_AUTH_ENABLED`, etc.

Never commit secrets. `SUPABASE_SERVICE_ROLE_KEY` must not reach the frontend.

**Local Postgres example:**

```
DIRECT_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/liquidity_platform
```

Start local DB: `make db-up` (docker-compose on port 5433).

## Commands

Prerequisite: `pip install -r requirements.txt`

| Purpose | `make` | Direct command |
|---|---|---|
| Apply migrations | `make migrate` | `python migrations/run_migrations.py apply` |
| Apply seeds | `make seed` | `python migrations/run_migrations.py seed` |
| Run schema tests | `make verify` | `python migrations/run_migrations.py verify` |
| Run all tests | `make test` | `pytest tests -q` |
| Contract tests only | `make test-contracts` | `pytest tests/contracts -q` |
| Run API server | `make server` | `uvicorn app.main:app --reload` |
| Generate OpenAPI | `make openapi` | `python -m app.scripts.generate_openapi` |
| DB status | `make status` | `python migrations/run_migrations.py status` |

Fresh setup: `make db-up && make migrate && make seed && make server`

## Phase 2 deliverables

- `GET /health` — liveness + database readiness (no confidential data)
- Versioned `/api/v1/*` stub routes — contract placeholders returning `501`; confidential routes require `Authorization: Bearer demo:<user_uuid>`
- Frozen v1 contracts in `app/contracts/v1/` with positive/negative fixture tests
- `envelope_to_alert_candidate()` adapter in `app/services/alert_candidate_adapter.py`
- OpenAPI baseline at `docs/openapi/openapi.v1.json`

Demo auth tokens map to seeded users in `seeds/reference_seed.sql`, e.g.:

```
Authorization: Bearer demo:d0000000-0000-0000-0000-000000000a01
```

## RLS context (for Phase 5+)

Policies resolve the caller via `app.current_user_id()` — see Phase 1 README section and migration `006`.

## Safety

No financial-action endpoints. Anomaly language is advisory only ("unusual", "requires review"). Provider reserves are never blended with shared cash.
