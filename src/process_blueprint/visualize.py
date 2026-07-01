"""
visualize.py — render the discovered process model as a real image.

Uses pm4py + Graphviz to render the discovered Petri net (the genuine process
model). Graphviz's `dot` binary is required; this module locates it on common
Windows install paths if it isn't already on PATH, and degrades to None if it
truly can't be found, so callers can fall back gracefully.

pm4py visualisation stays isolated here behind `render_petri_net()`.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from typing import Optional

import pandas as pd

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"

_GRAPHVIZ_DIRS = [
    r"C:\Program Files\Graphviz\bin",
    r"C:\Program Files (x86)\Graphviz\bin",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Graphviz", "bin"),
    os.path.join(os.environ.get("PROGRAMFILES", ""), "Graphviz", "bin"),
]


def graphviz_available() -> bool:
    """True if `dot` is callable, adding a known install dir to PATH if needed."""
    if shutil.which("dot"):
        return True
    for d in _GRAPHVIZ_DIRS:
        if d and (os.path.isfile(os.path.join(d, "dot.exe")) or os.path.isfile(os.path.join(d, "dot"))):
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            return True
    return shutil.which("dot") is not None


def render_petri_net(
    df: pd.DataFrame, algorithm: str = "inductive", fmt: str = "svg"
) -> Optional[bytes]:
    """Discover and render a Petri net image; returns image bytes or None."""
    if not graphviz_available():
        return None
    try:
        import pm4py

        keys = dict(activity_key=ACT, timestamp_key=TS, case_id_key=CASE)
        if algorithm == "heuristics":
            net, im, fm = pm4py.discover_petri_net_heuristics(df, **keys)
        else:
            net, im, fm = pm4py.discover_petri_net_inductive(df, **keys)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix="." + fmt)
        tmp.close()
        try:
            pm4py.save_vis_petri_net(net, im, fm, tmp.name)
            with open(tmp.name, "rb") as fh:
                return fh.read()
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
    except Exception:
        return None
