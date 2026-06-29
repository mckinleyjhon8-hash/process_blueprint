"""
ingest.py — load and normalise an event log into a pm4py-standard DataFrame.

Accepts CSV or XES. Maps arbitrary columns to the canonical pm4py triple
(``case:concept:name``, ``concept:name``, ``time:timestamp``), cleans nulls,
strips whitespace, sorts by time, and formats for pm4py.

Returns ``(dataframe, notifications)``. Raises ``IngestError`` on fatal problems
so the engine can fail loudly rather than emit garbage facts.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    import pm4py
except ImportError:  # pragma: no cover
    pm4py = None

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"
CANONICAL = {CASE, ACT, TS}

# common raw column names → canonical, used when no explicit mapping is given
_AUTO_MAP = {
    "case_id": CASE, "case": CASE, "caseid": CASE, "case id": CASE, CASE: CASE,
    "activity": ACT, "event": ACT, "task": ACT, "concept:name": ACT, ACT: ACT,
    "timestamp": TS, "time": TS, "start_time": TS, "starttime": TS,
    "end_time": TS, "time:timestamp": TS, TS: TS,
}


class IngestError(Exception):
    """Raised when an event log cannot be loaded into a usable form."""


def ingest(
    file_path: str,
    column_mapping: Optional[Dict[str, str]] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """Load and normalise an event log.

    Parameters
    ----------
    file_path
        Path to a ``.csv`` or ``.xes`` file.
    column_mapping
        Optional ``{"case_id": <col>, "activity": <col>, "timestamp": <col>}``.

    Returns
    -------
    (DataFrame, notifications)
    """
    notifications: List[str] = []

    if pm4py is None:
        raise IngestError("pm4py is not installed (`pip install pm4py`).")
    if not os.path.isfile(file_path):
        raise IngestError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".xes":
        log = pm4py.read_xes(file_path)
        df = log if isinstance(log, pd.DataFrame) else pm4py.convert_to_dataframe(log)
    elif ext == ".csv":
        df = pd.read_csv(file_path)
    else:
        raise IngestError(f"Unsupported format '{ext}'. Use .csv or .xes.")

    df = _apply_mapping(df, column_mapping, notifications)

    missing = CANONICAL - set(df.columns)
    if missing:
        raise IngestError(
            f"Could not resolve required columns {missing}. "
            f"Provide an explicit column_mapping. Found columns: {list(df.columns)}"
        )

    n0 = len(df)

    # timestamps
    df[TS] = pd.to_datetime(df[TS], errors="coerce", utc=True)
    null_ts = int(df[TS].isna().sum())
    if null_ts:
        notifications.append(f"Dropped {null_ts} rows with invalid timestamps.")
        df = df.dropna(subset=[TS])

    # activity + case hygiene
    df[ACT] = df[ACT].astype(str).str.strip()
    df[CASE] = df[CASE].astype(str).str.strip()
    blank = (df[ACT] == "") | (df[ACT].str.lower() == "nan")
    if int(blank.sum()):
        notifications.append(f"Dropped {int(blank.sum())} rows with blank activity names.")
        df = df[~blank]

    if df.empty:
        raise IngestError("No valid events remain after cleaning.")

    df = df.sort_values(TS).reset_index(drop=True)

    try:
        df = pm4py.format_dataframe(
            df, case_id=CASE, activity_key=ACT, timestamp_key=TS
        )
    except Exception as exc:  # pragma: no cover - defensive
        notifications.append(f"format_dataframe warning: {exc}")

    dropped = n0 - len(df)
    notifications.append(
        f"Ingested {len(df)} events across {df[CASE].nunique()} cases "
        f"({dropped} rows dropped during cleaning)."
    )
    return df, notifications


def _apply_mapping(
    df: pd.DataFrame,
    column_mapping: Optional[Dict[str, str]],
    notifications: List[str],
) -> pd.DataFrame:
    rename: Dict[str, str] = {}

    if column_mapping:
        canon_keys = {"case_id": CASE, "activity": ACT, "timestamp": TS}
        for key, raw in column_mapping.items():
            if key in canon_keys and raw in df.columns:
                rename[raw] = canon_keys[key]
    else:
        for col in df.columns:
            lc = str(col).strip().lower()
            if lc in _AUTO_MAP and col not in CANONICAL:
                rename[col] = _AUTO_MAP[lc]

    if rename:
        df = df.rename(columns=rename)
        notifications.append(f"Mapped columns: {rename}")
    return df
