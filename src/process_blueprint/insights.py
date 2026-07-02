"""
insights.py — the dormant-pm4py activation layer (Elite Phase E1a).

Adds the analysis dimensions the discovery playbook demands but the original
engine ignored:

  * flow          — the true performance DFG: every hand-off with frequency and
                    wait statistics (mean/median/stdev), not just the top variants.
  * time_profile  — "averages lie": case-duration percentiles (P10/P50/P90),
                    heavy-tail ratio, and how much volume the common paths cover.
  * resources     — the people dimension from `org:resource`: roles, hand-overs,
                    single-points-of-failure.
  * batching      — batch-processing behaviour (trigger for the Batch-to-Flow
                    redesign heuristic), best-effort.

Everything is wrapped so a failure degrades to an empty structure plus a
notification — never fatal. pm4py stays behind the engine boundary.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"
RES = "org:resource"
_KEYS = dict(activity_key=ACT, timestamp_key=TS, case_id_key=CASE)

TOP_EDGES = 30
TOP_HANDOVERS = 12
TOP_ROLES = 15


def compute_flow(df: pd.DataFrame, notifications: List[str]) -> Dict[str, Any]:
    """Performance DFG: frequency + wait stats for every directly-follows edge."""
    try:
        import pm4py

        perf, _sa, _ea = pm4py.discover_performance_dfg(df, **_KEYS)
        freq, _sa2, _ea2 = pm4py.discover_dfg(df, **_KEYS)
        edges = [
            {
                "source": str(s),
                "target": str(t),
                "frequency": int(freq.get((s, t), 0)),
                "mean_wait_seconds": round(float(stats.get("mean", 0.0)), 2),
                "median_wait_seconds": round(float(stats.get("median", 0.0)), 2),
                "stdev_wait_seconds": round(float(stats.get("stdev", 0.0) or 0.0), 2),
            }
            for (s, t), stats in perf.items()
        ]
        edges.sort(key=lambda e: -e["frequency"])
        return {"n_edges": len(edges), "edges": edges[:TOP_EDGES]}
    except Exception as exc:  # pragma: no cover - defensive
        notifications.append(f"Performance DFG not computed: {exc}")
        return {}


def compute_time_profile(
    df: pd.DataFrame,
    n_cases: int,
    notifications: List[str],
) -> Dict[str, Any]:
    """Case-duration distribution + path-coverage honesty numbers."""
    try:
        g = df.groupby(CASE)[TS]
        durations = (g.max() - g.min()).dt.total_seconds()
        seqs = df.sort_values(TS).groupby(CASE)[ACT].apply(tuple)
        counts = seqs.value_counts()
        top1 = float(counts.iloc[0]) if len(counts) else 0.0
        top5 = float(counts.head(5).sum()) if len(counts) else 0.0
        p10, p50, p90 = (
            float(durations.quantile(q)) for q in (0.10, 0.50, 0.90)
        )
        # % of cases containing at least one repeated activity (rework loop)
        rework_cases = (
            df.groupby(CASE)[ACT].apply(lambda s: s.duplicated().any()).sum()
        )
        rework_case_rate = 100.0 * float(rework_cases) / max(n_cases, 1)
        return {
            "rework_case_rate_pct": round(rework_case_rate, 1),
            "fpy_pct": round(100.0 - rework_case_rate, 1),  # right-first-time proxy
            "p10_seconds": round(p10, 2),
            "p50_seconds": round(p50, 2),
            "p90_seconds": round(p90, 2),
            # >2 means the slow tail runs at least twice the typical case —
            # the playbook's signal that the average is hiding the pain
            "heavy_tail_ratio": round(p90 / p50, 2) if p50 > 0 else None,
            "top_variant_coverage_pct": round(100.0 * top1 / max(n_cases, 1), 1),
            "top5_coverage_pct": round(100.0 * top5 / max(n_cases, 1), 1),
            "exception_rate_pct": round(100.0 - 100.0 * top5 / max(n_cases, 1), 1),
        }
    except Exception as exc:  # pragma: no cover - defensive
        notifications.append(f"Time profile not computed: {exc}")
        return {}


def compute_resources(df: pd.DataFrame, notifications: List[str]) -> Dict[str, Any]:
    """Roles, hand-overs and single-points-of-failure from org:resource."""
    if RES not in df.columns or df[RES].dropna().empty:
        return {}
    try:
        work = df.dropna(subset=[RES])

        # roles: which resource performs which activities, ranked by workload
        by_res = (
            work.groupby(RES)[ACT]
            .agg(["count", lambda s: s.value_counts().head(5).index.tolist()])
            .rename(columns={"count": "n_events", "<lambda_0>": "top_activities"})
        )
        by_res.columns = ["n_events", "top_activities"]
        roles = [
            {
                "resource": str(r),
                "n_events": int(row["n_events"]),
                "top_activities": [str(a) for a in row["top_activities"]],
            }
            for r, row in by_res.sort_values("n_events", ascending=False)
            .head(TOP_ROLES)
            .iterrows()
        ]

        # hand-overs: who passes work to whom (consecutive events within a case)
        ordered = work.sort_values([CASE, TS])
        nxt = ordered.groupby(CASE)[RES].shift(-1)
        pairs = pd.DataFrame({"from": ordered[RES], "to": nxt}).dropna()
        pairs = pairs[pairs["from"] != pairs["to"]]
        handovers = [
            {"source": str(a), "target": str(b), "count": int(c)}
            for (a, b), c in pairs.value_counts(["from", "to"]).head(TOP_HANDOVERS).items()
        ]

        # single-points-of-failure: activities executed by exactly one resource
        # (only meaningful when the activity actually recurs)
        per_act = work.groupby(ACT)[RES].agg(["nunique", "count"])
        spof = sorted(
            str(a)
            for a, row in per_act.iterrows()
            if row["nunique"] == 1 and row["count"] >= 5
        )

        return {
            "n_resources": int(work[RES].nunique()),
            "roles": roles,
            "handovers": handovers,
            "single_points_of_failure": spof,
        }
    except Exception as exc:  # pragma: no cover - defensive
        notifications.append(f"Resource analysis not computed: {exc}")
        return {}


def compute_batching(df: pd.DataFrame, notifications: List[str]) -> List[Dict[str, Any]]:
    """Batch-processing detection (Batch-to-Flow trigger). Best-effort —
    pm4py needs start+complete timestamps for full detection; single-timestamp
    logs fall back to a same-moment heuristic."""
    try:
        import pm4py

        batches = pm4py.discover_batches(df, **_KEYS)
        out = []
        for (act_res, batch_type), n in [
            ((b[0], b[1]), len(b[2])) for b in batches
        ][:10]:
            out.append(
                {
                    "activity": str(act_res[0]),
                    "resource": str(act_res[1]),
                    "batch_type": str(batch_type),
                    "n_batches": int(n),
                }
            )
        return out
    except Exception as exc:
        notifications.append(f"Batch detection not available: {exc}")
        return []


def compute_all(
    df: pd.DataFrame, n_cases: int
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], List[Dict[str, Any]], List[str]]:
    """Run every insight; return (flow, time_profile, resources, batching, notes)."""
    notes: List[str] = []
    flow = compute_flow(df, notes)
    time_profile = compute_time_profile(df, n_cases, notes)
    resources = compute_resources(df, notes)
    batching = compute_batching(df, notes)
    return flow, time_profile, resources, batching, notes
