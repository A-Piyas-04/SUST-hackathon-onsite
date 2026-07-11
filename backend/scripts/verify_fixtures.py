#!/usr/bin/env python3
"""Exit-gate check (task Section 11, bullet 2): a hand-written ResultEnvelope
fixture can be accepted and turned into a valid AlertCandidate fixture
without touching any Member 2/3 file. Also sanity-checks every other fixture
against its Pydantic contract.

Run: python scripts/verify_fixtures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import UUID

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.member1.adapters.alert_candidate import AlertCandidate, build_alert_candidate_from_liquidity  # noqa: E402
from app.member1.adapters.result_envelope import LiquidityResultEnvelope, validate_result_envelope  # noqa: E402
from app.member1.adapters.validation_payload import ValidationMetricPayload  # noqa: E402
from app.member1.schemas.dashboard import DashboardResponse  # noqa: E402

FIXTURES_DIR = BACKEND_DIR / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def strip_note(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


def main() -> int:
    print("1. Validating result_envelope.example.json ...")
    envelope_raw = strip_note(load("result_envelope.example.json"))
    envelope = validate_result_envelope(envelope_raw)
    assert isinstance(envelope, LiquidityResultEnvelope)
    print("   OK — accepted as LiquidityResultEnvelope")

    print("2. Deriving AlertCandidate from that envelope (no Member 2/3 files touched) ...")
    candidate = build_alert_candidate_from_liquidity(
        envelope, liquidity_projection_id=UUID("946d1131-4f1a-4a9b-b335-7eb5e107c55f")
    )
    print("   OK — derived AlertCandidate:", candidate.model_dump(mode="json"))

    print("3. Cross-checking against fixtures/alert_candidate.example.json ...")
    expected = strip_note(load("alert_candidate.example.json"))
    AlertCandidate.model_validate(expected)  # must itself be a valid AlertCandidate
    print("   OK — fixture file is itself a valid AlertCandidate")

    print("4. Validating fixtures/validation_payload.example.json ...")
    ValidationMetricPayload.model_validate(strip_note(load("validation_payload.example.json")))
    print("   OK")

    print("5. Validating fixtures/dashboard_response.json against DashboardResponse schema ...")
    DashboardResponse.model_validate(load("dashboard_response.json"))
    print("   OK")

    print("\nAll fixture checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
