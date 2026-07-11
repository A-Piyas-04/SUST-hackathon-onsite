"""Evidence artifact writers (docs/evidence/*.json).

Artifacts are generated from persisted validation results — never hand-edited —
so displayed numbers always trace back to the recorded release-candidate build.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.contracts.v1.validation import ValidationMetricPayload
from app.services.validation import config as vcfg

_PERF_RELIABILITY = {"performance", "reliability"}


def evidence_dir() -> Path:
    path = vcfg._repo_root() / "docs" / "evidence"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _dump(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def write_validation_summary(payload: ValidationMetricPayload) -> Path:
    data = payload.model_dump(mode="json")
    data["release_candidate"] = payload.configuration.get("release_candidate")
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    return _dump(evidence_dir() / "validation-summary.json", data)


def write_performance_reliability(payload: ValidationMetricPayload) -> Path:
    rows = [
        m.model_dump(mode="json")
        for m in payload.metrics
        if m.category.value in _PERF_RELIABILITY
    ]
    data = {
        "validation_run_id": str(payload.validation_run_id),
        "release_candidate": payload.configuration.get("release_candidate"),
        "measurements": rows,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return _dump(evidence_dir() / "performance-reliability.json", data)


def write_all(payload: ValidationMetricPayload) -> list[Path]:
    return [write_validation_summary(payload), write_performance_reliability(payload)]
