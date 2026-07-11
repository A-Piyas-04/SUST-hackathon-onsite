"""Anomaly Detection Engine (Phase 3, Member 3) -- near_identical_amounts rule.

Detects clusters of near-identical repeated amounts (within +/-2%,
configurable) coming from a small number of distinct accounts within a
short time window, for a single provider. This is the only anomaly
pattern active in this phase (docs/schema.md §9.7: "MVP activates only
`near_identical_amounts`").

Safe-language rule: every string this module can emit uses only
"unusual", "requires review", "possible", or "estimated" register --
never a fraud determination, and never words like "fraud", "blocked",
or "frozen".

Pure function, no HTTP/DB/UI code. Returns a list of ResultEnvelope (see
analytics/result_envelope.py) -- zero, one, or many per scan, since a
single provider/window can contain more than one distinct amount cluster.
"""

from __future__ import annotations

import dataclasses
import statistics
from datetime import datetime

from backend.analytics.confidence import clamp, combine_confidence
from backend.analytics.fixtures.stub_types import (
    TRANSACTION_STATUS_COMPLETED,
    TRANSACTION_TYPE_CASH_OUT,
    QualityAssessment,
    Transaction,
)
from backend.analytics.result_envelope import (
    AnomalyResult,
    ResultEnvelope,
    confidence_level_for,
)

ANOMALY_ENGINE_VERSION = "1.0.0"

ANOMALY_PATTERN_NEAR_IDENTICAL_AMOUNTS = "near_identical_amounts"

DISPOSITION_REQUIRES_REVIEW = "requires_review"
DISPOSITION_INCONCLUSIVE = "inconclusive"

# Distinct from `disposition`: a stable placeholder field so downstream
# consumers can wire in real quality-driven suppression later (Phase 4)
# without a breaking contract change. Only NOT_SUPPRESSED is ever
# produced by this phase's engine.
SUPPRESSION_NOT_SUPPRESSED = "NOT_SUPPRESSED"
SUPPRESSION_SUPPRESSED_PENDING_REVIEW = "SUPPRESSED_PENDING_REVIEW"  # reserved, unused this phase

_INCONCLUSIVE_CONFIDENCE_THRESHOLD = 0.15

# A round-number amount is treated as a weak signal on its own (round
# amounts are common demand-driven behavior, e.g. even cash-out amounts).
_ROUND_NUMBER_UNIT = 100.0
_ROUND_NUMBER_EPSILON = 0.01

_BENIGN_EXPLANATION = (
    "This pattern may reflect normal, event-driven demand (for example, "
    "seasonal or Eid-season cash-out demand) rather than an issue requiring escalation."
)


def _is_round_number(amount: float) -> bool:
    remainder = amount % _ROUND_NUMBER_UNIT
    return remainder < _ROUND_NUMBER_EPSILON or (_ROUND_NUMBER_UNIT - remainder) < _ROUND_NUMBER_EPSILON


def _filter_candidates(
    transactions: list[Transaction],
    *,
    provider_code: str,
    window_start: datetime,
    window_end: datetime,
) -> list[Transaction]:
    if any(t.provider_code != provider_code for t in transactions):
        raise ValueError(
            "detect_near_identical_amounts received transactions from more than one "
            "provider; the Anomaly Detection Engine never compares or combines "
            "transactions across providers. Split input by provider before calling."
        )
    return [
        t
        for t in transactions
        if t.status == TRANSACTION_STATUS_COMPLETED
        and t.transaction_type == TRANSACTION_TYPE_CASH_OUT
        and window_start <= t.occurred_at <= window_end
    ]


def _cluster_by_amount(transactions: list[Transaction], tolerance_pct: float) -> list[list[Transaction]]:
    """Greedily group transactions whose amount is within tolerance_pct of
    the running median of the cluster they'd join.

    Sorting by amount first (rather than relying on caller insertion
    order) makes clustering deterministic and avoids two failure modes of
    simpler approaches: anchoring to a "first-seen" amount lets slow
    drift accumulate outside the true +/-tolerance band relative to later
    members, and naive pairwise comparison is O(n^2) and ill-defined for
    clusters larger than two.
    """
    ordered = sorted(transactions, key=lambda t: t.amount)
    clusters: list[list[Transaction]] = []
    current: list[Transaction] = []

    for txn in ordered:
        if not current:
            current = [txn]
            continue
        running_median = statistics.median(t.amount for t in current)
        lower = running_median * (1 - tolerance_pct)
        upper = running_median * (1 + tolerance_pct)
        if lower <= txn.amount <= upper:
            current.append(txn)
        else:
            clusters.append(current)
            current = [txn]
    if current:
        clusters.append(current)
    return clusters


