from datetime import timedelta

import pytest

from backend.analytics.anomaly_rules import (
    DISPOSITION_REQUIRES_REVIEW,
    SUPPRESSION_NOT_SUPPRESSED,
    _cluster_by_amount,
    detect_near_identical_amounts,
)

_BANNED_WORDS = ("fraud", "fraudster", "blocked", "frozen", "confirmed")


def _window(base_time, minutes=30):
    return base_time, base_time + timedelta(minutes=minutes)


def test_provider_isolation_rejects_mixed_input(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    transactions = [
        txn_factory(provider_code="bkash", amount=1000.0, occurred_at=window_start + timedelta(minutes=1)),
        txn_factory(provider_code="nagad", amount=1000.0, occurred_at=window_start + timedelta(minutes=2)),
    ]

    with pytest.raises(ValueError):
        detect_near_identical_amounts(
            transactions,
            fresh_quality(),
            provider_code="bkash",
            outlet_id="outlet-1",
            window_start=window_start,
            window_end=window_end,
        )


def test_threshold_edges_inclusive_and_exclusive(base_time, txn_factory):
    window_start, _ = _window(base_time)
    baseline = [
        txn_factory(provider_code="bkash", amount=1000.0, occurred_at=window_start),
        txn_factory(provider_code="bkash", amount=1000.0, occurred_at=window_start + timedelta(minutes=1)),
    ]

    included = baseline + [
        txn_factory(provider_code="bkash", amount=1020.0, occurred_at=window_start + timedelta(minutes=2))
    ]
    clusters_included = _cluster_by_amount(included, tolerance_pct=0.02)
    assert len(clusters_included) == 1
    assert len(clusters_included[0]) == 3

    excluded = baseline + [
        txn_factory(provider_code="bkash", amount=1020.01, occurred_at=window_start + timedelta(minutes=2))
    ]
    clusters_excluded = _cluster_by_amount(excluded, tolerance_pct=0.02)
    assert len(clusters_excluded) == 2
    assert {len(c) for c in clusters_excluded} == {2, 1}


def test_benign_demand_many_accounts_round_number_no_high_confidence(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)

    # Over the max_distinct_accounts ceiling (default 5) -- must not be flagged at all.
    over_ceiling = [
        txn_factory(
            provider_code="bkash",
            amount=1000.0,
            synthetic_party_ref=f"syn-party-{i}",
            occurred_at=window_start + timedelta(minutes=i),
        )
        for i in range(8)
    ]
    result = detect_near_identical_amounts(
        over_ceiling,
        fresh_quality(),
        provider_code="bkash",
        outlet_id="outlet-1",
        window_start=window_start,
        window_end=window_end,
    )
    assert result == []

    # Exactly at the ceiling, still all round amounts -- may be flagged, but never high confidence.
    at_ceiling = [
        txn_factory(
            provider_code="bkash",
            amount=1000.0,
            synthetic_party_ref=f"syn-party-{i}",
            occurred_at=window_start + timedelta(minutes=i),
        )
        for i in range(5)
    ]
    result = detect_near_identical_amounts(
        at_ceiling,
        fresh_quality(),
        provider_code="bkash",
        outlet_id="outlet-1",
        window_start=window_start,
        window_end=window_end,
    )
    for envelope in result:
        assert envelope.confidence_level != "high"


def test_small_cluster_below_minimum_not_flagged(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    transactions = [
        txn_factory(provider_code="bkash", amount=987.0, occurred_at=window_start),
        txn_factory(provider_code="bkash", amount=988.0, occurred_at=window_start + timedelta(minutes=1)),
    ]

    result = detect_near_identical_amounts(
        transactions,
        fresh_quality(),
        provider_code="bkash",
        outlet_id="outlet-1",
        window_start=window_start,
        window_end=window_end,
        min_cluster_size=3,
    )
    assert result == []


def test_happy_path_cluster_flagged_with_evidence(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    amounts = [985.00, 987.50, 988.20, 990.00]
    transactions = [
        txn_factory(
            provider_code="bkash",
            amount=amount,
            synthetic_party_ref=f"syn-party-{i % 3}",
            occurred_at=window_start + timedelta(minutes=i),
        )
        for i, amount in enumerate(amounts)
    ]

    result = detect_near_identical_amounts(
        transactions,
        fresh_quality(),
        provider_code="bkash",
        outlet_id="outlet-1",
        window_start=window_start,
        window_end=window_end,
    )

    assert len(result) == 1
    envelope = result[0]
    assert len(envelope.evidence) > 0
    assert envelope.engine_specific["plausible_benign_explanation"]
    assert envelope.engine_specific["disposition"] == DISPOSITION_REQUIRES_REVIEW


def test_suppression_disposition_field_present_and_defaulted(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    amounts = [985.00, 987.50, 988.20, 990.00]
    transactions = [
        txn_factory(
            provider_code="bkash",
            amount=amount,
            synthetic_party_ref=f"syn-party-{i % 3}",
            occurred_at=window_start + timedelta(minutes=i),
        )
        for i, amount in enumerate(amounts)
    ]

    result = detect_near_identical_amounts(
        transactions,
        fresh_quality(),
        provider_code="bkash",
        outlet_id="outlet-1",
        window_start=window_start,
        window_end=window_end,
    )

    assert len(result) == 1
    assert result[0].engine_specific["suppression_disposition"] == SUPPRESSION_NOT_SUPPRESSED


def test_safe_language_scan(base_time, fresh_quality, txn_factory):
    window_start, window_end = _window(base_time)
    scenarios = [
        [985.00, 987.50, 988.20, 990.00],  # happy path
        [1000.0, 1000.0, 1000.0, 1000.0, 1000.0],  # round-number, at-ceiling
    ]

    strings_to_check = []
    for amounts in scenarios:
        transactions = [
            txn_factory(
                provider_code="bkash",
                amount=amount,
                synthetic_party_ref=f"syn-party-{i % 5}",
                occurred_at=window_start + timedelta(minutes=i),
            )
            for i, amount in enumerate(amounts)
        ]
        result = detect_near_identical_amounts(
            transactions,
            fresh_quality(),
            provider_code="bkash",
            outlet_id="outlet-1",
            window_start=window_start,
            window_end=window_end,
        )
        for envelope in result:
            strings_to_check.append(envelope.engine_specific["evidence_summary"])
            strings_to_check.append(envelope.engine_specific["plausible_benign_explanation"])
            strings_to_check.append(envelope.engine_specific["reason_code"])

    combined = " ".join(strings_to_check).lower()
    for banned in _BANNED_WORDS:
        assert banned not in combined
