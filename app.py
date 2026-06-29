# requirements.txt: pm4py, pandas, streamlit, graphviz
"""
app.py — Streamlit UI/UX Pro Max Interactive Dashboard Portal
Layer B: The Interactive Portal for the Consulting Process Analysis Platform.

Provides a professional dark-themed consulting dashboard with:
  1. Clean Workspace Grid (file upload + column mapping)
  2. Process Anatomy Panel (Petri-net / process-tree rendering with zoom)
  3. KPI Metrics Ribbon (throughput, cycle time, variants)
  4. AI Executive Evaluation Brief Panel (expandable, styled)
  5. Error / Log Panel (notifications)

Flow:
  Upload CSV/XES  →  Map columns  →  Analyze
  →  mining_engine processes (ingest → discover → diagnose → KPIs)
  →  research_agent provides domain context + executive brief
  →  Dashboard renders KPIs, process map, executive brief
"""

from __future__ import annotations

import os
import sys
import tempfile
import traceback
from io import BytesIO
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

# Ensure the directory containing this file is importable (so that
# mining_engine.py and research_agent.py can be imported even when
# Streamlit is launched from a different working directory).
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

import mining_engine as me          # noqa: E402
import research_agent as ra         # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROCESS_TYPES = [
    "Procure-to-Pay",
    "Order-to-Cash",
    "Issue Resolution",
    "Employee Onboarding",
    "Invoice Processing",
    "Customer Service",
    "Change Management",
    "Risk Assessment",
]

SESSION_KEYS = {
    "df": "_df",
    "notifications": "_notifications",
    "kpis": "_kpis",
    "diagnostics": "_diagnostics",
    "discovery": "_discovery",
    "image_path": "_image_path",
    "brief_md": "_brief_md",
    "brief_html": "_brief_html",
    "research": "_research",
    "analyzed": "_analyzed",
    "raw_file_path": "_raw_file_path",
    "raw_file_name": "_raw_file_name",
    "raw_columns": "_raw_columns",
    "zoom": "_zoom",
}


