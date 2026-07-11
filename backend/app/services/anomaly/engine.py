"""Anomaly Detection Engine (pure, deterministic).

Implements near-identical-amount repetition, transaction velocity spike, and
balance inconsistency / data-conflict rules within a single provider/outlet scope.
A flag means "unusual / requires review" and is never a determination of
wrongdoing; every actionable result carries a plausible benign explanation. When
the underlying data quality is degraded, an otherwise detectable pattern is
*suppressed* (persisted for measurement but never alertable) rather than
presented as a confident anomaly.
"""

from __future__ import annotations

import hashlib
import math
import statistics
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
    transaction_type: str | None = None
    status: str = "completed"


@dataclass(frozen=True)
class BalanceSnapshotRecord:
    observed_at: datetime
    balance: Decimal
    received_at: datetime | None = None


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
class VelocityRuleConfig:
    window_minutes: int = cfg.VELOCITY_SPIKE_DEFAULT_CONFIG["window_minutes"]
    std_dev_threshold: float = cfg.VELOCITY_SPIKE_DEFAULT_CONFIG["std_dev_threshold"]
    minimum_baseline_windows: int = cfg.VELOCITY_SPIKE_DEFAULT_CONFIG[
        "minimum_baseline_windows"
    ]
    minimum_spike_count: int = cfg.VELOCITY_SPIKE_DEFAULT_CONFIG["minimum_spike_count"]

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "VelocityRuleConfig":
        raw = raw or {}
        return cls(
            window_minutes=int(raw.get("window_minutes", cls.window_minutes)),
            std_dev_threshold=float(raw.get("std_dev_threshold", cls.std_dev_threshold)),
            minimum_baseline_windows=int(
                raw.get("minimum_baseline_windows", cls.minimum_baseline_windows)
            ),
            minimum_spike_count=int(raw.get("minimum_spike_count", cls.minimum_spike_count)),
        )


