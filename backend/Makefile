# Phase 1 schema + Phase 2 application commands.
# On Windows/Git Bash without `make`, run the underlying commands directly.
#
# PY defaults to the repo virtualenv interpreter; override with `make PY=python server`.
PY ?= ./venv/Scripts/python.exe
RUNNER := migrations/run_migrations.py
API_HOST ?= 0.0.0.0
API_PORT ?= 8000

.PHONY: migrate reset seed verify dump status db-up help server test test-contracts openapi

help:
	@echo "Targets: migrate | seed | verify | dump | status | reset | db-up"
	@echo "          server | test | test-contracts | openapi"
	@echo "Connections come from backend/.env (copy backend/.env.example)."

migrate:            ## Apply pending migrations (idempotent, checksum-tracked)
	$(PY) $(RUNNER) apply

reset:              ## Drop & recreate schema (APP_ENV=development/local/test only)
	$(PY) $(RUNNER) reset

seed:               ## Apply deterministic reference/demo seeds (idempotent)
	$(PY) $(RUNNER) seed

verify:             ## Run the pytest schema / RLS / view suite
	$(PY) $(RUNNER) verify

dump:               ## Write a schema-only snapshot to docs/verification/schema.sql
	$(PY) $(RUNNER) dump

status:             ## Show applied vs pending migrations
	$(PY) $(RUNNER) status

db-up:              ## Start the local dev Postgres (docker-compose, port 5433)
	docker compose up -d postgres

server:             ## Run the FastAPI application (reload)
	$(PY) -m uvicorn app.main:app --host $(API_HOST) --port $(API_PORT) --reload

test:               ## Run all backend tests (schema + contracts + app)
	$(PY) -m pytest tests -q

test-contracts:     ## Run contract validation tests only
	$(PY) -m pytest tests/contracts -q

openapi:            ## Generate docs/openapi/openapi.v1.json from registered routes
	$(PY) -m app.scripts.generate_openapi
