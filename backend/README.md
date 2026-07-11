# Backend

FastAPI modular monolith for ingestion, separated ledger reads, data quality, liquidity forecasting, unusual-activity analysis, alerts, provider-aware cases, notifications, audit, and validation.

Project-wide setup and demo instructions are in the [root README](../README.md). Database invariants are defined in [docs/schema.md](../docs/schema.md); the generated HTTP contract is [docs/openapi/openapi.v1.json](../docs/openapi/openapi.v1.json).

## Setup

With the repository Python environment active:

```powershell
Copy-Item .env.example .env
pip install -r requirements.txt
python migrations\run_migrations.py status
python migrations\run_migrations.py apply
python migrations\run_migrations.py seed
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Configure `DIRECT_DATABASE_URL` or `DATABASE_URL` in `.env`. Never expose database passwords or `SUPABASE_SERVICE_ROLE_KEY` to the frontend.

## Verification and generated artifacts

```powershell
python -m pytest tests -q
python -m app.scripts.validate_moderate_dataset
python -m app.scripts.safety_scan
python -m app.scripts.generate_openapi
python -m app.scripts.audit_database
```

The moderate-data loader defaults to a rolled-back dry run:

```powershell
python -m app.scripts.generate_moderate_dataset
python -m app.scripts.validate_moderate_dataset
python -m app.scripts.load_moderate_dataset
```

Commit it only to an explicitly development-classified database with `--apply --confirm-development`.

## Safety boundary

The backend uses synthetic data and advisory output only. It has no transfer, settlement, refill, reversal, blocking, freezing, accusation, or final fraud-decision endpoint.