@dataclass(frozen=True)
class BalanceRuleConfig:
    min_discrepancy_amount: float = cfg.BALANCE_INCONSISTENCY_DEFAULT_CONFIG[
        "min_discrepancy_amount"
    ]
    min_discrepancy_pct: float = cfg.BALANCE_INCONSISTENCY_DEFAULT_CONFIG["min_discrepancy_pct"]
    staleness_soft_minutes: int = cfg.BALANCE_INCONSISTENCY_DEFAULT_CONFIG[
        "staleness_soft_minutes"
    ]

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "BalanceRuleConfig":
        raw = raw or {}
        return cls(
            min_discrepancy_amount=float(
                raw.get("min_discrepancy_amount", cls.min_discrepancy_amount)
            ),
            min_discrepancy_pct=float(raw.get("min_discrepancy_pct", cls.min_discrepancy_pct)),
            staleness_soft_minutes=int(
                raw.get("staleness_soft_minutes", cls.staleness_soft_minutes)
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
class VelocityAnomalyInput:
    provider_code: str
    transactions: list[TransactionRecord]
    quality_status: str
    quality_modifier: Decimal
    as_of: datetime
    rule_config: VelocityRuleConfig = field(default_factory=VelocityRuleConfig)


@dataclass(frozen=True)
class BalanceAnomalyInput:
    provider_code: str
    transactions: list[TransactionRecord]
    observations: list[BalanceSnapshotRecord]
    quality_status: str
    quality_modifier: Decimal
    as_of: datetime
    rule_config: BalanceRuleConfig = field(default_factory=BalanceRuleConfig        )


@dataclass(frozen=True)
class BehavioralRuleConfig:
    k: int = cfg.BEHAVIORAL_EMBEDDING_DEFAULT_CONFIG["k"]
    distance_threshold: float = cfg.BEHAVIORAL_EMBEDDING_DEFAULT_CONFIG["distance_threshold"]
    minimum_history_transactions: int = cfg.BEHAVIORAL_EMBEDDING_DEFAULT_CONFIG[
        "minimum_history_transactions"
    ]
    window_minutes: int = cfg.BEHAVIORAL_EMBEDDING_DEFAULT_CONFIG["window_minutes"]

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> "BehavioralRuleConfig":
        raw = raw or {}
        return cls(
            k=int(raw.get("k", cls.k)),
            distance_threshold=float(raw.get("distance_threshold", cls.distance_threshold)),
            minimum_history_transactions=int(
                raw.get("minimum_history_transactions", cls.minimum_history_transactions)
            ),
            window_minutes=int(raw.get("window_minutes", cls.window_minutes)),
        )


@dataclass(frozen=True)
class BehavioralAnomalyInput:
    provider_code: str
    transactions: list[TransactionRecord]
    quality_status: str
    quality_modifier: Decimal
    as_of: datetime
    rule_config: BehavioralRuleConfig = field(default_factory=BehavioralRuleConfig)


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


_BENIGN_NEAR_IDENTICAL = (
    "Repeated similar amounts are common during salary disbursement, festival "
    "demand, or recurring bill payments; this pattern is flagged only for human "
    "review and is not a determination of wrongdoing."
)

_BENIGN_VELOCITY = (
    "Transaction volume can rise sharply on salary days, before festivals such as "
    "Eid, or during local events; this spike is flagged for review and is not "
    "evidence of wrongdoing."
)

_BENIGN_BALANCE = (
    "Reported balances may lag behind the transaction log because of feed delays, "
    "batch settlement, or a manual adjustment not yet reflected in sync; this is "
    "a data-quality finding, not evidence of wallet integrity loss."
)

_BENIGN_BEHAVIORAL = (
    "This transaction may reflect a new but legitimate customer pattern, a change "
    "in product mix, or seasonal demand that has not yet appeared in this outlet's "
    "recent history; being flagged is for human review and is not a determination "
    "of wrongdoing."
)


def _is_degraded_quality(quality_status: str, quality_modifier: Decimal) -> bool:
    return (
        quality_status in {"missing", "conflicting"}
        or quality_modifier <= Decimal(str(cfg.ANOMALY_SUPPRESSION_MODIFIER))
    )


def _suppression_reason(quality_status: str, quality_modifier: Decimal) -> str:
    return (
        f"Data quality is {quality_status} (modifier "
        f"{format(quality_modifier, 'f')}); pattern is retained for "
        f"measurement but suppressed from alerting."
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

    degraded = _is_degraded_quality(data.quality_status, data.quality_modifier)

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
            plausible_benign_explanation=_BENIGN_NEAR_IDENTICAL,
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
            plausible_benign_explanation=_BENIGN_NEAR_IDENTICAL,
            suppression_reason=_suppression_reason(data.quality_status, data.quality_modifier),
            transaction_ids=txn_ids,
            evidence_items=evidence_items,
            distinct_party_count=distinct_parties,
            representative_amount=representative,
        )

    size_factor = min(1.0, len(cluster) / (config.minimum_count * 1.5))
    spread = float((amount_max - amount_min) / representative) if representative else 0.0
    tightness = max(0.0, 1.0 - spread / (config.amount_tolerance_pct / 100.0 or 1.0))
    raw = 0.5 + 0.35 * size_factor + 0.15 * tightness
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
        plausible_benign_explanation=_BENIGN_NEAR_IDENTICAL,
        suppression_reason=None,
        transaction_ids=txn_ids,
        evidence_items=evidence_items,
        distinct_party_count=distinct_parties,
        representative_amount=representative,
    )


def _count_in_window(
    transactions: list[TransactionRecord],
    window_start: datetime,
    window_end: datetime,
) -> list[TransactionRecord]:
    return [t for t in transactions if window_start <= t.occurred_at <= window_end]


def _velocity_baseline_counts(
    transactions: list[TransactionRecord],
    *,
    window_minutes: int,
    target_hour: int,
    exclude_start: datetime,
    exclude_end: datetime,
) -> list[int]:
    """Historical window counts at the same hour-of-day, excluding the current window."""
    if not transactions:
        return []
    window = timedelta(minutes=window_minutes)
    counts: list[int] = []
    seen_ends: set[datetime] = set()
    for anchor in sorted(transactions, key=lambda t: t.occurred_at):
        end = anchor.occurred_at
        if end.hour != target_hour:
            continue
        if end in seen_ends:
            continue
        start = end - window
        if start < exclude_start and end > exclude_start:
            continue
        if not (end < exclude_start or start > exclude_end):
            continue
        seen_ends.add(end)
        counts.append(len(_count_in_window(transactions, start, end)))
    return counts


def detect_velocity_spike(data: VelocityAnomalyInput) -> AnomalyResult:
    config = data.rule_config
    window = timedelta(minutes=config.window_minutes)
    window_end = data.as_of
    window_start = window_end - window
    spike_txns = _count_in_window(data.transactions, window_start, window_end)
    observed_count = len(spike_txns)

    baseline_counts = _velocity_baseline_counts(
        data.transactions,
        window_minutes=config.window_minutes,
        target_hour=window_end.hour,
        exclude_start=window_start,
        exclude_end=window_end,
    )

    if len(baseline_counts) < config.minimum_baseline_windows:
        return AnomalyResult(
            detected=False,
            persist=False,
            disposition=AnomalyDisposition.INCONCLUSIVE,
            reason_code="insufficient_baseline",
            confidence_score=cfg.quantize_score(Decimal("0")),
            confidence_level=ConfidenceLevel.UNAVAILABLE,
            window_start=window_start,
            window_end=window_end,
            evidence_summary=(
                f"Insufficient same-hour baseline for velocity review on "
                f"{data.provider_code} (baseline windows={len(baseline_counts)})."
            ),
            plausible_benign_explanation=_BENIGN_VELOCITY,
            suppression_reason=None,
        )

    typical_count = statistics.mean(baseline_counts)
    std_count = statistics.pstdev(baseline_counts) if len(baseline_counts) > 1 else 0.0
    if std_count > 0:
        std_devs_above = (observed_count - typical_count) / std_count
    else:
        std_devs_above = float(observed_count - typical_count)

    meets_threshold = (
        observed_count >= config.minimum_spike_count
        and std_devs_above >= config.std_dev_threshold
    )

    evidence_items = [
        AnomalyEvidence(
            "observed_count",
            "Transactions in spike window",
            observed_count,
            0,
        ),
        AnomalyEvidence(
            "typical_count",
            "Typical count for this hour-of-day",
            round(typical_count, 2),
            1,
        ),
        AnomalyEvidence(
            "std_devs_above_baseline",
            "Standard deviations above baseline",
            round(std_devs_above, 2),
            2,
        ),
        AnomalyEvidence(
            "detection_window",
            "Detection window",
            {"start": window_start.isoformat(), "end": window_end.isoformat()},
            3,
        ),
        AnomalyEvidence(
            "spike_transactions",
            "Transactions in spike window",
            [
                {
                    "transaction_id": str(t.transaction_id),
                    "party_ref": t.party_ref,
                    "amount": format(t.amount, "f"),
                    "occurred_at": t.occurred_at.isoformat(),
                }
                for t in spike_txns
            ],
            4,
        ),
    ]

    summary = (
        f"{observed_count} transactions on {data.provider_code} in "
        f"{config.window_minutes} minutes vs typical {typical_count:.1f} for this "
        f"hour ({std_devs_above:.1f} std devs above baseline)."
    )

    degraded = _is_degraded_quality(data.quality_status, data.quality_modifier)

    if not meets_threshold:
        return AnomalyResult(
            detected=False,
            persist=False,
            disposition=AnomalyDisposition.INCONCLUSIVE,
            reason_code="no_supported_pattern",
            confidence_score=cfg.quantize_score(Decimal("0")),
            confidence_level=ConfidenceLevel.UNAVAILABLE,
            window_start=window_start,
            window_end=window_end,
            evidence_summary=summary,
            plausible_benign_explanation=_BENIGN_VELOCITY,
            suppression_reason=None,
        )

    if degraded:
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
            plausible_benign_explanation=_BENIGN_VELOCITY,
            suppression_reason=_suppression_reason(data.quality_status, data.quality_modifier),
            transaction_ids=[t.transaction_id for t in spike_txns],
            evidence_items=evidence_items,
            distinct_party_count=len({t.party_ref for t in spike_txns}),
        )

    excess = max(0.0, std_devs_above - config.std_dev_threshold)
    raw = min(1.0, 0.45 + 0.15 * excess)
    confidence = cfg.quantize_score(Decimal(str(raw)) * data.quality_modifier)

    return AnomalyResult(
        detected=True,
        persist=True,
        disposition=AnomalyDisposition.REQUIRES_REVIEW,
        reason_code="velocity_spike",
        confidence_score=confidence,
        confidence_level=cfg.confidence_level_for(confidence),
        window_start=window_start,
        window_end=window_end,
        evidence_summary=summary,
        plausible_benign_explanation=_BENIGN_VELOCITY,
        suppression_reason=None,
        transaction_ids=[t.transaction_id for t in spike_txns],
        evidence_items=evidence_items,
        distinct_party_count=len({t.party_ref for t in spike_txns}),
    )


