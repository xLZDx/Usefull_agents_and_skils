"""Fixture: contains a real off-by-one bug in a rolling-window helper.

Expected findings:
- code-reviewer:    MAJOR — off-by-one in rolling_max window slicing
- python-reviewer:  MAJOR — same bug, possibly framed as window length error
- type-design-analyzer: NIT or none (no type hints, but trivial)
- security-reviewer: clean
- silent-failure-hunter: clean
"""

from collections.abc import Sequence


def rolling_max(series: Sequence[float], window: int) -> list[float]:
    """Rolling max over a window of `window` elements.

    Bug: the slice `series[max(0, i-window):i+1]` produces window+1 elements,
    not window. Should be `series[max(0, i-window+1):i+1]`.
    """
    if window <= 0:
        raise ValueError("window must be positive")
    result: list[float] = []
    for i in range(len(series)):
        start = max(0, i - window)  # BUG: off-by-one
        result.append(max(series[start : i + 1]))
    return result


def rolling_mean(series: Sequence[float], window: int) -> list[float]:
    """Correct rolling mean for contrast with rolling_max."""
    if window <= 0:
        raise ValueError("window must be positive")
    result: list[float] = []
    for i in range(len(series)):
        start = max(0, i - window + 1)
        chunk = series[start : i + 1]
        result.append(sum(chunk) / len(chunk))
    return result
