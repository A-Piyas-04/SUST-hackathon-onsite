"""Shared fixtures for Member 2 (P1-M2) tests.

Loads the synthetic reference world + candidate fixtures from
`backend/fixtures/coordination/` and builds a dependency-free
`InMemoryReferenceLookup` so candidate/scope tests run without a database.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.coordination.shared.references import (
    AccountRef,
    InMemoryReferenceLookup,
    OutletRef,
    ProviderRef,
    SourceResultRef,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "coordination"


def load_json(*parts: str) -> dict:
    with (FIXTURES_DIR.joinpath(*parts)).open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def references() -> dict:
    return load_json("references.json")


@pytest.fixture(scope="session")
def lookup(references: dict) -> InMemoryReferenceLookup:
    providers = {
        k: ProviderRef(v["provider_id"], v["code"], v["is_active"])
        for k, v in references["providers"].items()
    }
    outlets = {
        k: OutletRef(v["outlet_id"], v["area_id"], v["is_active"])
        for k, v in references["outlets"].items()
    }
    accounts = {
        k: AccountRef(v["outlet_provider_account_id"], v["outlet_id"], v["provider_id"], v["is_active"])
        for k, v in references["accounts"].items()
    }
    sources = {
        k: SourceResultRef(
            v["source_result_id"], v["result_type"], v["outlet_id"], v["provider_id"],
            v["is_alertable"], v.get("is_suppressed", False),
        )
        for k, v in references["sources"].items()
    }
    return InMemoryReferenceLookup(providers, outlets, accounts, sources)


def _load_dir(subdir: str) -> dict[str, dict]:
    base = FIXTURES_DIR.joinpath(*subdir.split("/"))
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(base.glob("*.json"))}


@pytest.fixture(scope="session")
def valid_candidates() -> dict[str, dict]:
    return _load_dir("candidates/valid")


@pytest.fixture(scope="session")
def invalid_candidates() -> dict[str, dict]:
    return _load_dir("candidates/invalid")
