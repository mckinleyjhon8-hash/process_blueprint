"""
performance.py — KPIs, bottlenecks, variants and rework.

All computed deterministically with pandas (no pm4py version coupling), so the
numbers are stable and explainable to a client. Times are in seconds.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from .facts import Bottleneck, Variant

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"


def case_cycle_times(df: pd.DataFrame) -> pd.Series:
    """Per-case end-to-end duration in seconds (0 for single-event cases)."""
    g = df.groupby(CASE)[TS]
    span = (g.max() - g.min()).dt.total_seconds()
    return span.fillna(0.0)


def compute_kpis(df: pd.DataFrame) -> Dict[str, float]:
    cycles = case_cycle_times(df)
    return {
        "n_events": int(len(df)),
        "n_cases": int(df[CASE].nunique()),
        "n_activities": int(df[ACT].nunique()),
        "avg_cycle_time_seconds": round(float(cycles.mean()) if len(cycles) else 0.0, 4),
        "median_cycle_time_seconds": round(float(cycles.median()) if len(cycles) else 0.0, 4),
    }


def activity_frequencies(df: pd.DataFrame) -> Dict[str, int]:
    return {str(k): int(v) for k, v in df[ACT].value_counts().items()}


def start_end_activities(df: pd.DataFrame) -> Tuple[Dict[str, int], Dict[str, int]]:
    ordered = df.sort_values(TS)
    starts = ordered.groupby(CASE)[ACT].first().value_counts()
    ends = ordered.groupby(CASE)[ACT].last().value_counts()
    return (
        {str(k): int(v) for k, v in starts.items()},
        {str(k): int(v) for k, v in ends.items()},
    )


def compute_variants(df: pd.DataFrame, top_n: int = 10) -> Tuple[List[Variant], int]:
    """Return the top-N variants by frequency and the total distinct count."""
    seqs = (
        df.sort_values(TS)
        .groupby(CASE)[ACT]
        .apply(lambda s: tuple(s.tolist()))
    )
    counts = seqs.value_counts()
    variants = [
        Variant(sequence=tuple(seq), frequency=int(freq))
        for seq, freq in counts.head(top_n).items()
    ]
    return variants, int(len(counts))


def compute_bottlenecks(df: pd.DataFrame, top_n: int = 10) -> List[Bottleneck]:
    """Directly-follows pairs ranked by mean waiting time, above mean+1σ."""
    ordered = df.sort_values([CASE, TS])
    ordered = ordered.assign(
        _next_act=ordered.groupby(CASE)[ACT].shift(-1),
        _next_ts=ordered.groupby(CASE)[TS].shift(-1),
    ).dropna(subset=["_next_act", "_next_ts"])

    if ordered.empty:
        return []

    ordered = ordered.assign(
        _wait=(ordered["_next_ts"] - ordered[TS]).dt.total_seconds()
    )
    grp = ordered.groupby([ACT, "_next_act"])["_wait"]
    stats = grp.agg(["mean", "count"]).reset_index()

    mean_all = stats["mean"].mean()
    std_all = stats["mean"].std(ddof=0)
    threshold = mean_all + std_all if std_all and std_all > 0 else mean_all

    flagged = stats[stats["mean"] > threshold].sort_values("mean", ascending=False)
    return [
        Bottleneck(
            source=str(r[ACT]),
            target=str(r["_next_act"]),
            mean_wait_seconds=round(float(r["mean"]), 4),
            occurrences=int(r["count"]),
        )
        for _, r in flagged.head(top_n).iterrows()
    ]


def compute_rework(df: pd.DataFrame) -> Dict[str, int]:
    """Activities that repeat within a case (rework / loops) → total repeats."""
    ordered = df.sort_values([CASE, TS])
    rework: Dict[str, int] = {}
    for _, case_df in ordered.groupby(CASE):
        counts = case_df[ACT].value_counts()
        for act, c in counts.items():
            if c > 1:
                rework[str(act)] = rework.get(str(act), 0) + int(c - 1)
    return dict(sorted(rework.items(), key=lambda kv: kv[1], reverse=True))
