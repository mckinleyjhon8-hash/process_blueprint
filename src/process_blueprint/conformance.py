"""
conformance.py — quantify how well the discovered model matches reality.

This is the module that fixes the original always-"F" health score: it actually
computes fitness and precision (and best-effort generalization/simplicity)
instead of leaving them as None.

Strategy (robust + scalable):
  * Fitness & precision via **token-based replay** — fast, always attempted.
  * Fitness via **alignments** — exact but expensive; only on logs below a case
    threshold, best-effort.
  * generalization / simplicity — best-effort; never fatal.

Every metric is wrapped so a failure degrades to None with a notification rather
than crashing the pipeline.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

import pandas as pd

import pm4py

from .facts import ModelQuality

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"
_KEYS = dict(activity_key=ACT, timestamp_key=TS, case_id_key=CASE)


def _safe(fn, notifications: List[str], label: str) -> Optional[float]:
    try:
        val = fn()
        return None if val is None else float(val)
    except Exception as exc:  # pragma: no cover - defensive
        notifications.append(f"{label} not computed: {exc}")
        return None


def _fitness_value(d: Any) -> Optional[float]:
    """pm4py fitness functions return a dict; pull the log-level fitness."""
    if isinstance(d, dict):
        for k in ("log_fitness", "average_trace_fitness", "averageFitness"):
            if k in d:
                return float(d[k])
        return None
    return float(d) if d is not None else None


def evaluate(
    df: pd.DataFrame,
    net: Any,
    im: Any,
    fm: Any,
    algorithm: str = "inductive",
    max_cases_for_alignments: int = 500,
) -> Tuple[ModelQuality, List[str]]:
    """Compute conformance metrics and return a populated :class:`ModelQuality`."""
    notifications: List[str] = []
    n_cases = df[CASE].nunique()

    fitness = _safe(
        lambda: _fitness_value(
            pm4py.fitness_token_based_replay(df, net, im, fm, **_KEYS)
        ),
        notifications,
        "Token-replay fitness",
    )

    precision = _safe(
        lambda: pm4py.precision_token_based_replay(df, net, im, fm, **_KEYS),
        notifications,
        "Precision",
    )

    fitness_aln: Optional[float] = None
    if n_cases <= max_cases_for_alignments:
        fitness_aln = _safe(
            lambda: _fitness_value(
                pm4py.fitness_alignments(df, net, im, fm, **_KEYS)
            ),
            notifications,
            "Alignment fitness",
        )
    else:
        notifications.append(
            f"Skipped alignments ({n_cases} cases > {max_cases_for_alignments}); "
            f"token-based fitness used."
        )

    generalization = _safe(
        lambda: _generalization(df, net, im, fm),
        notifications,
        "Generalization",
    )
    simplicity = _safe(
        lambda: _simplicity(net),
        notifications,
        "Simplicity",
    )

    mq = ModelQuality(
        algorithm=algorithm,
        fitness=_round(fitness),
        fitness_alignments=_round(fitness_aln),
        precision=_round(precision),
        generalization=_round(generalization),
        simplicity=_round(simplicity),
    )
    notifications.append(
        f"Conformance: fitness={mq.fitness}, precision={mq.precision}, "
        f"simplicity={mq.simplicity}."
    )
    return mq, notifications


def _generalization(df, net, im, fm) -> Optional[float]:
    from pm4py.algo.evaluation.generalization import algorithm as gen
    return gen.apply(df, net, im, fm)


def _simplicity(net) -> Optional[float]:
    from pm4py.algo.evaluation.simplicity import algorithm as simp
    return simp.apply(net)


def _round(v: Optional[float]) -> Optional[float]:
    return None if v is None else round(float(v), 4)