def _snapshot_conflicts(
    observations: list[BalanceSnapshotRecord],
) -> list[dict[str, Any]]:
    by_time: dict[datetime, set[str]] = {}
    for obs in observations:
        by_time.setdefault(obs.observed_at, set()).add(format(obs.balance, "f"))
    return [
        {"observed_at": ts.isoformat(), "distinct_balances": sorted(vals)}
        for ts, vals in by_time.items()
        if len(vals) > 1
    ]


def _last_trusted_snapshot(
    observations: list[BalanceSnapshotRecord],
) -> BalanceSnapshotRecord | None:
    by_time: dict[datetime, set[str]] = {}
    for obs in observations:
        by_time.setdefault(obs.observed_at, set()).add(format(obs.balance, "f"))
    trusted = [o for o in observations if len(by_time[o.observed_at]) == 1]
    if not trusted:
        return None
    return max(trusted, key=lambda o: o.observed_at)


def _latest_unambiguous_snapshot(
    observations: list[BalanceSnapshotRecord],
) -> BalanceSnapshotRecord | None:
    if not observations:
        return None
    latest_ts = max(o.observed_at for o in observations)
    at_latest = [o for o in observations if o.observed_at == latest_ts]
    balances = {format(o.balance, "f") for o in at_latest}
    if len(balances) != 1:
        return None
    return at_latest[0]


