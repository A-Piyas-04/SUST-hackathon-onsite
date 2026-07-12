"""Deterministic simulation clock.

Each call to ``generate_dataset()`` creates its own timeline anchor — real
"now" at the moment that specific run starts — instead of sharing one fixed
or process-wide anchor. This matters for two reasons:

1. A hardcoded historical anchor (e.g. a literal 2026-07-11 timestamp) makes
   every "projected shortage" time — computed forward from the most recent
   synthetic balance observation — fall further into the past as real time
   moves on, so the dashboard would show "shortage 2 hours ago" instead of a
   forward-looking "in ~X hours" estimate.
2. A single anchor shared across an entire backend process (computed once at
   import time) makes any two SEPARATE scenario runs executed in the same
   backend session land on the exact same synthetic timestamps, since each
   run's event index always maps to anchor + index * minute_step. The ledger
   is append-only (see app/services/simulation/reset.py — Reset clears only
   raw ingestion metadata, never transactions or balance snapshots), so old
   runs' snapshots are never removed. Colliding timestamps between separate
   runs then look exactly like genuinely conflicting balance data (two
   different values reported for the same instant), which spuriously
   degrades data-quality/confidence for every provider and muddles the
   liquidity burn-rate window with unrelated runs' figures.

Anchoring per run (not per process, not to a fixed date) fixes both: each
run's data lands close to real time when it was generated, and separate runs
naturally occupy distinct points on the timeline instead of colliding.

Same-seed generation remains deterministic in every RELATIVE sense — same
amounts, synthetic references, and spacing between events — because the seed
still controls everything generated relative to the anchor. Only the anchor
moment differs between two separately executed runs, which is correct: they
really did happen at different real-world moments. See
tests/phase3/test_determinism.py, which compares relative structure rather
than absolute timestamps for this reason.
"""

from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone

# Process-local, thread-safe monotonic tie-breaker. Some container/host clock
# combinations (observed on Docker Desktop for Windows) report wall-clock time
# at coarser-than-microsecond resolution, so two datetime.now() calls made
# milliseconds apart can return a byte-identical value even though real time
# has genuinely advanced. A plain wall-clock anchor is therefore NOT sufficient
# to guarantee two back-to-back runs land on distinct timestamps. itertools.count
# is documented as atomic/thread-safe in CPython (protected by the GIL) and
# strictly increasing, so it reliably breaks ties the wall clock cannot.
_tie_breaker = itertools.count()


def new_anchor() -> datetime:
    """A fresh timeline anchor for one generation run, at full precision.

    Deliberately not just "the current wall-clock time": two runs started
    close together — including two rapid, back-to-back calls with no real gap
    between them — must still land on distinct anchors, or their synthetic
    timestamps collide exactly like the fixed/process-wide anchors this
    replaced (see module docstring), reproducing the same spurious
    "conflicting balance" bug. The microsecond field is overwritten with a
    strictly increasing counter (mod 1,000,000) rather than trusted from the
    OS clock, which guarantees distinct anchors across calls regardless of the
    underlying platform's actual clock resolution.
    """
    return datetime.now(timezone.utc).replace(microsecond=next(_tie_breaker) % 1_000_000)


def event_time(base: datetime, index: int, *, minute_step: int = 5) -> datetime:
    """Return a deterministic UTC timestamp for the given event index."""
    return base + timedelta(minutes=index * minute_step)


def batch_time(base: datetime, batch_index: int, *, minute_step: int = 15) -> datetime:
    return base + timedelta(minutes=batch_index * minute_step)
