"""Shared enumerations mirrored from docs/schema.md Section 4.

Owner: Member 1, limited to the enums needed by Member 1's own tables
(001/002/003/005 migrations). Coordination-only enums (`app_role`,
`case_status`, `assignment_reason`, `notification_channel`,
`notification_status`, `locale_code`) belong to Member 2's migration file.

These are implemented as Python str Enums backing Pydantic schemas; the
matching database columns use `text` + `CHECK (... IN (...))` constraints
(schema.md Section 4: "Constrained text is easier to evolve during the
hackathon") rather than native Postgres ENUM types, so values can be extended
without an `ALTER TYPE` migration.

`fraud`, `fraudster`, `blocked`, `frozen`, and similar definitive or
financial-action states are intentionally absent from every enum below.
"""
from enum import StrEnum


class ProviderCode(StrEnum):
    BKASH = "bkash"
    NAGAD = "nagad"
    ROCKET = "rocket"


class TransactionType(StrEnum):
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    PAYMENT = "payment"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class FeedEventType(StrEnum):
    TRANSACTION = "transaction"
    PROVIDER_BALANCE = "provider_balance"
    CASH_BALANCE = "cash_balance"
    HEARTBEAT = "heartbeat"


class NormalizationStatus(StrEnum):
    PENDING = "pending"
    NORMALIZED = "normalized"
    REJECTED = "rejected"


class FeedHealthStatus(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    MISSING = "missing"
    CONFLICTING = "conflicting"


class QualityIssueType(StrEnum):
    LATE_ARRIVAL = "late_arrival"
    MISSING_FEED = "missing_feed"
    MISSING_FIELD = "missing_field"
    CONFLICTING_SNAPSHOT = "conflicting_snapshot"
    IMPOSSIBLE_TRANSITION = "impossible_transition"
    INSUFFICIENT_SAMPLES = "insufficient_samples"
    MALFORMED_PAYLOAD = "malformed_payload"


class ReserveType(StrEnum):
    SHARED_CASH = "shared_cash"
    PROVIDER_E_MONEY = "provider_e_money"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNAVAILABLE = "unavailable"


class AnalyticsEngine(StrEnum):
    LIQUIDITY = "liquidity"
    ANOMALY = "anomaly"
    DATA_QUALITY = "data_quality"


class AnomalyPattern(StrEnum):
    NEAR_IDENTICAL_AMOUNTS = "near_identical_amounts"
    VELOCITY_SPIKE = "velocity_spike"
    TRANSACTION_SPLITTING = "transaction_splitting"
    CIRCULAR_ACTIVITY = "circular_activity"
    BALANCE_INCONSISTENCY = "balance_inconsistency"
    TIME_ANOMALY = "time_anomaly"
    FAILURE_RATE = "failure_rate"


class AnomalyDisposition(StrEnum):
    REQUIRES_REVIEW = "requires_review"
    SUPPRESSED_DATA_QUALITY = "suppressed_data_quality"
    DISMISSED_BENIGN = "dismissed_benign"
    CONFIRMED_UNUSUAL = "confirmed_unusual"
    INCONCLUSIVE = "inconclusive"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FaultType(StrEnum):
    DELAY = "delay"
    MISSING_FEED = "missing_feed"
    MISSING_FIELD = "missing_field"
    CONFLICTING_BALANCE = "conflicting_balance"
    MALFORMED_PAYLOAD = "malformed_payload"


class ValidationSplit(StrEnum):
    TUNING = "tuning"
    HELD_OUT = "held_out"
    DEMO = "demo"


class AlertType(StrEnum):
    """Referenced by Member 1's AlertCandidate adapter; the `alerts` table
    itself (migration 004) is owned by Member 2."""

    LIQUIDITY = "liquidity"
    ANOMALY = "anomaly"
    COMBINED = "combined"
    DATA_QUALITY = "data_quality"
