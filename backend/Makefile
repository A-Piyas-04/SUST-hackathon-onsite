# Phase 1 schema commands. On Windows/Git Bash without `make`, run the underlying
# `python migrations/run_migrations.py <cmd>` directly (see backend/README.md).
#
# PY defaults to the repo virtualenv interpreter; override with `make PY=python migrate`.
PY ?= ./venv/Scripts/python.exe
RUNNER := migrations/run_migrations.py

.PHONY: migrate reset seed verify dump status db-up help

help:
	@echo "Targets: migrate | seed | verify | dump | status | reset | db-up"
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
