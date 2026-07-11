"""Shared helpers for contract fixture tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_fixture(name: str, *, positive: bool = True) -> dict:
    folder = "positive" if positive else "negative"
    path = FIXTURES / folder / name
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def positive_fixtures():
    return FIXTURES / "positive"
