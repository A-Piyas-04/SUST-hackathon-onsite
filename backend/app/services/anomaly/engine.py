"""Anomaly Detection Engine (pure, deterministic).

Implements the near-identical-amount repetition rule within a single
provider/outlet/time window. A flag means "unusual / requires review" and is
never a determination of wrongdoing; every actionable result carries a plausible
benign explanation. When the underlying data quality is degraded, an otherwise
detectable pattern is *suppressed* (persisted for measurement but never
alertable) rather than presented as a confident anomaly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from app.contracts.v1.enums import AnomalyDisposition, ConfidenceLevel
from app.services.analytics import config as cfg


@dataclass(frozen=True)
class TransactionRecord:
    transaction_id: Any  # UUID (kept generic so the engine stays dependency-light)
    party_ref: str
    amount: Decimal
    occurred_at: datetime


@dataclass(frozen=True)
class AnomalyRuleConfig:
    window_minutes: int = cfg.ANOMALY_DEFAULT_CONFIG["window_minutes"]
    amount_tolerance_pct: float = cfg.ANOMALY_DEFAULT_CONFIG["amount_tolerance_pct"]
    minimum_count: int = cfg.ANOMALY_DEFAULT_CONFIG["minimum_count"]
    minimum_distinct_parties: int = cfg.ANOMALY_DEFAULT_CONFIG["minimum_distinct_parties"]

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "AnomalyRuleConfig":
        raw = raw or {}
        return cls(
            window_minutes=int(raw.get("window_minutes", cls.window_minutes)),
            amount_tolerance_pct=float(raw.get("amount_tolerance_pct", cls.amount_tolerance_pct)),
            minimum_count=int(raw.get("minimum_count", cls.minimum_count)),
            minimum_distinct_parties=int(
                raw.get("minimum_distinct_parties", cls.minimum_distinct_parties)
            ),
        )


@dataclass(frozen=True)
class AnomalyInput:
    provider_code: str
    transactions: list[TransactionRecord]
    quality_status: str
    quality_modifier: Decimal
    rule_config: AnomalyRuleConfig = field(default_factory=AnomalyRuleConfig)


@dataclass(frozen=True)
class AnomalyEvidence:
    evidence_type: str
    label: str
    value: Any
    display_order: int


@dataclass(frozen=True)
class AnomalyResult:
    detected: bool
    persist: bool
    disposition: AnomalyDisposition
    reason_code: str
    confidence_score: Decimal
    confidence_level: ConfidenceLevel
    window_start: datetime | None
    window_end: datetime | None
    evidence_summary: str
    plausible_benign_explanation: str
    suppression_reason: str | None
    transaction_ids: list[Any] = field(default_factory=list)
    evidence_items: list[AnomalyEvidence] = field(default_factory=list)
    distinct_party_count: int = 0
    representative_amount: Decimal | None = None


_BENIGN = (
    "Repeated similar amounts are common during salary disbursement, festival "
    "demand, or recurring bill payments; this pattern is flagged only for human "
    "review and is not a determination of wrongdoing."
)


def _best_cluster(
    transactions: list[TransactionRecord], config: AnomalyRuleConfig
) -> list[TransactionRecord]:
    """Largest set of near-identical amounts occurring within one time window."""
    if not transactions:
        return []
    tol = Decimal(str(config.amount_tolerance_pct)) / Decimal("100")
    window = timedelta(minutes=config.window_minutes)
    by_amount = sorted(transactions, key=lambda t: t.amount)

    best: list[TransactionRecord] = []
    i = 0
    n = len(by_amount)
    while i < n:
        anchor = by_amount[i].amount
        bound = anchor * (Decimal("1") + tol)
        group = [t for t in by_amount[i:] if t.amount <= bound]
        # Within the amount group, find the largest subset within the time window.
        group_by_time = sorted(group, key=lambda t: t.occurred_at)
        lo = 0
        for hi in range(len(group_by_time)):
            while (
                group_by_time[hi].occurred_at - group_by_time[lo].occurred_at
            ) > window:
                lo += 1
            subset = group_by_time[lo : hi + 1]
            if len(subset) > len(best):
                best = list(subset)
        i += 1
    return best


def detect_near_identical_amounts(data: AnomalyInput) -> AnomalyResult:
    config = data.rule_config
    cluster = _best_cluster(data.transactions, config)
    distinct_parties = len({t.party_ref for t in cluster})
    meets_threshold = (
        len(cluster) >= config.minimum_count
        and distinct_parties >= config.minimum_distinct_parties
    )

    degraded = (
        data.quality_status in {"missing", "conflicting"}
        or data.quality_modifier <= Decimal(str(cfg.ANOMALY_SUPPRESSION_MODIFIER))
    )

    if not meets_threshold:
        return AnomalyResult(
            detected=False,
            persist=False,
            disposition=AnomalyDisposition.INCONCLUSIVE,
            reason_code="no_supported_pattern",
            confidence_score=cfg.quantize_score(Decimal("0")),
            confidence_level=ConfidenceLevel.UNAVAILABLE,
            window_start=None,
            window_end=None,
            evidence_summary=(
                f"No near-identical-amount cluster met the review threshold for "
                f"{data.provider_code} (largest cluster={len(cluster)})."
            ),
            plausible_benign_explanation=_BENIGN,
            suppression_reason=None,
        )

    window_start = min(t.occurred_at for t in cluster)
    window_end = max(t.occurred_at for t in cluster)
    amounts = [t.amount for t in cluster]
    amount_min, amount_max = min(amounts), max(amounts)
    representative = max(set(amounts), key=amounts.count)
    txn_ids = [t.transaction_id for t in cluster]

    evidence_items = [
        AnomalyEvidence("count", "Transactions in cluster", len(cluster), 0),
        AnomalyEvidence(
            "amount_cluster",
            "Amount cluster (representative / min / max)",
            {
                "representative": format(representative, "f"),
                "min": format(amount_min, "f"),
                "max": format(amount_max, "f"),
                "tolerance_pct": config.amount_tolerance_pct,
            },
            1,
        ),
        AnomalyEvidence("distinct_parties", "Distinct synthetic parties", distinct_parties, 2),
        AnomalyEvidence(
            "detection_window",
            "Detection window",
            {"start": window_start.isoformat(), "end": window_end.isoformat()},
            3,
        ),
    ]

    summary = (
        f"{len(cluster)} transactions of about {format(representative, 'f')} BDT "
        f"from {distinct_parties} synthetic party(ies) on {data.provider_code} "
        f"within {config.window_minutes} minutes."
    )

    if degraded:
        # Suppressed: retained for measurement, can never be an alertable anomaly.
        return AnomalyResult(
            detected=True,
            persist=True,
            disposition=AnomalyDisposition.SUPPRESSED_DATA_QUALITY,
            reason_code="suppressed_degraded_quality",
            confidence_score=cfg.quantize_score(Decimal("0.2")),
            confidence_level=ConfidenceLevel.LOW,
            window_start=window_start,
            window_end=window_end,
            evidence_summary=summary,
            plausible_benign_explanation=_BENIGN,
            suppression_reason=(
                f"Data quality is {data.quality_status} (modifier "
                f"{format(data.quality_modifier, 'f')}); pattern is retained for "
                f"measurement but suppressed from alerting."
            ),
            transaction_ids=txn_ids,
            evidence_items=evidence_items,
            distinct_party_count=distinct_parties,
            representative_amount=representative,
        )

    # --- Confidence: cluster strength scaled by quality. -----------------------
    size_factor = min(1.0, len(cluster) / (config.minimum_count * 1.5))
    spread = float((amount_max - amount_min) / representative) if representative else 0.0
    tightness = max(0.0, 1.0 - spread / (config.amount_tolerance_pct / 100.0 or 1.0))
    raw = (0.5 + 0.35 * size_factor + 0.15 * tightness)
    confidence = cfg.quantize_score(Decimal(str(raw)) * data.quality_modifier)

    return AnomalyResult(
        detected=True,
        persist=True,
        disposition=AnomalyDisposition.REQUIRES_REVIEW,
        reason_code="near_identical_amount_cluster",
        confidence_score=confidence,
        confidence_level=cfg.confidence_level_for(confidence),
        window_start=window_start,
        window_end=window_end,
        evidence_summary=summary,
        plausible_benign_explanation=_BENIGN,
        suppression_reason=None,
        transaction_ids=txn_ids,
        evidence_items=evidence_items,
        distinct_party_count=distinct_parties,
        representative_amount=representative,
    )