def _cluster_confidence(
    cluster: list[Transaction],
    *,
    max_distinct_accounts: int,
    min_cluster_size: int,
    quality: QualityAssessment,
) -> float:
    distinct_accounts = len({t.synthetic_party_ref for t in cluster})
    account_concentration = clamp(1.0 - (distinct_accounts - 1) / max_distinct_accounts)

    round_ratio = sum(1 for t in cluster if _is_round_number(t.amount)) / len(cluster)
    round_number_component = clamp(1.0 - round_ratio)

    cluster_density = clamp(len(cluster) / min_cluster_size)

    base = combine_confidence(
        account_concentration, round_number_component, quality.confidence_modifier
    )
    return clamp(base * (0.5 + 0.5 * cluster_density))


def detect_near_identical_amounts(
    transactions: list[Transaction],
    quality: QualityAssessment,
    *,
    provider_code: str,
    outlet_id: str,
    window_start: datetime,
    window_end: datetime,
    tolerance_pct: float = 0.02,
    max_distinct_accounts: int = 5,
    min_cluster_size: int = 3,
    engine_version: str = ANOMALY_ENGINE_VERSION,
) -> list[ResultEnvelope]:
    """Scan one provider's transactions for near-identical amount clusters.

    Raises ValueError if `transactions` mixes more than one provider --
    provider isolation is enforced, not merely documented.
    """
    candidates = _filter_candidates(
        transactions,
        provider_code=provider_code,
        window_start=window_start,
        window_end=window_end,
    )
    clusters = _cluster_by_amount(candidates, tolerance_pct)

    envelopes: list[ResultEnvelope] = []
    for cluster in clusters:
        distinct_accounts = len({t.synthetic_party_ref for t in cluster})
        if len(cluster) < min_cluster_size or distinct_accounts > max_distinct_accounts:
            continue

        confidence = _cluster_confidence(
            cluster,
            max_distinct_accounts=max_distinct_accounts,
            min_cluster_size=min_cluster_size,
            quality=quality,
        )
        confidence_level = confidence_level_for(confidence, sample_count=len(cluster))
        disposition = (
            DISPOSITION_INCONCLUSIVE
            if confidence < _INCONCLUSIVE_CONFIDENCE_THRESHOLD
            else DISPOSITION_REQUIRES_REVIEW
        )

        amounts = [t.amount for t in cluster]
        median_amount = statistics.median(amounts)
        account_refs = tuple(sorted({t.synthetic_party_ref for t in cluster}))

        evidence_summary = (
            f"{len(cluster)} cash-outs of approximately {median_amount:.2f} occurred "
            f"from {distinct_accounts} distinct account(s) between "
            f"{window_start.isoformat()} and {window_end.isoformat()}; this is unusual "
            "and may warrant review."
        )

        evidence = (
            {
                "evidence_type": "count",
                "label": "Transactions in cluster",
                "value": len(cluster),
                "display_order": 0,
            },
            {
                "evidence_type": "amount_cluster",
                "label": "Amount range",
                "value": {"min": min(amounts), "max": max(amounts), "median": median_amount},
                "display_order": 1,
            },
            {
                "evidence_type": "account_cluster",
                "label": "Distinct accounts involved",
                "value": list(account_refs),
                "display_order": 2,
            },
            {
                "evidence_type": "time_window",
                "label": "Detection window",
                "value": {"start": window_start.isoformat(), "end": window_end.isoformat()},
                "display_order": 3,
            },
            *(
                {
                    "evidence_type": "transaction",
                    "label": "Contributing transaction",
                    "value": {
                        "transaction_id": t.transaction_id,
                        "amount": t.amount,
                        "synthetic_party_ref": t.synthetic_party_ref,
                        "occurred_at": t.occurred_at.isoformat(),
                    },
                    "display_order": 4 + i,
                }
                for i, t in enumerate(cluster)
            ),
        )

        engine_specific = AnomalyResult(
            pattern=ANOMALY_PATTERN_NEAR_IDENTICAL_AMOUNTS,
            provider_code=provider_code,
            window_start=window_start,
            window_end=window_end,
            disposition=disposition,
            reason_code="near_identical_amounts_cluster",
            evidence_summary=evidence_summary,
            plausible_benign_explanation=_BENIGN_EXPLANATION,
            suppression_disposition=SUPPRESSION_NOT_SUPPRESSED,
            account_refs=account_refs,
        )

        envelopes.append(
            ResultEnvelope(
                engine="anomaly",
                engine_version=engine_version,
                input_window_start=window_start,
                input_window_end=window_end,
                quality_assessment_ids=(quality.data_quality_assessment_id,),
                confidence=confidence,
                confidence_level=confidence_level,
                evidence=evidence,
                generated_at=window_end,
                engine_specific=dataclasses.asdict(engine_specific),
            )
        )

    return envelopes