def _reconciliation_anchor(
    observations: list[BalanceSnapshotRecord],
) -> BalanceSnapshotRecord | None:
    """Last unambiguous snapshot before the latest reported balance."""
    reported = _latest_unambiguous_snapshot(observations)
    if reported is None:
        return _last_trusted_snapshot(observations)
    by_time: dict[datetime, set[str]] = {}
    for obs in observations:
        by_time.setdefault(obs.observed_at, set()).add(format(obs.balance, "f"))
    trusted = [o for o in observations if len(by_time[o.observed_at]) == 1]
    prior = [o for o in trusted if o.observed_at < reported.observed_at]
    if prior:
        return max(prior, key=lambda o: o.observed_at)
    return None


def _provider_balance_delta(transaction_type: str | None, amount: Decimal) -> Decimal:
    if transaction_type == "cash_out":
        return amount
    if transaction_type == "cash_in":
        return -amount
    if transaction_type == "refund":
        return amount
    if transaction_type == "payment":
        return -amount
    if transaction_type == "adjustment":
        return amount
    return Decimal("0")


def _expected_balance(
    trusted: BalanceSnapshotRecord,
    transactions: list[TransactionRecord],
    *,
    as_of: datetime,
) -> Decimal:
    expected = trusted.balance
    for txn in transactions:
        if txn.status != "completed":
            continue
        if txn.occurred_at <= trusted.observed_at or txn.occurred_at > as_of:
            continue
        expected += _provider_balance_delta(txn.transaction_type, txn.amount)
    return expected