# ---------------------------------------------------------------------------
# CSS — Dark Consulting Theme
# ---------------------------------------------------------------------------
DARK_THEME_CSS = """
<style>
/* ---------- Root / body ---------- */
.stApp {
    background: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #16213e;
    border-right: 1px solid #0f3460;
}
section[data-testid="stSidebar"] .stMarkdown, 
section[data-testid="stSidebar"] label {
    color: #c0c8d8 !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #00d2ff !important;
}

/* ---------- Headings ---------- */
h1, h2, h3 {
    color: #00d2ff !important;
    font-family: 'Inter', 'Segoe UI', sans-serif;
    letter-spacing: -0.02em;
}
h1 { font-weight: 800; }
h2 { font-weight: 700; border-bottom: 1px solid #0f3460; padding-bottom: 6px; }

/* ---------- Metric cards ---------- */
div[data-testid="stMetric"] {
    background: #16213e;
    border: 1px solid #0f3460;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.35);
}
div[data-testid="stMetric"] label {
    color: #8eaac4 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #00d2ff !important;
    font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
    font-size: 1.75rem !important;
    font-weight: 700;
}
div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {
    color: #e94560 !important;
}

/* ---------- Buttons ---------- */
.stButton > button {
    background: #0f3460 !important;
    color: #00d2ff !important;
    border: 1px solid #0f3460 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 8px 24px !important;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: #00d2ff !important;
    color: #1a1a2e !important;
    border-color: #00d2ff !important;
}

/* ---------- Select boxes / dropdowns ---------- */
.stSelectbox > div > div {
    background: #16213e !important;
    color: #e0e0e0 !important;
    border: 1px solid #0f3460 !important;
    border-radius: 6px !important;
}

/* ---------- File uploader ---------- */
.stFileUploader {
    border: 1px dashed #0f3460 !important;
    border-radius: 8px !important;
    background: #16213e !important;
    padding: 12px !important;
}

/* ---------- Expanders ---------- */
.streamlit-expanderHeader {
    background: #16213e !important;
    color: #00d2ff !important;
    border: 1px solid #0f3460 !important;
    border-radius: 8px !important;
    font-weight: 600;
}

/* ---------- Dataframe tables ---------- */
.dataframe {
    color: #e0e0e0;
}
.dataframe th {
    background: #0f3460 !important;
    color: #00d2ff !important;
}
.dataframe td {
    background: #16213e !important;
    color: #c8d0dc !important;
}

/* ---------- Alerts / notifications ---------- */
.stAlert {
    border-radius: 8px;
}
.stAlert > div {
    background: #16213e !important;
    color: #e0e0e0 !important;
    border-left: 3px solid #00d2ff !important;
}

/* ---------- Custom notification panel ---------- */
.notif-panel {
    background: #16213e;
    border: 1px solid #0f3460;
    border-radius: 10px;
    padding: 16px 18px;
    max-height: 300px;
    overflow-y: auto;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 0.85rem;
    line-height: 1.5;
}
.notif-panel .notif-item {
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(15,52,96,0.5);
}
.notif-panel .notif-tag {
    font-weight: 700;
}
.notif-panel .notif-info .notif-tag  { color: #00d2ff; }
.notif-panel .notif-warn .notif-tag  { color: #ffcc00; }
.notif-panel .notif-error .notif-tag { color: #e94560; }
.notif-panel .notif-success .notif-tag { color: #4ee07b; }

/* ---------- KPI ribbon wrapper ---------- */
.kpi-ribbon {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
}
.kpi-card {
    flex: 1;
    background: #16213e;
    border: 1px solid #0f3460;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.kpi-card .kpi-label {
    color: #8eaac4;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 8px;
}
.kpi-card .kpi-value {
    color: #00d2ff;
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 2rem;
    font-weight: 700;
}
.kpi-card .kpi-sub {
    color: #e94560;
    font-size: 0.75rem;
    margin-top: 4px;
}

/* ---------- Brief panel ---------- */
.brief-panel {
    background: #16213e;
    border: 1px solid #0f3460;
    border-radius: 12px;
    padding: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.brief-panel iframe {
    width: 100%;
    min-height: 600px;
    border: none;
    border-radius: 8px;
    background: #fff;
}

/* ---------- Process map container ---------- */
.process-map-container {
    background: #ffffff;
    border: 1px solid #0f3460;
    border-radius: 12px;
    padding: 12px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    overflow: auto;
}

/* ---------- Header banner ---------- */
.header-banner {
    background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
    border-bottom: 2px solid #00d2ff;
    padding: 18px 0;
    margin-bottom: 24px;
}
.header-banner h1 {
    margin: 0;
    padding: 0;
    border: none;
}
.header-banner .subtitle {
    color: #8eaac4;
    font-size: 0.9rem;
    margin-top: 4px;
}

/* ---------- Zoom slider styling ---------- */
.zoom-control .stSlider > div > div {
    background: #0f3460;
}
</style>
"""


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------
def init_session_state() -> None:
    """Initialise all session-state keys with sensible defaults."""
    for key, default in [
        ("df", None),
        ("notifications", []),
        ("kpis", None),
        ("diagnostics", None),
        ("discovery", None),
        ("image_path", None),
        ("brief_md", None),
        ("brief_html", None),
        ("research", None),
        ("analyzed", False),
        ("raw_file_path", None),
        ("raw_file_name", None),
        ("raw_columns", []),
        ("zoom", 1.0),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default


def reset_analysis() -> None:
    """Clear all analysis results (but keep the uploaded file)."""
    st.session_state["df"] = None
    st.session_state["notifications"] = []
    st.session_state["kpis"] = None
    st.session_state["diagnostics"] = None
    st.session_state["discovery"] = None
    st.session_state["image_path"] = None
    st.session_state["brief_md"] = None
    st.session_state["brief_html"] = None
    st.session_state["research"] = None
    st.session_state["analyzed"] = False


def add_notification(level: str, message: str) -> None:
    """Append a notification to session state.

    level: 'info' | 'warn' | 'error' | 'success'
    """
    st.session_state["notifications"].append({"level": level, "message": message})


# ---------------------------------------------------------------------------
# File handling
# ---------------------------------------------------------------------------
def save_uploaded_file(uploaded_file) -> str:
    """Save a Streamlit UploadedFile to a temp file and return its path."""
    suffix = os.path.splitext(uploaded_file.name)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.getvalue())
    tmp.close()
    return tmp.name


