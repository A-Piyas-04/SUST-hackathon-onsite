"""Security tests: safe-language scan, identical missing/forbidden 404 shape,
no confidential leak in errors, synthetic-only fixtures, no financial-action or
generic status-patch endpoints."""
from __future__ import annotations

import json
from pathlib import Path

from app.coordination.shared.errors import not_found, scan_for_leaks, validate_error_shape
from app.coordination.shared.security import (
    is_safe_workflow_text,
    looks_like_phone_number,
    scan_workflow_text,
)

FRAUD_AND_ACTION = [
    "Confirmed fraud by the agent.",
    "This agent is a fraudster.",
    "Block the account immediately.",
    "Freeze the funds now.",
    "Transfer funds to the reserve.",
    "Refill the wallet.",
    "Reverse the transaction.",
    "Suspend the customer.",
]

SAFE_ADVISORY = [
    "Unusual activity requires review.",
    "Possible liquidity pressure; human review recommended.",
    "This is not proof of fraud.",
    "The platform does not block accounts or freeze funds.",
    "Estimated shortage within two hours; the data source should be checked.",
    "Potential inconsistency in the feed.",
]


def test_prohibited_language_flagged():
    for text in FRAUD_AND_ACTION:
        assert scan_workflow_text(text), f"should flag: {text!r}"


def test_safe_advisory_language_passes():
    for text in SAFE_ADVISORY:
        assert is_safe_workflow_text(text), f"should pass: {text!r}"


def test_missing_and_forbidden_have_identical_public_shape():
    missing = not_found(request_id="req_a").to_response()["error"]
    forbidden = not_found(request_id="req_b").to_response()["error"]
    # Everything except request_id must be byte-identical.
    missing_wo = {k: v for k, v in missing.items() if k != "request_id"}
    forbidden_wo = {k: v for k, v in forbidden.items() if k != "request_id"}
    assert missing_wo == forbidden_wo
    assert missing["code"] == "NOT_FOUND"
    assert missing["details"] == {}


def test_fixture_error_bodies_are_safe_and_identical_shape(fixtures_dir: Path):
    data = json.loads((fixtures_dir / "errors" / "safe_errors.json").read_text(encoding="utf-8"))
    a = data["not_found_missing"]["error"]
    b = data["not_found_cross_provider"]["error"]
    assert {k: v for k, v in a.items() if k != "request_id"} == {k: v for k, v in b.items() if k != "request_id"}
    for key, body in data.items():
        if key.startswith("_"):
            continue
        validate_error_shape(body)


def test_no_leaks_in_error_details():
    assert scan_for_leaks("password: hunter2")
    assert scan_for_leaks("Authorization: Bearer eyJx.y.z")
    assert not scan_for_leaks("expected_version 4")


def test_fixtures_contain_no_phone_like_or_secret_strings(fixtures_dir: Path):
    # Scan only real string VALUES (skip `_`-prefixed documentation/meta keys so
    # a comment that *names* the forbidden concepts is not a false positive).
    secret_markers = ("passwd", "pin:", "otp:", "bearer ", "private_key", "eyj")

    def walk(v, path):
        if isinstance(v, str):
            low = v.lower()
            for marker in secret_markers:
                assert marker not in low, f"{path.name} value contains secret marker {marker!r}: {v!r}"
            assert not looks_like_phone_number(v), f"{path.name} has phone-like value {v!r}"
        elif isinstance(v, dict):
            for k, x in v.items():
                if str(k).startswith("_"):
                    continue
                walk(x, path)
        elif isinstance(v, list):
            for x in v:
                walk(x, path)

    for path in fixtures_dir.rglob("*.json"):
        walk(json.loads(path.read_text(encoding="utf-8")), path)


def _member2_openapi_paths():
    from fastapi import FastAPI

    from app.coordination.router import include_member2_routers

    app = FastAPI()
    include_member2_routers(app)
    return app.openapi()["paths"]


def test_no_generic_status_patch_endpoint():
    paths = _member2_openapi_paths()
    for path, ops in paths.items():
        assert not (path.endswith("/status") and "patch" in ops), f"generic status patch found: {path}"


def test_no_financial_action_endpoints():
    paths = _member2_openapi_paths()
    forbidden = ("transfer", "convert", "settle", "refill", "recover", "reverse",
                 "block", "freeze", "accuse", "fraud", "seize", "suspend")
    for path in paths:
        assert not any(word in path.lower() for word in forbidden), f"forbidden endpoint: {path}"


def test_review_route_cannot_carry_fraud_verdict():
    # Structural: ReviewOutcome enum has no fraud value, so a fraud verdict is
    # unrepresentable in the review contract.
    from app.coordination.shared.enums import ReviewOutcome

    assert "fraud" not in {v.value for v in ReviewOutcome}
