"""
mining_engine.py — PM4Py-based Process Mining Engine
Layer A: Data Science & Process Discovery for the Consulting Process Analysis Platform

Provides deterministic processing functions for data alignment, process discovery,
performance diagnostics, and KPI computation using PM4Py + Pandas.
"""

import os
import logging
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

try:
    import pm4py
    from pm4py.objects.log.util import dataframe_utils
    from pm4py.objects.conversion.log import converter as log_converter
except ImportError:
    pm4py = None

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MANDATORY_COLUMNS = {"case_id", "activity", "timestamp"}

DEFAULT_COLUMN_MAPPING = {
    "case_id": "case:concept:name",
    "activity": "concept:name",
    "timestamp": "time:timestamp",
}


# ---------------------------------------------------------------------------
# 1. Data Alignment
# ---------------------------------------------------------------------------
def ingest_data(
    file_path: str,
    column_mapping: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Ingest .csv or .xes data streams and normalize into a Pandas DataFrame.

    Parameters
    ----------
    file_path : str
        Path to a .csv or .xes event log file.
    column_mapping : dict, optional
        Mapping from canonical keys ('case_id', 'activity', 'timestamp') to the
        actual column names present in the source file.  If *None* the PM4Py
        standard naming (``case:concept:name``, ``concept:name``,
        ``time:timestamp``) is assumed for XES files, while CSV files default
        to those same names unless overridden.

    Returns
    -------
    dict
        ``{"dataframe": pd.DataFrame, "notifications": list, "status": str}``
        — The normalised DataFrame (with PM4Py-standard column names), a list
        of human-readable notification messages, and an overall status flag
        (``"success"`` or ``"error"``).
    """
    result: Dict[str, Any] = {
        "dataframe": pd.DataFrame(),
        "notifications": [],
        "status": "error",
    }

    if pm4py is None:
        result["notifications"].append(
            "DEPENDENCY_ERROR: pm4py is not installed. Install with `pip install pm4py`."
        )
        return result

    if not os.path.isfile(file_path):
        result["notifications"].append(f"FILE_NOT_FOUND: '{file_path}' does not exist.")
        return result

    col_map = column_mapping or {}
    # Normalise to the three canonical keys
    col_map = {k: v for k, v in col_map.items() if k in MANDATORY_COLUMNS}

    ext = os.path.splitext(file_path)[1].lower()

    # ---- Load raw data ---------------------------------------------------
    try:
        if ext == ".xes":
            log = pm4py.read_xes(file_path)
            # Convert to DataFrame if returned as EventLog object
            if not isinstance(log, pd.DataFrame):
                df = log_converter.apply(
                    log, variant=log_converter.TO_DATA_FRAME
                )
            else:
                df = log
        elif ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            result["notifications"].append(
                f"UNSUPPORTED_FORMAT: '{ext}' is not supported. Use .csv or .xes."
            )
            return result
    except Exception as exc:
        result["notifications"].append(f"READ_ERROR: Failed to read '{file_path}': {exc}")
        return result

    # ---- Apply column mapping / rename -----------------------------------
    rename_dict: Dict[str, str] = {}
    for canonical, raw_name in col_map.items():
        if raw_name in df.columns and raw_name != DEFAULT_COLUMN_MAPPING.get(canonical, raw_name):
            rename_dict[raw_name] = DEFAULT_COLUMN_MAPPING[canonical]

    # If no mapping provided for CSV, attempt common auto-mappings
    if ext == ".csv" and not rename_dict:
        _auto_rename = {
            "case_id": "case:concept:name",
            "Case ID": "case:concept:name",
            "case:concept:name": "case:concept:name",
            "activity": "concept:name",
            "Activity": "concept:name",
            "concept:name": "concept:name",
            "timestamp": "time:timestamp",
            "Timestamp": "time:timestamp",
            "time:timestamp": "time:timestamp",
            "start_time": "time:timestamp",
            "StartTime": "time:timestamp",
        }
        for col in df.columns:
            if col in _auto_rename:
                rename_dict[col] = _auto_rename[col]

    if rename_dict:
        df = df.rename(columns=rename_dict)

    # ---- Validate mandatory columns --------------------------------------
    pm4py_cols = set(DEFAULT_COLUMN_MAPPING.values())
    missing = pm4py_cols - set(df.columns)
    if missing:
        result["notifications"].append(
            f"MISSING_COLUMNS: Required PM4Py columns not found: {missing}. "
            f"Provide a column_mapping to resolve."
        )
        return result

    n_original = len(df)

    # ---- Handle missing timestamps ---------------------------------------
    ts_col = "time:timestamp"
    df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")
    null_ts = df[ts_col].isna().sum()
    if null_ts:
        result["notifications"].append(
            f"NULL_TIMESTAMPS: {null_ts} rows have missing/invalid timestamps and will be dropped."
        )
        df = df.dropna(subset=[ts_col])

    # ---- Handle null activity names ---------------------------------------
    act_col = "concept:name"
    null_act = df[act_col].isna().sum()
    if null_act:
        result["notifications"].append(
            f"NULL_ACTIVITIES: {null_act} rows have null activity names and will be dropped."
        )
        df = df.dropna(subset=[act_col])

    # ---- Strip whitespace from activity & case columns --------------------
    df[act_col] = df[act_col].astype(str).str.strip()
    df["case:concept:name"] = df["case:concept:name"].astype(str).str.strip()

    # ---- Drop duplicate blank activities ---------------------------------
    blank_act = (df[act_col] == "") | (df[act_col].str.lower() == "nan")
    n_blank = blank_act.sum()
    if n_blank:
        result["notifications"].append(
            f"BLANK_ACTIVITIES: {n_blank} rows with blank/NaN activity names dropped."
        )
        df = df[~blank_act]

    # ---- Sort by timestamp -----------------------------------------------
    df = df.sort_values(by=[ts_col]).reset_index(drop=True)

    # ---- PM4Py format enforcement ----------------------------------------
    try:
        df = pm4py.format_dataframe(
            df,
            case_id="case:concept:name",
            activity_key="concept:name",
            timestamp_key="time:timestamp",
        )
    except Exception as exc:
        result["notifications"].append(
            f"FORMAT_WARNING: pm4py.format_dataframe failed ({exc}). "
            f"DataFrame kept but may lack PM4Py metadata."
        )

    n_final = len(df)
    dropped = n_original - n_final
    result["notifications"].append(
        f"INGEST_SUMMARY: Loaded {n_original} events; {dropped} dropped during cleaning; "
        f"{n_final} events retained across {df['case:concept:name'].nunique()} cases."
    )
    result["dataframe"] = df
    result["status"] = "success"
    return result


# ---------------------------------------------------------------------------
# 2. Heuristics Discovery
# ---------------------------------------------------------------------------
def discover_process(
    df: pd.DataFrame,
    output_path: str = "process_skeleton.png",
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Discover a Heuristics Net / Petri net from an event log.

    Parameters
    ----------
    df : pd.DataFrame
        A normalised event log DataFrame (as returned by :func:`ingest_data`).
    output_path : str
        File path (typically ``.png``) for the rendered process model image.
    parameters : dict, optional
        Keyword arguments forwarded to
        ``pm4py.discover_petri_net_heuristics()`` (e.g. ``dependency_threshold``,
        ``and_threshold``, ``loop_two_threshold``).

    Returns
    -------
    dict
        ``{"net": net, "im": im, "fm": fm, "image_path": str,
        "notifications": list, "status": str}``
    """
    result: Dict[str, Any] = {
        "net": None,
        "im": None,
        "fm": None,
        "image_path": None,
        "notifications": [],
        "status": "error",
    }

    if pm4py is None:
        result["notifications"].append("DEPENDENCY_ERROR: pm4py is not installed.")
        return result

    if df is None or df.empty:
        result["notifications"].append("EMPTY_DATAFRAME: Input DataFrame is empty.")
        return result

    # ---- Build kwargs for discover_petri_net_heuristics -------------------
    # pm4py 2.7.x accepts individual keyword arguments, not a parameters dict.
    valid_heuristics_kwargs = {
        "dependency_threshold",
        "and_threshold",
        "loop_two_threshold",
        "activity_key",
        "timestamp_key",
        "case_id_key",
    }
    kwargs: Dict[str, Any] = {
        "activity_key": "concept:name",
        "timestamp_key": "time:timestamp",
        "case_id_key": "case:concept:name",
    }
    if parameters:
        for k, v in parameters.items():
            if k in valid_heuristics_kwargs:
                kwargs[k] = v
            else:
                result["notifications"].append(
                    f"PARAM_WARNING: Unknown heuristic-miner parameter '{k}' ignored."
                )

    try:
        net, im, fm = pm4py.discover_petri_net_heuristics(df, **kwargs)
    except Exception as exc:
        result["notifications"].append(f"DISCOVERY_ERROR: {exc}")
        return result

    result["net"] = net
    result["im"] = im
    result["fm"] = fm
    result["notifications"].append("DISCOVERY_SUCCESS: Heuristics Miner Petri net discovered.")

    # ---- Visualization ----------------------------------------------------
    try:
        # Ensure output directory exists
        out_dir = os.path.dirname(output_path) or "."
        os.makedirs(out_dir, exist_ok=True)

        pm4py.save_vis_petri_net(net, im, fm, output_path)
        result["image_path"] = output_path
        result["notifications"].append(
            f"VISUALIZATION_SAVED: Process model rendered to '{output_path}'."
        )
    except Exception as exc:
        # Fallback: try viewing (which may render to a temp file)
        result["notifications"].append(
            f"VISUALIZATION_WARNING: Could not save image to '{output_path}': {exc}"
        )

    result["status"] = "success"
    return result


# ---------------------------------------------------------------------------
# 3. Performance Diagnostics
# ---------------------------------------------------------------------------
def compute_diagnostics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate execution latencies between activities and variant frequencies.

    Parameters
    ----------
    df : pd.DataFrame
        Normalised event log DataFrame.

    Returns
    -------
    dict
        ``{
            "activity_pair_latencies": list,   # sorted mean-duration pairs
            "bottlenecks": list,              # pairs exceeding 1 std above mean
            "variant_frequencies": dict,       # variant -> count
            "notifications": list,
            "status": str,
        }``
    """
    result: Dict[str, Any] = {
        "activity_pair_latencies": [],
        "bottlenecks": [],
        "variant_frequencies": {},
        "notifications": [],
        "status": "error",
    }

    if df is None or df.empty:
        result["notifications"].append("EMPTY_DATAFRAME: Input DataFrame is empty.")
        return result

    required = {"case:concept:name", "concept:name", "time:timestamp"}
    missing = required - set(df.columns)
    if missing:
        result["notifications"].append(
            f"MISSING_COLUMNS: DataFrame is missing required columns: {missing}."
        )
        return result

    # ---- Ensure timestamp dtype -------------------------------------------
    df = df.copy()
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], errors="coerce")
    df = df.dropna(subset=["time:timestamp"])
    df = df.sort_values(["case:concept:name", "time:timestamp"])

    # ---- Activity-pair latencies (per case, then averaged) ----------------
    latencies: Dict[Tuple[str, str], List[float]] = {}

    for case_id, case_events in df.groupby("case:concept:name"):
        events = case_events.sort_values("time:timestamp").reset_index(drop=True)
        for i in range(len(events) - 1):
            src = events.loc[i, "concept:name"]
            dst = events.loc[i + 1, "concept:name"]
            dur = (events.loc[i + 1, "time:timestamp"] - events.loc[i, "time:timestamp"]).total_seconds()
            key = (src, dst)
            latencies.setdefault(key, []).append(dur)

    # Compute mean latency per pair
    pair_latencies: List[Dict[str, Any]] = []
    for (src, dst), durs in latencies.items():
        mean_dur = sum(durs) / len(durs)
        pair_latencies.append(
            {
                "source": src,
                "target": dst,
                "mean_duration_seconds": round(mean_dur, 4),
                "occurrences": len(durs),
            }
        )

    # Sort descending by mean duration
    pair_latencies.sort(key=lambda x: x["mean_duration_seconds"], reverse=True)
    result["activity_pair_latencies"] = pair_latencies

    # ---- Bottleneck detection: > mean + 1std across all pair-means ---------
    if pair_latencies:
        durations = [p["mean_duration_seconds"] for p in pair_latencies]
        mean_all = sum(durations) / len(durations)
        std_all = (sum((d - mean_all) ** 2 for d in durations) / len(durations)) ** 0.5
        threshold = mean_all + std_all

        bottlenecks = [
            p for p in pair_latencies if p["mean_duration_seconds"] > threshold
        ]
        result["bottlenecks"] = bottlenecks
        result["notifications"].append(
            f"BOTTLENECK_SUMMARY: {len(bottlenecks)} activity pairs exceed "
            f"latency threshold ({threshold:.2f}s = mean+1σ)."
        )

    # ---- Variant frequencies ----------------------------------------------
    variants: Dict[str, int] = {}
    for case_id, case_events in df.groupby("case:concept:name"):
        activities = tuple(case_events.sort_values("time:timestamp")["concept:name"].tolist())
        variants[activities] = variants.get(activities, 0) + 1

    # Sort by frequency descending
    result["variant_frequencies"] = dict(
        sorted(variants.items(), key=lambda item: item[1], reverse=True)
    )
    result["notifications"].append(
        f"VARIANT_SUMMARY: {len(variants)} unique variants across "
        f"{df['case:concept:name'].nunique()} cases."
    )

    result["status"] = "success"
    return result


# ---------------------------------------------------------------------------
# 4. KPI Computation
# ---------------------------------------------------------------------------
def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute high-level process KPIs from the event log.

    Parameters
    ----------
    df : pd.DataFrame
        Normalised event log DataFrame.

    Returns
    -------
    dict
        ``{
            "total_case_throughput": int,
            "avg_case_cycle_time_seconds": float,
            "total_unique_variants": int,
            "notifications": list,
            "status": str,
        }``
    """
    result: Dict[str, Any] = {
        "total_case_throughput": 0,
        "avg_case_cycle_time_seconds": 0.0,
        "total_unique_variants": 0,
        "notifications": [],
        "status": "error",
    }

    if df is None or df.empty:
        result["notifications"].append("EMPTY_DATAFRAME: Input DataFrame is empty.")
        return result

    required = {"case:concept:name", "concept:name", "time:timestamp"}
    missing = required - set(df.columns)
    if missing:
        result["notifications"].append(
            f"MISSING_COLUMNS: DataFrame is missing required columns: {missing}."
        )
        return result

    df = df.copy()
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], errors="coerce")
    df = df.dropna(subset=["time:timestamp"])

    # ---- Total case throughput --------------------------------------------
    n_cases = df["case:concept:name"].nunique()
    result["total_case_throughput"] = n_cases

    # ---- Average case cycle time ------------------------------------------
    case_durations: List[float] = []
    for case_id, case_events in df.groupby("case:concept:name"):
        ts = case_events["time:timestamp"]
        if len(ts) >= 2:
            duration = (ts.max() - ts.min()).total_seconds()
            case_durations.append(duration)
        else:
            # Single-event case: cycle time is effectively 0
            case_durations.append(0.0)

    if case_durations:
        avg_cycle = sum(case_durations) / len(case_durations)
        result["avg_case_cycle_time_seconds"] = round(avg_cycle, 4)
    else:
        result["avg_case_cycle_time_seconds"] = 0.0

    # ---- Total unique variants --------------------------------------------
    variants: set = set()
    for case_id, case_events in df.groupby("case:concept:name"):
        variant = tuple(case_events.sort_values("time:timestamp")["concept:name"].tolist())
        variants.add(variant)
    result["total_unique_variants"] = len(variants)

    # ---- Attempt PM4Py native KPIs for cross-validation -------------------
    if pm4py is not None:
        try:
            pm4py_arrival_avg = pm4py.get_case_arrival_average(df)
            result["notifications"].append(
                f"PM4PY_CASE_ARRIVAL_AVG: {pm4py_arrival_avg}"
            )
        except Exception:
            result["notifications"].append(
                "PM4PY_ARRIVAL_WARNING: Could not compute case arrival average."
            )

        try:
            pm4py_cycle_time = pm4py.get_cycle_time(df)
            result["notifications"].append(
                f"PM4PY_CYCLE_TIME: {pm4py_cycle_time}"
            )
        except Exception:
            result["notifications"].append(
                "PM4PY_CYCLE_TIME_WARNING: Could not compute cycle time via pm4py."
            )

    result["notifications"].append(
        f"KPI_SUMMARY: {n_cases} cases, "
        f"avg cycle time = {result['avg_case_cycle_time_seconds']:.2f}s, "
        f"{len(variants)} unique variants."
    )

    result["status"] = "success"
    return result


# ---------------------------------------------------------------------------
# Convenience: run full pipeline
# ---------------------------------------------------------------------------
def run_pipeline(
    file_path: str,
    column_mapping: Optional[Dict[str, str]] = None,
    output_image: str = "process_skeleton.png",
) -> Dict[str, Any]:
    """Execute the full mining pipeline: ingest → discover → diagnose → KPIs.

    Returns
    -------
    dict
        Aggregated results keyed by stage name.
    """
    pipeline: Dict[str, Any] = {
        "ingest": None,
        "discovery": None,
        "diagnostics": None,
        "kpis": None,
        "status": "error",
    }

    ingest_result = ingest_data(file_path, column_mapping)
    pipeline["ingest"] = ingest_result

    if ingest_result["status"] != "success":
        pipeline["status"] = "error"
        return pipeline

    df = ingest_result["dataframe"]

    pipeline["discovery"] = discover_process(df, output_path=output_image)
    pipeline["diagnostics"] = compute_diagnostics(df)
    pipeline["kpis"] = compute_kpis(df)

    pipeline["status"] = "success"
    return pipeline
