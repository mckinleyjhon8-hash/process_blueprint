"""
sample_log.py — deterministic synthetic Procure-to-Pay event log for tests/demos.

Designed to exercise every Phase-1 capability:
  * 3 distinct variants (happy path, re-approval rework, skipped goods receipt)
  * an injected bottleneck: long waits straight after "Approve PO"
  * rework: "Approve PO" repeated within a case
"""

from __future__ import annotations

import datetime as dt
import random

import pandas as pd

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"

_HAPPY = [
    "Create PO", "Approve PO", "Receive Goods",
    "Receive Invoice", "Match Invoice", "Pay Invoice",
]
_REWORK = [
    "Create PO", "Approve PO", "Approve PO", "Receive Goods",
    "Receive Invoice", "Match Invoice", "Pay Invoice",
]
_SKIP = [
    "Create PO", "Approve PO", "Receive Invoice", "Match Invoice", "Pay Invoice",
]


def build_sample_log(n_cases: int = 60, seed: int = 42) -> pd.DataFrame:
    """Return a normalised event-log DataFrame with canonical pm4py columns."""
    rng = random.Random(seed)
    base = dt.datetime(2026, 1, 1, 9, 0, 0)
    rows = []

    for i in range(n_cases):
        case = f"PO-{1000 + i}"
        t = base + dt.timedelta(hours=rng.randint(0, 240))
        roll = rng.random()
        acts = _REWORK if roll < 0.15 else _SKIP if roll < 0.25 else _HAPPY

        for a in acts:
            rows.append({CASE: case, ACT: a, TS: t})
            # Long wait straight after approval => deliberate bottleneck.
            wait = rng.randint(20, 72) if a == "Approve PO" else rng.randint(1, 6)
            t = t + dt.timedelta(hours=wait)

    df = pd.DataFrame(rows)
    df[TS] = pd.to_datetime(df[TS], utc=True)
    return df


def write_sample_csv(path: str, n_cases: int = 60, seed: int = 42) -> str:
    """Write the sample log to a CSV and return the path."""
    build_sample_log(n_cases=n_cases, seed=seed).to_csv(path, index=False)
    return path
