"""Validation harness configuration: engine version, held-out set, release id.

All values are documented and inspectable so evidence is reproducible and tied
to an exact signed-off release-candidate build (docs/phase-7 Evidence Gate).
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from app.contracts.v1.enums import ScenarioCode
from app.core.config import get_settings
from app.services.analytics import config as analytics_cfg
from app.services.constants import DEFAULT_OUTLET_ID

# Version of the validation harness itself (persisted as validation_runs.engine_version).
VALIDATION_ENGINE_VERSION = "validation-v1"

# Default held-out run name.
VALIDATION_RUN_NAME = "held_out_mvp_eval"

# Latency measurement volume (per endpoint) for performance metrics.
LATENCY_ITERATIONS = 30


class HeldOutScenario:
    """A frozen held-out scenario used for reported metrics (never demo/tuning)."""

    def __init__(self, code: ScenarioCode, seed: int, expects_alert: bool) -> None:
        self.code = code
        self.seed = seed
        self.expects_alert = expects_alert


# Seeds mirror backend/seeds/reference_seed.sql (held_out split scenarios A/B/C).
# scenario_d and normal are the demo split and are intentionally excluded.
HELD_OUT_SCENARIOS: tuple[HeldOutScenario, ...] = (
    HeldOutScenario(ScenarioCode.SCENARIO_A, seed=2001, expects_alert=True),
    HeldOutScenario(ScenarioCode.SCENARIO_B, seed=2002, expects_alert=True),
    HeldOutScenario(ScenarioCode.SCENARIO_C, seed=2003, expects_alert=False),
)

DEFAULT_VALIDATION_OUTLET_ID: UUID = DEFAULT_OUTLET_ID


def _repo_root() -> Path:
    # backend/app/services/validation/config.py -> repo root is 4 parents up from backend/
    return Path(__file__).resolve().parents[4]


@lru_cache
def git_commit() -> str:
    """Best-effort git commit hash for the release-candidate identifier."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_repo_root()),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        commit = out.stdout.strip()
        return commit or "unknown"
    except Exception:  # noqa: BLE001 - evidence must never crash on missing git
        return "unknown"


def engine_versions() -> dict[str, str]:
    return {
        "quality": analytics_cfg.QUALITY_ENGINE_VERSION,
        "liquidity": analytics_cfg.LIQUIDITY_ENGINE_VERSION,
        "anomaly": analytics_cfg.ANOMALY_ENGINE_VERSION,
        "validation": VALIDATION_ENGINE_VERSION,
    }


def release_candidate() -> dict:
    """The signed-off release-candidate identifier embedded in every artifact."""
    settings = get_settings()
    return {
        "commit": git_commit(),
        "contract_version": settings.contract_version,
        "engine_versions": engine_versions(),
    }
