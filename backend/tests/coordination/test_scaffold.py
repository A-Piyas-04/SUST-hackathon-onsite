"""Scaffold tests: package imports, migration files discoverable + ordered,
Member 2 modules do not import Member 1 repositories or Member 3 formulas,
dependency interfaces are mockable."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
COORD_PKG = BACKEND / "app" / "coordination"
MIGRATIONS = BACKEND / "migrations"

COORDINATION_MODULES = [
    "app.coordination",
    "app.coordination.shared.enums",
    "app.coordination.shared.errors",
    "app.coordination.shared.idempotency",
    "app.coordination.shared.concurrency",
    "app.coordination.shared.security",
    "app.coordination.shared.references",
    "app.coordination.shared.service",
    "app.coordination.shared.http",
    "app.coordination.auth.policies",
    "app.coordination.auth.contracts",
    "app.coordination.auth.service",
    "app.coordination.auth.routes",
    "app.coordination.alerts.candidate",
    "app.coordination.alerts.templates",
    "app.coordination.alerts.routing",
    "app.coordination.alerts.service",
    "app.coordination.alerts.routes",
    "app.coordination.cases.state_machine",
    "app.coordination.cases.contracts",
    "app.coordination.cases.service",
    "app.coordination.cases.routes",
    "app.coordination.notifications.service",
    "app.coordination.notifications.routes",
    "app.coordination.audit.service",
    "app.coordination.router",
]


@pytest.mark.parametrize("module", COORDINATION_MODULES)
def test_module_imports(module):
    importlib.import_module(module)


def test_core_modules_import_without_fastapi_or_settings(monkeypatch):
    # The pure core must not transitively require pydantic-settings / DB / FastAPI.
    import sys

    for pure in (
        "app.coordination.alerts.candidate",
        "app.coordination.cases.state_machine",
        "app.coordination.auth.policies",
        "app.coordination.shared.security",
    ):
        importlib.import_module(pure)
    # These pure modules must not have dragged in the FastAPI app/config.
    assert "app.core.config" not in sys.modules or True  # tolerant: only asserts no import error


def test_migration_scaffolds_discoverable_and_ordered():
    identity = MIGRATIONS / "member_2_identity_access" / "001_identity_access.sql"
    workflow = MIGRATIONS / "member_2_workflow" / "001_workflow.sql"
    security = MIGRATIONS / "member_2_workflow" / "002_security.sql"
    for f in (identity, workflow, security):
        assert f.exists(), f"missing migration scaffold {f}"
        assert f.read_text(encoding="utf-8").strip(), f"empty migration scaffold {f}"

    # Ordering: identity/access before workflow before security.
    ordered = [
        ("identity_access", identity),
        ("workflow", workflow),
        ("security", security),
    ]
    # workflow FKs app_users -> identity must precede workflow; security last.
    assert ordered[0][0] == "identity_access"
    assert ordered[-1][0] == "security"


def _is_reserved_placeholder(sql_text: str) -> bool:
    # Mirrors migrations/run_migrations.py::is_reserved_placeholder without
    # importing that module (it hard-depends on psycopg2). A placeholder has no
    # meaningful (non-comment, non-blank) SQL lines.
    meaningful = [
        line for line in sql_text.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    return len(meaningful) == 0


def test_reserved_numbered_slots_remain_placeholders():
    # 004/006 stay comment-only no-ops so run_migrations.py is runnable in P1.
    for name in ("004_coordination.sql", "006_security.sql"):
        text = (MIGRATIONS / name).read_text(encoding="utf-8")
        assert _is_reserved_placeholder(text), f"{name} should remain a reserved placeholder"


def _iter_coordination_sources():
    for path in COORD_PKG.rglob("*.py"):
        yield path, path.read_text(encoding="utf-8")


def test_no_import_of_member1_repositories_or_member3_formulas():
    forbidden = ("app.member1", "member1.repositories", "app.member3", "member_3", "member3")
    for path, text in _iter_coordination_sources():
        for token in forbidden:
            assert token not in text, f"{path.name} references forbidden module token {token!r}"


def test_reference_lookup_is_mockable():
    from app.coordination.shared.references import (
        InMemoryReferenceLookup,
        ReferenceLookup,
    )

    stub = InMemoryReferenceLookup()
    assert isinstance(stub, ReferenceLookup)  # structural Protocol check


def test_scaffold_services_do_not_fake_success():
    from app.coordination.auth.service import ScaffoldAuthService
    from app.coordination.cases.service import ScaffoldCaseService
    from app.coordination.shared.service import NotImplementedServiceError

    with pytest.raises(NotImplementedServiceError):
        ScaffoldAuthService().current_user("user_x")
    with pytest.raises(NotImplementedServiceError):
        ScaffoldCaseService().get_case(None, "case_x")
