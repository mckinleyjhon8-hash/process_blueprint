"""
scoring.py — the Process Health Score, computed from REAL conformance metrics.

This is the correct implementation of the score that the legacy prototype always
returned "F" for (because fitness/precision were never populated). Here they are,
so the score is meaningful. Weights are renormalised over whichever metrics are
available, so a partial model still yields a sensible score.
"""

from __future__ import annotations

from typing import Optional, Tuple

from ..facts import ProcessFacts

_WEIGHTS = {
    "fitness": 0.40,
    "precision": 0.25,
    "generalization": 0.15,
    "simplicity": 0.20,
}


def health_score(facts: ProcessFacts) -> Tuple[Optional[int], str]:
    """Return (score 0-100 or None, grade label)."""
    m = facts.model
    values = {
        "fitness": m.fitness,
        "precision": m.precision,
        "generalization": m.generalization,
        "simplicity": m.simplicity,
    }

    num = 0.0
    den = 0.0
    for key, weight in _WEIGHTS.items():
        v = values.get(key)
        if isinstance(v, (int, float)):
            num += min(max(float(v), 0.0), 1.0) * weight
            den += weight

    if den == 0.0:
        return None, "N/A (insufficient model data)"

    score = round(num / den * 100)
    return score, _grade(score)


def _grade(score: int) -> str:
    if score >= 85:
        return "A (Excellent)"
    if score >= 70:
        return "B (Good)"
    if score >= 55:
        return "C (Moderate)"
    if score >= 40:
        return "D (Poor)"
    return "F (Critical)"
