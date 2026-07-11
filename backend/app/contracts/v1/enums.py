"""Enumerations mirroring docs/schema.md §4."""

from __future__ import annotations

from enum import StrEnum


class ProviderCode(StrEnum):
    BKASH = "bkash"
    NAGAD = "nagad"
    ROCKET = "rocket"


class AppRole(StrEnum):
    AGENT = "agent"
    FIELD_OFFICER = "field_officer"
    AREA_MANAGER = "area_manager"
    PROVIDER_OPS = "provider_ops"
    RISK_ANALYST = "risk_analyst"
    MANAGEMENT = "management"
    ADMIN = "admin"


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


class AlertType(StrEnum):
    LIQUIDITY = "liquidity"
    ANOMALY = "anomaly"
    COMBINED = "combined"
    DATA_QUALITY = "data_quality"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertState(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CLOSED = "closed"


class CaseStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class LocaleCode(StrEnum):
    EN = "en"
    BN = "bn"
    BN_LATN = "bn_latn"


class ValidationSplit(StrEnum):
    TUNING = "tuning"
    HELD_OUT = "held_out"
    DEMO = "demo"


class MetricCategory(StrEnum):
    ANALYTICS = "analytics"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    EXPLAINABILITY = "explainability"
