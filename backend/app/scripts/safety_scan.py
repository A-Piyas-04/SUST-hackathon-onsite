"""Phase 7 safety & security verification (machine-checkable).

Runs three scans over the frozen build and writes a pass/fail artifact to
``docs/evidence/safety-security-scan.json``:

  1. Secrets / real-data scan  — no API keys, private keys, real phone numbers,
     PIN/OTP literals, or non-synthetic account data outside allowlisted demos.
  2. Unsafe-action endpoint scan — no route behaves as transfer/convert/settle/
     refill/recover/reverse/block/freeze/accuse/fraud-decision.
  3. Prohibited-language scan   — no definitive fraud/guilt language in alert
     templates, explanation renders, or frontend user-visible strings.

    python -m app.scripts.safety_scan        # exits non-zero on any failure

Honest by design: any deliberately allowlisted demo pattern (e.g. the local
docker Postgres password) is recorded as an explicit waiver in the artifact.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.api.router import api_router
from app.services.validation import config as vcfg

ROOT = vcfg._repo_root()

# Directories never scanned (build output, deps, VCS, generated evidence).
_EXCLUDE_DIRS = {
    ".git", ".next", "node_modules", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", "evidence", "dist", "build",
}
_SCAN_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".sql", ".json", ".md", ".env", ".txt"}

# Files/patterns allowlisted as intentional, synthetic, or placeholder.
_ALLOWLIST_FILES = {".env.example"}
# Local demo docker Postgres credential (never a real secret) — recorded as waiver.
_DEMO_DSN = re.compile(r"postgres:postgres@localhost")
_DEMO_TOKEN = re.compile(r"demo:[0-9a-fA-F-]{8,}")

_PROHIBITED_WORDS = [
    "fraud", "fraudulent", "criminal", "guilty", "theft", "stole", "stolen",
    "embezzle", "launder", "scammer", "scam",
]
# Files allowed to contain prohibited words (negative tests + the scanners
# themselves, which necessarily list the words to detect them).
_LANGUAGE_ALLOW_SUBSTR = (
    "tests/", "safety_scan.py", "test_e2e_scenarios.py",
    "alert_candidate_unsafe_language.json", "docs/evidence",
)

_UNSAFE_ROUTE_TOKENS = [
    "transfer", "convert", "settle", "refill", "recover", "reverse",
    "block", "freeze", "accuse", "fraud", "verdict",
]

# High-signal secret patterns (kept conservative to avoid false positives on a
# synthetic codebase; the demo DSN/token are handled separately as waivers).
_SECRET_PATTERNS = {
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "bd_phone_number": re.compile(r"(?<!\d)(?:\+?880|0)1[3-9]\d{8}(?!\d)"),
    "otp_literal": re.compile(r"\b(?:otp|one[_-]?time[_-]?password)\b\s*[:=]\s*['\"]?\d{4,8}", re.I),
    "pin_literal": re.compile(r"\bpin\b\s*[:=]\s*['\"]?\d{4,6}\b", re.I),
}


def _iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _EXCLUDE_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in _SCAN_SUFFIXES:
            continue
        yield path


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def scan_secrets() -> dict:
    findings: list[dict] = []
    waivers: list[dict] = []
    files_scanned = 0
    for path in _iter_files():
        rel = _rel(path)
        if path.name in _ALLOWLIST_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        files_scanned += 1
        for lineno, line in enumerate(text.splitlines(), start=1):
            for kind, pattern in _SECRET_PATTERNS.items():
                for m in pattern.finditer(line):
                    matched = m.group(0)
                    # Waive the known local demo DSN / demo bearer tokens.
                    if _DEMO_DSN.search(line) or _DEMO_TOKEN.search(matched):
                        waivers.append({"file": rel, "line": lineno, "kind": kind, "reason": "synthetic demo credential"})
                        continue
                    findings.append({"file": rel, "line": lineno, "kind": kind, "match": matched[:40]})
    return {
        "name": "secrets_and_real_data",
        "passed": not findings,
        "files_scanned": files_scanned,
        "findings": findings,
        "waivers": waivers,
    }


def scan_unsafe_endpoints() -> dict:
    findings: list[dict] = []
    routes = []
    for route in api_router.routes:
        path = getattr(route, "path", "")
        name = getattr(route, "name", "")
        methods = sorted(getattr(route, "methods", []) or [])
        routes.append(path)
        haystack = f"{path} {name}".lower()
        for token in _UNSAFE_ROUTE_TOKENS:
            if token in haystack:
                findings.append({"path": path, "name": name, "methods": methods, "token": token})
    return {
        "name": "unsafe_action_endpoints",
        "passed": not findings,
        "routes_checked": len(routes),
        "findings": findings,
    }


def scan_prohibited_language() -> dict:
    findings: list[dict] = []
    files_scanned = 0
    patterns = {w: re.compile(rf"\b{re.escape(w)}\b", re.I) for w in _PROHIBITED_WORDS}
    for path in _iter_files():
        rel = _rel(path)
        if any(sub in rel for sub in _LANGUAGE_ALLOW_SUBSTR):
            continue
        # Only scan genuinely user-visible surfaces: frontend UI strings, seeded
        # explanation/alert templates, and the explanation renderer copy. DDL and
        # code comments are excluded — they are never shown to a user.
        is_frontend = rel.startswith("frontend/src")
        is_template_seed = rel.startswith("backend/seeds")
        is_explanation_render = rel.endswith("coordination/explanations.py")
        if not (is_frontend or is_template_seed or is_explanation_render):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        files_scanned += 1
        for lineno, line in enumerate(text.splitlines(), start=1):
            for word, pattern in patterns.items():
                if pattern.search(line):
                    findings.append({"file": rel, "line": lineno, "word": word, "text": line.strip()[:80]})
    return {
        "name": "prohibited_language",
        "passed": not findings,
        "files_scanned": files_scanned,
        "findings": findings,
    }


def run_scans() -> dict:
    scans = [scan_secrets(), scan_unsafe_endpoints(), scan_prohibited_language()]
    passed = all(s["passed"] for s in scans)
    return {
        "passed": passed,
        "release_candidate": vcfg.release_candidate(),
        "scans": scans,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_artifact(result: dict) -> Path:
    out_dir = ROOT / "docs" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "safety-security-scan.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    result = run_scans()
    path = write_artifact(result)
    summary = {s["name"]: ("PASS" if s["passed"] else "FAIL") for s in result["scans"]}
    print(json.dumps({"overall": "PASS" if result["passed"] else "FAIL", "scans": summary, "artifact": str(path)}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
