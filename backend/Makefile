# Phase 1 schema + Phase 2 application commands.
# On Windows/Git Bash without `make`, run the underlying commands directly.
#
# PY defaults to the repo virtualenv interpreter; override with `make PY=python server`.
PY ?= ./venv/Scripts/python.exe
RUNNER := migrations/run_migrations.py
API_HOST ?= 0.0.0.0
API_PORT ?= 8000

.PHONY: migrate reset seed verify dump status db-up help server test test-contracts openapi
.PHONY: sim-run sim-status sim-reset sim-fault-add sim-fault-toggle sim-demo bootstrap-demo
.PHONY: validate safety-scan

SCENARIO ?= normal
SEED ?=
OUTLET_ID ?= 0b000000-0000-0000-0000-000000000001
RUN_ID ?=
FAULT_ID ?=
FAULT_TYPE ?= conflicting_balance
PROVIDER ?= nagad

help:
	@echo "Targets: migrate | seed | verify | dump | status | reset | db-up"
	@echo "          server | test | test-contracts | openapi"
	@echo "          sim-run | sim-status | sim-reset | sim-fault-add | sim-fault-toggle | sim-demo | bootstrap-demo"
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

validate:           ## Run held-out validation harness; persist metrics + write docs/evidence/*
	$(PY) -m app.scripts.validation_cli run

safety-scan:        ## Run secrets/unsafe-endpoint/prohibited-language scans; write evidence
	$(PY) -m app.scripts.safety_scan

sim-run:            ## Start deterministic simulation run (SCENARIO, SEED, OUTLET_ID)
	$(PY) -m app.scripts.simulation_cli run --scenario $(SCENARIO) $(if $(SEED),--seed $(SEED),) --outlet-id $(OUTLET_ID)

sim-status:         ## Get simulation run status (RUN_ID required)
	$(PY) -m app.scripts.simulation_cli status --run-id $(RUN_ID)

sim-reset:          ## Reset and re-run simulation (RUN_ID required)
	$(PY) -m app.scripts.simulation_cli reset --run-id $(RUN_ID)

sim-fault-add:      ## Add fault to run (RUN_ID, FAULT_TYPE, PROVIDER)
	$(PY) -m app.scripts.simulation_cli fault add --run-id $(RUN_ID) --type $(FAULT_TYPE) --provider $(PROVIDER)

sim-fault-toggle:   ## Toggle fault (RUN_ID, FAULT_ID, ENABLED=true|false)
	$(PY) -m app.scripts.simulation_cli fault toggle --run-id $(RUN_ID) --fault-id $(FAULT_ID) --enabled $(ENABLED)

sim-demo:           ## Full demo workflow: migrate, seed, bootstrap dashboard data
	$(MAKE) migrate seed bootstrap-demo

bootstrap-demo:     ## Run normal scenario + liquidity analytics (idempotent)
	$(PY) -m app.scripts.bootstrap_demo --outlet-id $(OUTLET_ID)
