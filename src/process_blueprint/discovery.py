"""
discovery.py — discover a Petri-net process model from an event log.

Supports the two algorithms that matter for SME consulting:
  * "inductive"  — Inductive Miner. Sound, block-structured models; the default
    because it always yields a replayable net (good for conformance) and reads
    cleanly for clients.
  * "heuristics" — Heuristics Miner. Better at noisy, real-world logs with
    infrequent paths.

Returns ``(net, im, fm, notifications)``. Discovery never renders images here
(no Graphviz dependency); visualisation is a separate, optional concern.
"""

from __future__ import annotations

from typing import Any, List, Tuple

import pandas as pd

import pm4py

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"

_KEYS = dict(activity_key=ACT, timestamp_key=TS, case_id_key=CASE)


def discover(
    df: pd.DataFrame,
    algorithm: str = "inductive",
    noise_threshold: float = 0.0,
) -> Tuple[Any, Any, Any, List[str]]:
    """Discover a Petri net.

    Parameters
    ----------
    df
        Normalised event log (from :func:`ingest`).
    algorithm
        "inductive" (default) or "heuristics".
    noise_threshold
        Inductive Miner filtering of infrequent behaviour (0..1). Ignored for
        heuristics.
    """
    notifications: List[str] = []
    algo = algorithm.lower().strip()

    if algo == "inductive":
        net, im, fm = pm4py.discover_petri_net_inductive(
            df, noise_threshold=noise_threshold, **_KEYS
        )
        notifications.append(
            f"Discovered Petri net via Inductive Miner "
            f"(noise_threshold={noise_threshold})."
        )
    elif algo == "heuristics":
        net, im, fm = pm4py.discover_petri_net_heuristics(df, **_KEYS)
        notifications.append("Discovered Petri net via Heuristics Miner.")
    else:
        raise ValueError(
            f"Unknown discovery algorithm '{algorithm}'. "
            f"Use 'inductive' or 'heuristics'."
        )

    notifications.append(
        f"Model: {len(net.places)} places, {len(net.transitions)} transitions, "
        f"{len(net.arcs)} arcs."
    )
    return net, im, fm, notifications
