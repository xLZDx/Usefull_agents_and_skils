"""Fixture: well-written code with no real issues.

Expected findings:
- All Tier B reviewers: clean. NITs only (e.g. could add more tests),
  no BLOCKER, no MAJOR.
"""

from __future__ import annotations

from collections.abc import Sequence


def mean(values: Sequence[float]) -> float:
    """Arithmetic mean of a non-empty sequence.

    Raises:
        ValueError: if `values` is empty.
    """
    if not values:
        raise ValueError("mean of empty sequence")
    return sum(values) / len(values)


def safe_divide(numerator: float, denominator: float) -> float | None:
    """Return numerator / denominator, or None when denominator is zero."""
    if denominator == 0:
        return None
    return numerator / denominator


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp `value` into the inclusive range [lo, hi]."""
    if lo > hi:
        raise ValueError(f"lo ({lo}) must be <= hi ({hi})")
    return max(lo, min(hi, value))
