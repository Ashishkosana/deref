"""Empirical complexity classification.

Given measured ``(n, ops)`` points from a run at several input sizes, decide
which complexity class the solution belongs to. For each candidate class ``f``
we compute the Pearson r-squared between ``f(n)`` and ``ops`` and pick the best
fit. Pearson correlation is invariant to both a multiplicative AND an additive
constant (it fits ``ops ~= a*f(n) + b``), so a large fixed setup cost cannot
flatten a quadratic curve into a linear grade, and constant factors within a
class are ignored by design.

This lets us predict the brown-out at huge n *without ever running huge n*: we
fit on a modest sweep and extrapolate the class.
"""

import math

CLASSES = [
    ("O(1)", lambda n: 1.0),
    ("O(log n)", lambda n: math.log2(n) if n > 1 else 1.0),
    ("O(n)", lambda n: float(n)),
    ("O(n log n)", lambda n: n * math.log2(n) if n > 1 else 1.0),
    ("O(n^2)", lambda n: float(n) * n),
]

RANK = {name: i for i, (name, _) in enumerate(CLASSES)}


def _pearson_r2(xs, ys):
    m = len(xs)
    if m < 2:
        return 0.0
    mx = sum(xs) / m
    my = sum(ys) / m
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return 0.0
    r = sxy / math.sqrt(sxx * syy)
    return r * r


def fit_class(points):
    """Return ``(best_class_name, {class_name: r2})`` for points ``[(n, ops)]``."""
    ys = [ops for _, ops in points]
    scores = {}
    for name, f in CLASSES:
        scores[name] = _pearson_r2([f(n) for n, _ in points], ys)
    best = max(scores.values()) if scores else 0.0
    # On a near-exact tie, fail closed toward the higher complexity class.
    near = [name for name, r2 in scores.items() if r2 >= best - 1e-6]
    best_name = max(near, key=lambda nm: RANK[nm]) if near else None
    return best_name, scores


def worse_than(candidate, target):
    """True if ``candidate`` is a strictly higher complexity class than ``target``."""
    return RANK.get(candidate, len(CLASSES)) > RANK.get(target, -1)
