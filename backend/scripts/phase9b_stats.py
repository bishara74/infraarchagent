"""Descriptive binomial intervals and fixed-margin two-sided Fisher tests."""

from math import comb, sqrt


def wilson(passed: int, total: int) -> tuple[float | None, float | None]:
    if not 0 <= passed <= total:
        raise ValueError("Invalid binomial counts")
    if not total:
        return None, None
    z = 1.959963984540054
    rate = passed / total
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    half = z * sqrt(rate * (1 - rate) / total + z * z / (4 * total**2)) / denominator
    return (
        0.0 if passed == 0 else max(0.0, center - half),
        1.0 if passed == total else min(1.0, center + half),
    )


def fisher(a: int, n: int, b: int, m: int) -> float:
    """Sum tables no more likely than observed, using exact integer weights."""
    if not (0 <= a <= n and 0 <= b <= m):
        raise ValueError("Invalid contingency table")
    successes = a + b
    observed = comb(n, a) * comb(m, b)
    weights = (
        comb(n, x) * comb(m, successes - x)
        for x in range(max(0, successes - m), min(n, successes) + 1)
    )
    return sum(weight for weight in weights if weight <= observed) / comb(
        n + m, successes
    )
