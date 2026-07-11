"""Small shared primitives for combining independent confidence signals.

Both engines derive their overall confidence score from several partial
signals (sample size, stability/concentration, data-quality modifier).
A geometric mean is used rather than an arithmetic average so that any
single weak signal (e.g. only one sample, or a stale feed) pulls the
combined score toward zero instead of being diluted by the other,
healthier signals -- this is what lets the engines satisfy "never a
falsely precise estimate" when input is thin or degraded.
"""

from __future__ import annotations


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def combine_confidence(*components: float) -> float:
    """Geometric mean of one or more components, each expected in [0, 1].

    Any component <= 0 forces the combined result to 0 (a weak/absent
    signal should dominate, not be averaged away).
    """
    if not components:
        return 0.0
    clamped = [clamp(c) for c in components]
    if any(c <= 0.0 for c in clamped):
        return 0.0
    product = 1.0
    for c in clamped:
        product *= c
    return clamp(product ** (1.0 / len(clamped)))
