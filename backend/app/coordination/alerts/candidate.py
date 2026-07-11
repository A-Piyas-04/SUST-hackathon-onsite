"""AlertCandidate consumer contract + validator (member-2 plan Section 6.1;
master Sections 9.10-9.11, Checkpoint 3).

Owner: Member 2. Pure-stdlib. This is the frozen v1 contract for the object
Member 1 hands Member 2 after it persists a Member 3 ResultEnvelope.

Member 2 VALIDATES and REJECTS; it never recalculates confidence/anomaly
scores or re-derives suppression. Alertability and suppression are read from
Member 1's persisted-result lookup (`ReferenceLookup`), which reflects Member
3's truth table.

Rejection codes are stable and machine-readable (master "Suggested rejection-code
categories"). Candidate ingestion is an INTERNAL Member 1 -> Member 2 surface,
so detailed rejection reasons are acceptable here; they are never rendered to an
unauthorized external caller.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from app.coordination.shared.enums import (
    SUPPORTED_CANDIDATE_VERSIONS,
    AlertType,
    Severity,
)
from app.coordination.shared.references import ReferenceLookup
from app.coordination.shared.security import (
    scan_structured_variables,
    scan_workflow_text,
)

VALID_ALERT_TYPES: frozenset[str] = frozenset(t.value for t in AlertType)
VALID_SEVERITIES: frozenset[str] = frozenset(s.value for s in Severity)
VALID_SOURCE_TYPES: frozenset[str] = frozenset(
    {"liquidity_projection", "anomaly_flag", "data_quality_assessment"}
)
HIGH_IMPACT: frozenset[str] = frozenset({Severity.HIGH.value, Severity.CRITICAL.value})

#: Structured-variable keys that would imply Member 2 recalculating or
#: overriding analytical truth — forbidden by contract.
_FORBIDDEN_VARIABLE_KEYS: frozenset[str] = frozenset(
    {
        "confidence_override",
        "recomputed_confidence",
        "override_suppression",
        "force_alert",
        "recompute",
    }
)


class RejectionCode(StrEnum):
    UNSUPPORTED_CANDIDATE_VERSION = "UNSUPPORTED_CANDIDATE_VERSION"
    INVALID_ALERT_TYPE = "INVALID_ALERT_TYPE"
    SOURCE_RESULT_NOT_FOUND = "SOURCE_RESULT_NOT_FOUND"
    SOURCE_RESULT_NOT_ALERTABLE = "SOURCE_RESULT_NOT_ALERTABLE"
    SOURCE_SCOPE_MISMATCH = "SOURCE_SCOPE_MISMATCH"
    PROVIDER_SCOPE_MISMATCH = "PROVIDER_SCOPE_MISMATCH"
    OUTLET_SCOPE_MISMATCH = "OUTLET_SCOPE_MISMATCH"
    SUPPRESSED_ANOMALY = "SUPPRESSED_ANOMALY"
    MISSING_BENIGN_CONTEXT = "MISSING_BENIGN_CONTEXT"
    UNSAFE_STRUCTURED_VARIABLE = "UNSAFE_STRUCTURED_VARIABLE"
    UNSAFE_RECOMMENDED_ACTION = "UNSAFE_RECOMMENDED_ACTION"
    INVALID_DEDUPLICATION_KEY = "INVALID_DEDUPLICATION_KEY"
    INVALID_SEVERITY = "INVALID_SEVERITY"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    INVALID_SHARED_CASH_SCOPE = "INVALID_SHARED_CASH_SCOPE"
    MISSING_SOURCE_RESULTS = "MISSING_SOURCE_RESULTS"
    EMPTY_HIGH_IMPACT_EVIDENCE = "EMPTY_HIGH_IMPACT_EVIDENCE"
    CONFIDENCE_OVERRIDE_ATTEMPT = "CONFIDENCE_OVERRIDE_ATTEMPT"
    MALFORMED_CANDIDATE = "MALFORMED_CANDIDATE"


@dataclass(frozen=True)
class SourceLink:
    result_type: str
    source_result_id: str


@dataclass(frozen=True)
class AlertCandidate:
    candidate_version: str
    alert_type: str
    outlet_id: str
    provider_id: str | None
    severity: str
    source_result_ids: tuple[SourceLink, ...]
    detected_at: str
    deduplication_key: str
    structured_variables: dict[str, Any]
    plausible_benign_explanation: str | None
    requires_case: bool
    recommended_next_step: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "AlertCandidate":
        raw_sources = data.get("source_result_ids") or []
        links: list[SourceLink] = []
        for item in raw_sources:
            if isinstance(item, dict):
                links.append(
                    SourceLink(
                        result_type=str(item.get("result_type", "")),
                        source_result_id=str(item.get("source_result_id", "")),
                    )
                )
            else:  # bare id — tolerated but flagged untyped downstream
                links.append(SourceLink(result_type="", source_result_id=str(item)))
        return AlertCandidate(
            candidate_version=str(data.get("candidate_version", "")),
            alert_type=str(data.get("alert_type", "")),
            outlet_id=str(data.get("outlet_id", "")),
            provider_id=data.get("provider_id"),
            severity=str(data.get("severity", "")),
            source_result_ids=tuple(links),
            detected_at=str(data.get("detected_at", "")),
            deduplication_key=str(data.get("deduplication_key", "")),
            structured_variables=dict(data.get("structured_variables") or {}),
            plausible_benign_explanation=data.get("plausible_benign_explanation"),
            requires_case=bool(data.get("requires_case", False)),
            recommended_next_step=str(data.get("recommended_next_step", "")),
        )


@dataclass(frozen=True)
class Rejection:
    code: RejectionCode
    detail: str
    field: str | None = None


@dataclass(frozen=True)
class CandidateValidationResult:
    accepted: bool
    rejections: tuple[Rejection, ...] = field(default_factory=tuple)

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(str(r.code) for r in self.rejections)


def _is_iso_utc(value: str) -> bool:
    if not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def validate_candidate(
    candidate: AlertCandidate,
    lookup: ReferenceLookup,
) -> CandidateValidationResult:
    """Validate a candidate against the frozen contract and Member 1's lookup.

    Collects ALL applicable rejections (internal surface) so the producer gets a
    complete picture. Never mutates analytical evidence; suppression/alertability
    come from `lookup`, not recomputation.
    """
    rejections: list[Rejection] = []

    def reject(code: RejectionCode, detail: str, field_name: str | None = None) -> None:
        rejections.append(Rejection(code, detail, field_name))

    # 1. Version
    if candidate.candidate_version not in SUPPORTED_CANDIDATE_VERSIONS:
        reject(
            RejectionCode.UNSUPPORTED_CANDIDATE_VERSION,
            f"version {candidate.candidate_version!r} not in {sorted(SUPPORTED_CANDIDATE_VERSIONS)}",
            "candidate_version",
        )

    # 2. Alert type
    if candidate.alert_type not in VALID_ALERT_TYPES:
        reject(RejectionCode.INVALID_ALERT_TYPE, candidate.alert_type, "alert_type")

    # 3. Severity
    if candidate.severity not in VALID_SEVERITIES:
        reject(RejectionCode.INVALID_SEVERITY, candidate.severity, "severity")

    # 4. Timestamp
    if not _is_iso_utc(candidate.detected_at):
        reject(RejectionCode.INVALID_TIMESTAMP, candidate.detected_at, "detected_at")

    # 5. Deduplication key
    if not candidate.deduplication_key.strip():
        reject(RejectionCode.INVALID_DEDUPLICATION_KEY, "empty", "deduplication_key")

    # 6. Shared-cash vs provider scope. shared-cash alert => provider_id None;
    #    every other alert type must carry a provider_id.
    is_shared_cash = candidate.provider_id is None
    if candidate.alert_type == AlertType.DATA_QUALITY.value:
        pass  # data-quality may be provider-scoped or shared; no extra rule here
    if candidate.alert_type in (AlertType.ANOMALY.value, AlertType.COMBINED.value) and is_shared_cash:
        reject(
            RejectionCode.INVALID_SHARED_CASH_SCOPE,
            "anomaly/combined candidate must be provider-scoped",
            "provider_id",
        )

    # 7. Source results present and typed
    if not candidate.source_result_ids:
        reject(RejectionCode.MISSING_SOURCE_RESULTS, "at least one typed source required", "source_result_ids")
    else:
        for link in candidate.source_result_ids:
            if link.result_type not in VALID_SOURCE_TYPES or not link.source_result_id:
                reject(
                    RejectionCode.SOURCE_RESULT_NOT_FOUND,
                    f"untyped/blank source link {link!r}",
                    "source_result_ids",
                )
                continue
            ref = lookup.get_source_result(link.source_result_id)
            if ref is None:
                reject(RejectionCode.SOURCE_RESULT_NOT_FOUND, link.source_result_id, "source_result_ids")
                continue
            # Scope: source must belong to the claimed outlet/provider.
            if ref.outlet_id != candidate.outlet_id:
                reject(RejectionCode.OUTLET_SCOPE_MISMATCH, link.source_result_id, "outlet_id")
            if ref.provider_id != candidate.provider_id:
                reject(RejectionCode.PROVIDER_SCOPE_MISMATCH, link.source_result_id, "provider_id")
            if not lookup.source_matches_scope(
                link.source_result_id, candidate.outlet_id, candidate.provider_id
            ):
                reject(RejectionCode.SOURCE_SCOPE_MISMATCH, link.source_result_id, "source_result_ids")
            # Alertability / suppression come from Member 1's persisted result.
            if not ref.is_alertable:
                reject(RejectionCode.SOURCE_RESULT_NOT_ALERTABLE, link.source_result_id, "source_result_ids")
            if ref.is_suppressed and candidate.alert_type in (
                AlertType.ANOMALY.value,
                AlertType.COMBINED.value,
            ):
                reject(
                    RejectionCode.SUPPRESSED_ANOMALY,
                    f"suppressed anomaly {link.source_result_id} cannot back an anomaly/combined alert",
                    "source_result_ids",
                )

    # 8. Benign context required for anomaly/combined.
    if candidate.alert_type in (AlertType.ANOMALY.value, AlertType.COMBINED.value):
        if not (candidate.plausible_benign_explanation or "").strip():
            reject(
                RejectionCode.MISSING_BENIGN_CONTEXT,
                "anomaly/combined candidate must supply a plausible benign explanation",
                "plausible_benign_explanation",
            )

    # 9. Safe language on structured variables + recommended next step + benign.
    if scan_structured_variables(candidate.structured_variables):
        reject(RejectionCode.UNSAFE_STRUCTURED_VARIABLE, "prohibited language in structured_variables", "structured_variables")
    if scan_workflow_text(candidate.recommended_next_step):
        reject(RejectionCode.UNSAFE_RECOMMENDED_ACTION, "prohibited language in recommended_next_step", "recommended_next_step")
    if scan_workflow_text(candidate.plausible_benign_explanation):
        reject(RejectionCode.UNSAFE_STRUCTURED_VARIABLE, "prohibited language in benign explanation", "plausible_benign_explanation")

    # 10. No confidence-override / recalculation attempts.
    forbidden = _FORBIDDEN_VARIABLE_KEYS & set(candidate.structured_variables.keys())
    if forbidden:
        reject(
            RejectionCode.CONFIDENCE_OVERRIDE_ATTEMPT,
            f"structured_variables must not override analytics: {sorted(forbidden)}",
            "structured_variables",
        )

    # 11. High-impact alerts must carry non-empty evidence variables.
    if candidate.severity in HIGH_IMPACT:
        evidence = candidate.structured_variables.get("evidence_summary") or candidate.structured_variables.get("evidence")
        evidence_items = candidate.structured_variables.get("evidence_items")
        if not (str(evidence or "").strip() or evidence_items):
            reject(
                RejectionCode.EMPTY_HIGH_IMPACT_EVIDENCE,
                "high-impact alert requires non-empty evidence variables",
                "structured_variables",
            )

    return CandidateValidationResult(accepted=not rejections, rejections=tuple(rejections))
