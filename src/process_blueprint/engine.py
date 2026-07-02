"""
engine.py — Phase 1 orchestrator.

Runs the full pipeline and returns a single :class:`ProcessFacts`:

    ingest → discover → conform → diagnose (KPIs / bottlenecks / variants / rework)

This is the only function the rest of the system needs from Phase 1.
The pm4py engine stays isolated behind this boundary (AGPL-clean: internal
batch step; downstream layers consume facts, never the engine).
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from . import benchmarks as bench
from . import conformance, discovery, discovery_completeness, insights, performance
from .facts import ModelQuality, ProcessFacts
from .ingest import ingest, IngestError

__all__ = ["analyze", "analyze_dataframe", "IngestError"]


def analyze(
    file_path: str,
    process_type: str = "Unknown",
    column_mapping: Optional[Dict[str, str]] = None,
    algorithm: str = "inductive",
) -> ProcessFacts:
    """Run the Phase-1 pipeline on a CSV/XES file and return ProcessFacts."""
    df, notes = ingest(file_path, column_mapping=column_mapping)
    facts = analyze_dataframe(df, process_type=process_type, algorithm=algorithm)
    facts.source_file = file_path
    facts.notifications = notes + facts.notifications
    return facts


def analyze_dataframe(
    df: pd.DataFrame,
    process_type: str = "Unknown",
    algorithm: str = "inductive",
) -> ProcessFacts:
    """Run discovery → conformance → diagnostics on an already-ingested df."""
    notifications: List[str] = []

    # --- discovery + conformance (best-effort; never fatal to the facts) ---
    model = ModelQuality(algorithm=algorithm)
    try:
        net, im, fm, disc_notes = discovery.discover(df, algorithm=algorithm)
        notifications += disc_notes
        model, conf_notes = conformance.evaluate(df, net, im, fm, algorithm=algorithm)
        notifications += conf_notes
    except Exception as exc:  # pragma: no cover - defensive
        notifications.append(f"Model discovery/conformance failed: {exc}")

    # --- diagnostics (pure pandas; the backbone numbers) ---
    kpis = performance.compute_kpis(df)
    start_acts, end_acts = performance.start_end_activities(df)
    act_freq = performance.activity_frequencies(df)
    top_variants, n_variants = performance.compute_variants(df)
    bottlenecks = performance.compute_bottlenecks(df)
    rework = performance.compute_rework(df)

    notifications.append(
        f"Diagnostics: {n_variants} variants, {len(bottlenecks)} bottlenecks, "
        f"{len(rework)} rework activities."
    )

    # --- v1.1 insight layers: performance DFG, percentiles, people, batching ---
    flow, time_profile, resources, batching, ins_notes = insights.compute_all(
        df, kpis["n_cases"]
    )
    notifications += ins_notes

    facts = ProcessFacts(
        process_type=process_type,
        source_file="<dataframe>",
        n_events=kpis["n_events"],
        n_cases=kpis["n_cases"],
        n_activities=kpis["n_activities"],
        n_variants=n_variants,
        avg_cycle_time_seconds=kpis["avg_cycle_time_seconds"],
        median_cycle_time_seconds=kpis["median_cycle_time_seconds"],
        start_activities=start_acts,
        end_activities=end_acts,
        activity_frequencies=act_freq,
        model=model,
        bottlenecks=bottlenecks,
        top_variants=top_variants,
        rework_activities=rework,
        flow=flow,
        time_profile=time_profile,
        resources=resources,
        batching=batching,
        notifications=notifications,
    )

    # Every log-derived figure is measured evidence (discovery playbook E1).
    facts.provenance = {
        k: "measured"
        for k in (
            "lead_time_days", "fpy_pct", "rework_rate_pct", "exception_rate_pct",
            "heavy_tail_ratio", "n_cases", "n_events", "n_variants",
        )
    }
    facts.benchmarks = bench.apply_benchmarks(facts)
    facts.discovery = discovery_completeness.compute(facts)
    return facts