def detect_balance_inconsistency(data: BalanceAnomalyInput) -> AnomalyResult:
    config = data.rule_config
    observations = data.observations
    window_start = min((o.observed_at for o in observations), default=data.as_of)
    window_end = data.as_of

    conflicts = _snapshot_conflicts(observations)
    anchor = _reconciliation_anchor(observations)
    reported = _latest_unambiguous_snapshot(observations)
    trusted = _last_trusted_snapshot(observations)

    discrepancy: Decimal | None = None
    expected_balance: Decimal | None = None
    reported_balance: Decimal | None = None
    last_consistent_at: datetime | None = None
    reason_detail = "no_supported_pattern"
    conflict_at: datetime | None = None

    if conflicts:
        latest_conflict = max(datetime.fromisoformat(c["observed_at"]) for c in conflicts)
        conflict_at = latest_conflict
        conflict_entry = next(
            c for c in conflicts if c["observed_at"] == latest_conflict.isoformat()
        )
        vals = [Decimal(v) for v in conflict_entry["distinct_balances"]]
        reported_balance = max(vals)
        expected_balance = min(vals)
        discrepancy = abs(reported_balance - expected_balance)
        last_consistent_at = trusted.observed_at if trusted else None
        reason_detail = "conflicting_balance_snapshots"
    elif anchor is not None and reported is not None:
        expected_balance = _expected_balance(anchor, data.transactions, as_of=data.as_of)
        reported_balance = reported.balance
        discrepancy = abs(expected_balance - reported_balance)
        last_consistent_at = anchor.observed_at
        reason_detail = "balance_reconciliation_mismatch"

    staleness_minutes = 0.0
    if observations:
        latest_obs = max(o.observed_at for o in observations)
        staleness_minutes = max(0.0, (data.as_of - latest_obs).total_seconds() / 60.0)

    min_abs = Decimal(str(config.min_discrepancy_amount))
    meets_threshold = False
    if discrepancy is not None and expected_balance is not None and reported_balance is not None:
        pct_base = max(abs(expected_balance), abs(reported_balance), Decimal("1"))
        pct = float(discrepancy / pct_base) * 100.0
        meets_threshold = discrepancy >= min_abs and pct >= config.min_discrepancy_pct

    evidence_items: list[AnomalyEvidence] = []
    if expected_balance is not None and reported_balance is not None and discrepancy is not None:
        evidence_items = [
            AnomalyEvidence(
                "expected_balance",
                "Expected balance from transaction log",
                format(expected_balance, "f"),
                0,
            ),
            AnomalyEvidence(
                "reported_balance",
                "Reported balance from feed",
                format(reported_balance, "f"),
                1,
            ),
            AnomalyEvidence(
                "discrepancy_amount",
                "Discrepancy amount",
                format(discrepancy, "f"),
                2,
            ),
            AnomalyEvidence(
                "last_consistent_at",
                "Last known consistent balance timestamp",
                last_consistent_at.isoformat() if last_consistent_at else None,
                3,
            ),
            AnomalyEvidence(
                "feed_staleness_minutes",
                "Feed staleness (minutes)",
                round(staleness_minutes, 1),
                4,
            ),
        ]
        if conflicts:
            evidence_items.append(
                AnomalyEvidence(
                    "conflicting_snapshots",
                    "Conflicting balance snapshots",
                    conflicts,
                    5,
                )
            )

    if discrepancy is None or not meets_threshold:
        return AnomalyResult(
            detected=False,
            persist=False,
            disposition=AnomalyDisposition.INCONCLUSIVE,
            reason_code="no_supported_pattern",
            confidence_score=cfg.quantize_score(Decimal("0")),
            confidence_level=ConfidenceLevel.UNAVAILABLE,
            window_start=window_start,
            window_end=window_end,
            evidence_summary=(
                f"No balance data conflict met the review threshold for "
                f"{data.provider_code}."
            ),
            plausible_benign_explanation=_BENIGN_BALANCE,
            suppression_reason=None,
            evidence_items=evidence_items,
        )

    summary = (
        f"Data-quality finding on {data.provider_code}: reported balance "
        f"{format(reported_balance, 'f')} BDT vs expected "
        f"{format(expected_balance, 'f')} BDT from the transaction log "
        f"(discrepancy {format(discrepancy, 'f')} BDT"
        f"{'' if last_consistent_at is None else f', last consistent at {last_consistent_at.isoformat()}'})."
    )

    degraded = _is_degraded_quality(data.quality_status, data.quality_modifier)

    if degraded:
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
            plausible_benign_explanation=_BENIGN_BALANCE,
            suppression_reason=_suppression_reason(data.quality_status, data.quality_modifier),
            evidence_items=evidence_items,
        )

    staleness_factor = min(1.0, staleness_minutes / float(config.staleness_soft_minutes))
    pct_base = max(abs(expected_balance), abs(reported_balance), Decimal("1"))
    magnitude = float(discrepancy / pct_base)
    raw = max(0.0, magnitude * (1.0 - 0.6 * staleness_factor))
    confidence = cfg.quantize_score(Decimal(str(min(1.0, raw))) * data.quality_modifier)

    return AnomalyResult(
        detected=True,
        persist=True,
        disposition=AnomalyDisposition.REQUIRES_REVIEW,
        reason_code=reason_detail,
        confidence_score=confidence,
        confidence_level=cfg.confidence_level_for(confidence),
        window_start=window_start,
        window_end=window_end,
        evidence_summary=summary,
        plausible_benign_explanation=_BENIGN_BALANCE,
        suppression_reason=None,
        evidence_items=evidence_items,
    )