def peek_columns(file_path: str) -> List[str]:
    """Return column names from a CSV or XES file for mapping dropdowns."""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == ".csv":
            df = pd.read_csv(file_path, nrows=0)
            return list(df.columns)
        elif ext == ".xes":
            # Try pm4py first; fallback to manual line scan
            try:
                import pm4py  # noqa: WPS433
                log = pm4py.read_xes(file_path)
                if isinstance(log, pd.DataFrame):
                    return list(log.columns)
                # Convert event-log to df
                from pm4py.objects.conversion.log import converter as lc
                df = lc.apply(log, variant=lc.TO_DATA_FRAME)
                return list(df.columns)
            except Exception:
                # Manual fallback: parse XES attribute tags from first ~200 lines
                cols: set[str] = set()
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                    for _i, line in enumerate(fh):
                        if _i > 500:
                            break
                        import re
                        for m in re.finditer(r'string key="([^"]+)"', line):
                            cols.add(m.group(1))
                        for m in re.finditer(r'date key="([^"]+)"', line):
                            cols.add(m.group(1))
                        for m in re.finditer(r'float key="([^"]+)"', line):
                            cols.add(m.group(1))
                        for m in re.finditer(r'int key="([^"]+)"', line):
                            cols.add(m.group(1))
                return sorted(cols)
        else:
            return []
    except Exception as exc:
        add_notification("error", f"Failed to peek columns: {exc}")
        return []


def auto_detect_column(columns: List[str], candidates: List[str]) -> str:
    """Return the first candidate found in columns, else ''."""
    for c in candidates:
        for col in columns:
            if col == c or col.lower() == c.lower():
                return col
    return ""


# ---------------------------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------------------------
def run_analysis(
    file_path: str,
    column_mapping: Dict[str, str],
    process_type: str,
) -> None:
    """Execute the full pipeline: ingest → discover → diagnose → KPIs → research."""
    reset_analysis()

    # ---- 1. Ingest ----
    add_notification("info", f"→ Ingesting data from {os.path.basename(file_path)} …")
    ingest_result = me.ingest_data(file_path, column_mapping=column_mapping)
    _collect_notifications(ingest_result.get("notifications", []))

    if ingest_result["status"] != "success":
        add_notification("error", "Ingestion failed. See notifications above.")
        return

    df = ingest_result["dataframe"]
    st.session_state["df"] = df
    add_notification("success", f"✓ Ingested {len(df)} events from {df['case:concept:name'].nunique()} cases.")

    # ---- 2. Discover process model ----
    image_path = os.path.join(tempfile.gettempdir(), "process_skeleton.png")
    add_notification("info", "→ Discovering process model (Heuristics Miner) …")
    discovery_result = me.discover_process(df, output_path=image_path)
    _collect_notifications(discovery_result.get("notifications", []))
    st.session_state["discovery"] = discovery_result

    if discovery_result["status"] == "success" and discovery_result.get("image_path"):
        st.session_state["image_path"] = discovery_result["image_path"]
        add_notification("success", "✓ Process model discovered and rendered.")
    else:
        add_notification("warn", "Process discovery completed with warnings; image may be unavailable.")

    # ---- 3. Diagnostics ----
    add_notification("info", "→ Computing performance diagnostics …")
    diag_result = me.compute_diagnostics(df)
    _collect_notifications(diag_result.get("notifications", []))
    st.session_state["diagnostics"] = diag_result

    # ---- 4. KPIs ----
    add_notification("info", "→ Computing KPIs …")
    kpi_result = me.compute_kpis(df)
    _collect_notifications(kpi_result.get("notifications", []))
    st.session_state["kpis"] = kpi_result
    add_notification("success", "✓ KPIs computed.")

    # ---- 5. Research agent → executive brief ----
    add_notification("info", f"→ Researching domain context for '{process_type}' …")
    research_result = ra.research_process_type(process_type, use_web_fallback=True)
    st.session_state["research"] = research_result

    # Build pm4py_diagnostics dict for the brief generator
    kpis = kpi_result
    diag = diag_result
    cycle_s = kpis.get("avg_case_cycle_time_seconds", 0) or 0
    pm4py_diag: Dict[str, Any] = {
        "total_cases": kpis.get("total_case_throughput", 0),
        "variant_count": kpis.get("total_unique_variants", 0),
        "avg_cycle_time": cycle_s / 3600.0,  # hours
        "avg_cycle_time_hours": cycle_s / 3600.0,
        "bottleneck_activities": [
            b.get("source", "") + " → " + b.get("target", "")
            for b in (diag.get("bottlenecks") or [])
        ],
        "rework_rate_pct": 0,  # not directly computed; leave 0
        "automation_potential_pct": 0,
        "process_fit_pct": 0,
        "deviations": [],
    }

    brief_md = ra.generate_executive_brief(
        process_type,
        pm4py_diag,
        research_result.get("data") or {},
    )
    st.session_state["brief_md"] = brief_md

    try:
        brief_html = ra.format_brief_html(brief_md)
        st.session_state["brief_html"] = brief_html
    except Exception as exc:
        add_notification("warn", f"format_brief_html failed: {exc}")
        st.session_state["brief_html"] = None

    add_notification("success", "✓ AI Executive Evaluation Brief generated.")
    st.session_state["analyzed"] = True
    add_notification("info", "Analysis pipeline complete.")


