"""Ground-truth labels derived from known held-out scenario expectations.

Expectations come directly from ``reference_seed.sql`` default_config and the
frozen Phase 6 E2E assertions (``tests/phase6/test_e2e_scenarios.py``). They are
frozen *before* measurement — the harness never tunes against detector output.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.contracts.v1.enums import ProviderCode, ScenarioCode
from app.services.constants import PROVIDER_IDS


@dataclass(frozen=True)
class GroundTruthLabel:
    label_type: str  # shortage | anomaly | normal | data_quality_incident
    outlet_id: UUID
    provider_id: UUID | None
    expected_value: dict
    window_start: datetime
    window_end: datetime


def build_labels(
    *,
    scenario_code: ScenarioCode,
    outlet_id: UUID,
    window_start: datetime,
    window_end: datetime,
) -> list[GroundTruthLabel]:
    """Return the frozen ground-truth labels for one held-out scenario run."""
    bkash = PROVIDER_IDS[ProviderCode.BKASH]
    nagad = PROVIDER_IDS[ProviderCode.NAGAD]
    rocket = PROVIDER_IDS[ProviderCode.ROCKET]

    def normal(provider_id: UUID) -> GroundTruthLabel:
        return GroundTruthLabel(
            label_type="normal",
            outlet_id=outlet_id,
            provider_id=provider_id,
            expected_value={"anomaly": False, "alertable_anomaly": False},
            window_start=window_start,
            window_end=window_end,
        )

    if scenario_code is ScenarioCode.SCENARIO_A:
        # Shared physical cash faces a shortage; provider e-money must not falsely
        # deplete. No anomaly clusters — all providers are anomaly-negative.
        return [
            GroundTruthLabel(
                label_type="shortage",
                outlet_id=outlet_id,
                provider_id=None,  # shared cash carries no provider_id
                expected_value={"reserve_type": "shared_cash", "shortage": True},
                window_start=window_start,
                window_end=window_end,
            ),
            normal(bkash),
            normal(nagad),
            normal(rocket),
        ]

    if scenario_code is ScenarioCode.SCENARIO_B:
        # Near-identical amount cluster on bkash → alertable anomaly expected.
        return [
            GroundTruthLabel(
                label_type="anomaly",
                outlet_id=outlet_id,
                provider_id=bkash,
                expected_value={
                    "pattern": "near_identical_amounts",
                    "alertable_anomaly": True,
                    "cluster_amount": "1000.00",
                    "cluster_count": 6,
                },
                window_start=window_start,
                window_end=window_end,
            ),
            normal(nagad),
            normal(rocket),
        ]

    if scenario_code is ScenarioCode.SCENARIO_C:
        # Same cluster but degraded/conflicting feed → data-quality incident on
        # bkash; the anomaly must be SUPPRESSED (non-alertable), never a false alert.
        return [
            GroundTruthLabel(
                label_type="data_quality_incident",
                outlet_id=outlet_id,
                provider_id=bkash,
                expected_value={
                    "incident": True,
                    "anomaly_present": True,
                    "alertable_anomaly": False,  # must be suppressed
                },
                window_start=window_start,
                window_end=window_end,
            ),
            normal(nagad),
            normal(rocket),
        ]

    return []