def _stable_hash01(value: str) -> float:
    digest = hashlib.sha256(value.encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _minutes_of_day(occurred_at: datetime) -> float:
    return (occurred_at.hour * 60 + occurred_at.minute + occurred_at.second / 60.0) / 1440.0


def _party_frequency(party_ref: str, history: list[TransactionRecord]) -> float:
    if not history:
        return 0.0
    count = sum(1 for txn in history if txn.party_ref == party_ref)
    return count / len(history)


def _raw_feature_components(
    txn: TransactionRecord,
    *,
    history: list[TransactionRecord],
    provider_code: str,
) -> tuple[float, float, float, float, float]:
    return (
        float(txn.amount),
        _minutes_of_day(txn.occurred_at),
        _party_frequency(txn.party_ref, history),
        _stable_hash01(provider_code),
        _stable_hash01(txn.transaction_type or ""),
    )


def _zscore(values: list[float]) -> tuple[list[float], float, float]:
    if not values:
        return [], 0.0, 1.0
    mean = statistics.mean(values)
    if len(values) == 1:
        return [0.0], mean, 1.0
    std = statistics.pstdev(values)
    if std == 0:
        return [0.0 for _ in values], mean, 1.0
    return [(v - mean) / std for v in values], mean, std


def _feature_vector(
    txn: TransactionRecord,
    *,
    history: list[TransactionRecord],
    provider_code: str,
) -> list[float]:
    """Five-dimensional feature vector: amount, time-of-day, party frequency, provider, type."""
    raw_rows = [_raw_feature_components(h, history=history, provider_code=provider_code) for h in history]
    candidate_raw = _raw_feature_components(txn, history=history, provider_code=provider_code)
    if not raw_rows:
        return list(candidate_raw)

    dims = len(candidate_raw)
    zscored_candidate: list[float] = []
    for dim in range(dims):
        col = [row[dim] for row in raw_rows]
        zcol, _, _ = _zscore(col)
        mean = statistics.mean(col)
        std = statistics.pstdev(col) if len(col) > 1 else 1.0
        if std == 0:
            zscored_candidate.append(0.0)
        else:
            zscored_candidate.append((candidate_raw[dim] - mean) / std)
    return zscored_candidate


def _euclidean(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _mean_knn_distance(
    candidate_vec: list[float],
    history_vecs: list[list[float]],
    *,
    k: int,
) -> float:
    if not history_vecs:
        return 0.0
    distances = sorted(_euclidean(candidate_vec, vec) for vec in history_vecs)
    take = min(k, len(distances))
    return sum(distances[:take]) / take


def _median_typical_knn_distance(history_vecs: list[list[float]], *, k: int) -> float:
    if len(history_vecs) < 2:
        return 1.0
    typical: list[float] = []
    for idx, vec in enumerate(history_vecs):
        others = history_vecs[:idx] + history_vecs[idx + 1 :]
        typical.append(_mean_knn_distance(vec, others, k=k))
    return statistics.median(typical) if typical else 1.0


def _nearest_neighbor_records(
    candidate_vec: list[float],
    history: list[TransactionRecord],
    history_vecs: list[list[float]],
    *,
    k: int,
) -> list[TransactionRecord]:
    ranked = sorted(
        zip(history, history_vecs),
        key=lambda pair: _euclidean(candidate_vec, pair[1]),
    )
    return [txn for txn, _ in ranked[: min(k, len(ranked))]]


def _txn_evidence_payload(txn: TransactionRecord) -> dict[str, Any]:
    return {
        "transaction_id": str(txn.transaction_id),
        "party_ref": txn.party_ref,
        "amount": format(txn.amount, "f"),
        "occurred_at": txn.occurred_at.isoformat(),
        "transaction_type": txn.transaction_type,
    }


def detect_behavioral_embedding(data: BehavioralAnomalyInput) -> AnomalyResult:
    config = data.rule_config
    window = timedelta(minutes=config.window_minutes)
    window_end = data.as_of
    window_start = window_end - window

    sorted_txns = sorted(data.transactions, key=lambda t: t.occurred_at)
    candidates = [
        txn
        for txn in sorted_txns
        if window_start <= txn.occurred_at <= window_end and txn.status == "completed"
    ]

    if not candidates:
        return AnomalyResult(
            detected=False,
            persist=False,
            disposition=AnomalyDisposition.INCONCLUSIVE,
            reason_code="no_supported_pattern",
            confidence_score=cfg.quantize_score(Decimal("0")),
            confidence_level=ConfidenceLevel.UNAVAILABLE,
            window_start=window_start,
            window_end=window_end,
            evidence_summary=(
                f"No completed transactions in the behavioral review window for "
                f"{data.provider_code}."
            ),
            plausible_benign_explanation=_BENIGN_BEHAVIORAL,
            suppression_reason=None,
        )

    scored: list[tuple[TransactionRecord, list[TransactionRecord], float, float]] = []
    max_history_count = 0
    for candidate in candidates:
        history = [txn for txn in sorted_txns if txn.occurred_at < candidate.occurred_at]
        max_history_count = max(max_history_count, len(history))
        if len(history) < config.minimum_history_transactions:
            continue

        history_vecs = [
            _feature_vector(txn, history=history, provider_code=data.provider_code)
            for txn in history
        ]
        candidate_vec = _feature_vector(
            candidate, history=history, provider_code=data.provider_code
        )
        distance = _mean_knn_distance(candidate_vec, history_vecs, k=config.k)
        typical = _median_typical_knn_distance(history_vecs, k=config.k)
        scored.append((candidate, history, distance, typical))

    if not scored:
        return AnomalyResult(
            detected=False,
            persist=True,
            disposition=AnomalyDisposition.INCONCLUSIVE,
            reason_code="insufficient_history",
            confidence_score=cfg.quantize_score(Decimal("0")),
            confidence_level=ConfidenceLevel.UNAVAILABLE,
            window_start=window_start,
            window_end=window_end,
            evidence_summary=(
                f"Insufficient transaction history for behavioral review on "
                f"{data.provider_code} (history transactions={max_history_count}, "
                f"minimum={config.minimum_history_transactions})."
            ),
            plausible_benign_explanation=_BENIGN_BEHAVIORAL,
            suppression_reason=None,
            evidence_items=[
                AnomalyEvidence(
                    "insufficient_history",
                    "History transaction count",
                    max_history_count,
                    0,
                ),
                AnomalyEvidence(
                    "minimum_history_transactions",
                    "Minimum history required",
                    config.minimum_history_transactions,
                    1,
                ),
            ],
        )

    worst = max(scored, key=lambda item: item[2])
    candidate, history, distance, typical = worst
    meets_threshold = distance > config.distance_threshold

    history_vecs = [
        _feature_vector(txn, history=history, provider_code=data.provider_code)
        for txn in history
    ]
    candidate_vec = _feature_vector(
        candidate, history=history, provider_code=data.provider_code
    )
    neighbors = _nearest_neighbor_records(
        candidate_vec, history, history_vecs, k=config.k
    )

    ratio = distance / max(typical, 1e-6)
    evidence_items = [
        AnomalyEvidence(
            "knn_distance",
            "Mean k-nearest-neighbor distance",
            round(distance, 4),
            0,
        ),
        AnomalyEvidence(
            "typical_neighbor_distance",
            "Typical neighbor distance for this outlet",
            round(typical, 4),
            1,
        ),
        AnomalyEvidence(
            "distance_ratio",
            "Distance ratio vs typical spread",
            round(ratio, 4),
            2,
        ),
        AnomalyEvidence(
            "distance_threshold",
            "Configured distance threshold",
            config.distance_threshold,
            3,
        ),
        AnomalyEvidence(
            "candidate_transaction",
            "Candidate transaction",
            _txn_evidence_payload(candidate),
            4,
        ),
        AnomalyEvidence(
            "nearest_neighbors",
            "Nearest historical neighbor transactions",
            [_txn_evidence_payload(txn) for txn in neighbors],
            5,
        ),
    ]

    summary = (
        f"Transaction on {data.provider_code} sits {distance:.2f} units from this "
        f"outlet's typical neighborhood (typical spread {typical:.2f}, ratio "
        f"{ratio:.2f})."
    )

    if not meets_threshold:
        return AnomalyResult(
            detected=False,
            persist=False,
            disposition=AnomalyDisposition.INCONCLUSIVE,
            reason_code="no_supported_pattern",
            confidence_score=cfg.quantize_score(Decimal("0")),
            confidence_level=ConfidenceLevel.UNAVAILABLE,
            window_start=window_start,
            window_end=window_end,
            evidence_summary=summary,
            plausible_benign_explanation=_BENIGN_BEHAVIORAL,
            suppression_reason=None,
        )

    if not neighbors:
        return AnomalyResult(
            detected=False,
            persist=False,
            disposition=AnomalyDisposition.INCONCLUSIVE,
            reason_code="no_supported_pattern",
            confidence_score=cfg.quantize_score(Decimal("0")),
            confidence_level=ConfidenceLevel.UNAVAILABLE,
            window_start=window_start,
            window_end=window_end,
            evidence_summary=(
                f"Behavioral outlier detected on {data.provider_code} but nearest "
                f"neighbor evidence could not be materialized."
            ),
            plausible_benign_explanation=_BENIGN_BEHAVIORAL,
            suppression_reason=None,
        )

    degraded = _is_degraded_quality(data.quality_status, data.quality_modifier)

    if degraded:
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
            plausible_benign_explanation=_BENIGN_BEHAVIORAL,
            suppression_reason=_suppression_reason(data.quality_status, data.quality_modifier),
            transaction_ids=[candidate.transaction_id],
            evidence_items=evidence_items,
            distinct_party_count=1,
        )

    raw_confidence = min(1.0, ratio)
    confidence = cfg.quantize_score(Decimal(str(raw_confidence)) * data.quality_modifier)

    return AnomalyResult(
        detected=True,
        persist=True,
        disposition=AnomalyDisposition.REQUIRES_REVIEW,
        reason_code="behavioral_embedding",
        confidence_score=confidence,
        confidence_level=cfg.confidence_level_for(confidence),
        window_start=window_start,
        window_end=window_end,
        evidence_summary=summary,
        plausible_benign_explanation=_BENIGN_BEHAVIORAL,
        suppression_reason=None,
        transaction_ids=[candidate.transaction_id],
        evidence_items=evidence_items,
        distinct_party_count=1,
    )