def _collect_notifications(raw_notifs: List[str]) -> None:
    """Parse mining_engine notifications into the session-state panel."""
    for msg in raw_notifs or []:
        if msg.startswith("ERROR") or "ERROR" in msg or "FAILED" in msg.upper():
            add_notification("error", msg)
        elif "WARNING" in msg or "WARN" in msg.upper():
            add_notification("warn", msg)
        elif "SUCCESS" in msg.upper() or msg.startswith("✓"):
            add_notification("success", msg)
        else:
            add_notification("info", msg)


# ---------------------------------------------------------------------------
# Rendering — sub-components
# ---------------------------------------------------------------------------
def render_header() -> None:
    """Top banner."""
    st.markdown(
        """
        <div class="header-banner">
            <div style="max-width:1200px;margin:0 auto;padding:0 24px;">
                <h1>🔬 Consulting Process Analysis Platform</h1>
                <div class="subtitle">
                    Interactive Process Mining & AI Executive Evaluation Portal
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Sidebar: process type selector + info."""
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        st.markdown("---")

        st.markdown("#### Process Type")
        st.caption("Select the business process category for the research agent.")
        st.session_state["_selected_process"] = st.selectbox(
            "Process Type",
            PROCESS_TYPES,
            index=0,
            help="Used by the research agent to pull domain benchmarks and best practices.",
        )

        st.markdown("---")
        st.markdown("#### About")
        st.markdown(
            """
            <div style="font-size:0.8rem;color:#8eaac4;line-height:1.6;">
            <b>Layer B</b> — Interactive Portal<br/>
            Powered by <b>PM4Py</b> process-mining engine
            and the <b>AutoResearch</b> knowledge base.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        if st.button("🗑️ Reset Analysis", use_container_width=True):
            reset_analysis()
            st.rerun()


def render_workspace_grid() -> None:
    """
    1. Clean Workspace Grid — file uploader + column mapping selectors.
    """
    st.markdown("## 📂 Data Ingestion")
    st.markdown("Upload an event log (CSV or XES) and map its columns.")

    uploaded = st.file_uploader(
        "Upload CSV or XES",
        type=["csv", "xes"],
        label_visibility="collapsed",
    )

    col_a, col_b, col_c = st.columns([1, 1, 1])

    if uploaded is not None:
        # Save and peek columns (only when a new file is uploaded)
        if (
            st.session_state["raw_file_name"] != uploaded.name
            or st.session_state["raw_file_path"] is None
        ):
            path = save_uploaded_file(uploaded)
            st.session_state["raw_file_path"] = path
            st.session_state["raw_file_name"] = uploaded.name
            st.session_state["raw_columns"] = peek_columns(path)
            reset_analysis()
            add_notification("info", f"File uploaded: {uploaded.name} ({uploaded.size} bytes)")

        cols = st.session_state["raw_columns"]
        if not cols:
            st.warning("Could not read columns from this file. Ensure it is a valid CSV/XES.")
            return

        # Auto-detect defaults
        default_case = auto_detect_column(
            cols, ["case:concept:name", "case_id", "Case ID", "case", "Case"]
        )
        default_act = auto_detect_column(
            cols, ["concept:name", "activity", "Activity", "event", "Event"]
        )
        default_ts = auto_detect_column(
            cols, ["time:timestamp", "timestamp", "Timestamp", "time", "start_time"]
        )

        with col_a:
            case_col = st.selectbox("Case ID column", cols,
                                    index=cols.index(default_case) if default_case else 0)
        with col_b:
            act_col = st.selectbox("Activity column", cols,
                                   index=cols.index(default_act) if default_act else 0)
        with col_c:
            ts_col = st.selectbox("Timestamp column", cols,
                                  index=cols.index(default_ts) if default_ts else 0)

        # Preview
        with st.expander("📋 Data Preview (first 10 rows)"):
            try:
                if uploaded.name.lower().endswith(".csv"):
                    preview_df = pd.read_csv(st.session_state["raw_file_path"], nrows=10)
                else:
                    preview_df = pd.read_csv(st.session_state["raw_file_path"], nrows=10) if False else None
                if preview_df is not None:
                    st.dataframe(preview_df, use_container_width=True)
            except Exception:
                st.info("Preview not available for this file format.")

        # Analyze button
        st.markdown("")
        col_btn_l, col_btn_r = st.columns([1, 3])
        with col_btn_l:
            analyze = st.button("🚀 Analyze", type="primary", use_container_width=True)

        if analyze:
            mapping = {
                "case_id": case_col,
                "activity": act_col,
                "timestamp": ts_col,
            }
            process_type = st.session_state.get("_selected_process", PROCESS_TYPES[0])
            with st.spinner("Running analysis pipeline…"):
                run_analysis(
                    st.session_state["raw_file_path"],
                    mapping,
                    process_type,
                )
            st.rerun()
    else:
        st.info("👆 Upload a file to begin.")
        st.session_state["raw_file_path"] = None
        st.session_state["raw_file_name"] = None
        st.session_state["raw_columns"] = []


def render_kpi_ribbon() -> None:
    """
    3. KPI Metrics Ribbon — three metric cards displayed horizontally.
    """
    kpis: Optional[Dict[str, Any]] = st.session_state.get("kpis")
    if kpis is None or kpis.get("status") != "success":
        return

    throughput = kpis.get("total_case_throughput", 0)
    cycle_s = kpis.get("avg_case_cycle_time_seconds", 0) or 0
    variants = kpis.get("total_unique_variants", 0)

    # Format cycle time nicely
    if cycle_s >= 86400:
        cycle_str = f"{cycle_s / 86400:.2f} d"
    elif cycle_s >= 3600:
        cycle_str = f"{cycle_s / 3600:.2f} h"
    elif cycle_s >= 60:
        cycle_str = f"{cycle_s / 60:.2f} m"
    else:
        cycle_str = f"{cycle_s:.1f} s"

    # Use native st.metric in columns for the KPI ribbon
    st.markdown("## 📊 KPI Metrics")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(
            label="Total Case Throughput",
            value=f"{throughput:,}",
            help="Total number of unique process cases observed in the event log.",
        )
    with m2:
        st.metric(
            label="Avg Case Cycle Time",
            value=cycle_str,
            help="Average end-to-end cycle time (lead time) per case.",
        )
    with m3:
        st.metric(
            label="Unique Workflow Variants",
            value=f"{variants:,}",
            help="Number of distinct activity sequences (variants) — a complexity indicator.",
        )

    # Custom HTML ribbon (extra visual flair)
    st.markdown(
        f"""
        <div class="kpi-ribbon">
            <div class="kpi-card">
                <div class="kpi-label">Throughput</div>
                <div class="kpi-value">{throughput:,}</div>
                <div class="kpi-sub">cases processed</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Avg Cycle Time</div>
                <div class="kpi-value">{cycle_str}</div>
                <div class="kpi-sub">lead time per case</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Variants</div>
                <div class="kpi-value">{variants:,}</div>
                <div class="kpi-sub">complexity metric</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_process_anatomy() -> None:
    """
    2. Process Anatomy Panel — render the discovered process map with zoom.
    """
    if not st.session_state.get("analyzed"):
        return

    st.markdown("## 🗺️ Process Anatomy")

    image_path = st.session_state.get("image_path")
    if not image_path or not os.path.isfile(image_path):
        st.warning("Process map image is not available. Check the notification panel for details.")
        return

    # Zoom control using st.columns layout
    col_zoom, col_info = st.columns([3, 1])
    with col_zoom:
        zoom = st.slider(
            "🔎 Zoom level",
            min_value=0.25,
            max_value=3.0,
            value=st.session_state.get("zoom", 1.0),
            step=0.05,
            help="Adjust the zoom of the process map.",
        )
        st.session_state["zoom"] = zoom
    with col_info:
        discovery = st.session_state.get("discovery") or {}
        st.caption(f"Algorithm: Heuristics Miner")
        if discovery.get("net") is not None:
            st.caption("Petri net: ✓")

    # Render image with dynamic width based on zoom
    img_width = int(100 * zoom)  # percentage
    img_width = max(25, min(400, img_width))

    st.markdown('<div class="process-map-container">', unsafe_allow_html=True)
    try:
        st.image(image_path, width=min(1200, max(400, int(600 * zoom))))
    except Exception as exc:
        st.error(f"Failed to render process map: {exc}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Provide download link for the PNG
    with open(image_path, "rb") as fh:
        st.download_button(
            "📥 Download process map (PNG)",
            data=fh.read(),
            file_name="process_skeleton.png",
            mime="image/png",
        )


def render_executive_brief() -> None:
    """
    4. AI Executive Evaluation Brief Panel — styled expandable section.
    """
    if not st.session_state.get("analyzed"):
        return

    st.markdown("## 🤖 AI Executive Evaluation Brief")

    brief_html = st.session_state.get("brief_html")
    brief_md = st.session_state.get("brief_md")

    if not brief_md:
        st.info("No executive brief was generated.")
        return

    with st.expander("📄 View Executive Brief (click to expand)", expanded=True):
        if brief_html:
            # Render the HTML brief inside an iframe so its embedded CSS
            # doesn't clash with the Streamlit dark theme.
            import base64
            b64 = base64.b64encode(brief_html.encode("utf-8")).decode("utf-8")
            st.markdown(
                f'<div class="brief-panel">'
                f'<iframe src="data:text/html;base64,{b64}"></iframe>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            # Fallback: render raw markdown
            st.markdown(brief_md)

    # Also offer a download for the markdown brief
    st.download_button(
        "📥 Download brief (Markdown)",
        data=brief_md,
        file_name="executive_brief.md",
        mime="text/markdown",
    )


def render_diagnostics_detail() -> None:
    """Optional detail panel: bottleneck table + variant frequency."""
    diag: Optional[Dict[str, Any]] = st.session_state.get("diagnostics")
    if diag is None or diag.get("status") != "success":
        return

    with st.expander("🔬 Performance Diagnostics Detail", expanded=False):
        # Bottlenecks
        bottlenecks = diag.get("bottlenecks") or []
        if bottlenecks:
            st.markdown("### ⚠️ Detected Bottlenecks")
            bn_df = pd.DataFrame(bottlenecks)
            st.dataframe(bn_df, use_container_width=True)
        else:
            st.info("No significant bottlenecks detected (within mean+1σ).")

        # Variant frequencies (top 10)
        var_freq = diag.get("variant_frequencies") or {}
        if var_freq:
            st.markdown("### 🔀 Top 10 Workflow Variants")
            var_rows = []
            for i, (variant, count) in enumerate(list(var_freq.items())[:10]):
                var_rows.append({
                    "Rank": i + 1,
                    "Variant (activity sequence)": " → ".join(variant),
                    "Frequency": count,
                })
            st.dataframe(pd.DataFrame(var_rows), use_container_width=True)


def render_log_panel() -> None:
    """
    5. Error / Log Panel — clean notification area.
    """
    st.markdown("## 📋 Notifications & Logs")

    notifs: List[Dict[str, str]] = st.session_state.get("notifications") or []

    if not notifs:
        st.info("No notifications yet. Upload a file and run analysis to see logs here.")
        return

    # Build HTML notification panel
    items_html = []
    for n in notifs:
        level = n["level"]
        msg = n["message"]
        # Extract tag (first word before ':')
        if ":" in msg:
            tag, rest = msg.split(":", 1)
        else:
            tag, rest = level.upper(), msg
        items_html.append(
            f'<div class="notif-item notif-{level}">'
            f'<span class="notif-tag">[{tag.strip()}]</span> {rest.strip()}'
            f'</div>'
        )

    panel_html = (
        '<div class="notif-panel">'
        + "".join(items_html)
        + '</div>'
    )
    st.markdown(panel_html, unsafe_allow_html=True)

    # Clear button
    col_c1, col_c2 = st.columns([1, 4])
    with col_c1:
        if st.button("Clear notifications"):
            st.session_state["notifications"] = []
            st.rerun()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Consulting Process Analysis Platform",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject dark theme CSS
    st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

    init_session_state()
    render_header()
    render_sidebar()

    # Top-level layout
    # --- Workspace grid ---
    render_workspace_grid()

    # Divider
    st.markdown("---")

    # --- KPI ribbon ---
    render_kpi_ribbon()

    # --- Process anatomy + zoom ---
    render_process_anatomy()

    # --- Diagnostics detail ---
    render_diagnostics_detail()

    # --- Executive brief ---
    render_executive_brief()

    # --- Notification / log panel ---
    render_log_panel()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center;color:#5a6a80;font-size:0.8rem;padding:12px;">
        Consulting Process Analysis Platform · Layer B: Interactive Portal ·
        Powered by PM4Py + AutoResearch
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        st.error("An unexpected error occurred:")
        st.code(traceback.format_exc())
