"""
research_agent.py
=================

Layer C — Dynamic Context Gathering for the Consulting Process Analysis Platform.

This module adapts the AutoResearch / GitSkills autonomous-research-swarm pattern
(karpathy/autoresearch) as a lightweight, offline-first wrapper that pulls
reference materials dynamically based on the client process being analyzed.

It provides three capabilities:

1. **Domain Lookup** — `research_process_type(process_name)`
   Looks up best-practice operational metrics, common structural flaws, and
   framework targets for a specific type of business workflow, using a built-in
   knowledge base of common consulting process types (8+ entries) with an
   optional web-search fallback.

2. **Executive Brief Generation** — `generate_executive_brief(...)`
   Combines PM4py analytics with domain knowledge to produce a structured
   "AI Executive Evaluation Brief" in Markdown.

3. **Brief Formatter** — `format_brief_html(brief_markdown)`
   Converts the Markdown brief to HTML for rendering in the Streamlit dashboard.

Author : Layer C Subsystem
License: MIT
"""

from __future__ import annotations

import re
import json
import logging
import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Optional markdown dependency — fall back to a built-in converter if absent.
try:
    import markdown as _markdown_lib  # type: ignore

    _HAS_MARKDOWN = True
except Exception:  # pragma: no cover — optional dependency
    _HAS_MARKDOWN = False

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Built-in Knowledge Base
# ──────────────────────────────────────────────────────────────────────────────
# Each entry mirrors the schema requested:
#   avg_cycle_time_target  – target end-to-end cycle time (human-readable + hours)
#   typical_variants       – number of distinct process variants typically seen
#   common_bottlenecks     – recurring bottleneck activities
#   benchmark_kpis         – dict of KPI name -> benchmark value
#   structural_flaws       – known structural weaknesses in real-world deployments
#   best_practices         – recommended remediation / excellence practices

KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "Procure-to-Pay": {
        "avg_cycle_time_target": {"value": "5–7 days", "hours": 144},
        "typical_variants": "6–12",
        "common_bottlenecks": [
            "PO approval routing",
            "Supplier confirmation delay",
            "3-way match exceptions",
            "Invoice approval backlog",
        ],
        "benchmark_kpis": {
            "Touchless PO ratio": "≥ 70%",
            "First-pass match rate": "≥ 85%",
            "PO cycle time": "≤ 8 hours",
            "Invoice processing cost": "≤ $3 / invoice",
            "On-time delivery": "≥ 95%",
            "Maverick spend": "≤ 5%",
        },
        "structural_flaws": [
            "Excessive manual approval layers not correlated to PO value",
            "Re-keying between PR / PO / GRN / Invoice systems",
            "Missing supplier performance feedback loop",
            "Conformance-to-happy-path < 40% in legacy ERPs",
        ],
        "best_practices": [
            "Tiered approval thresholds based on spend bands",
            "Catalog-based purchasing to enable touchless PO",
            "Automated 3-way match with exception-only review",
            "Supplier scorecards with monthly reviews",
            "Source-to-contract integration for pricing accuracy",
        ],
    },
    "Order-to-Cash": {
        "avg_cycle_time_target": {"value": "1–3 days", "hours": 48},
        "typical_variants": "4–8",
        "common_bottlenecks": [
            "Credit hold decisions",
            "Order entry rework",
            "Pick-pack-ship coordination",
            "AR collection follow-up",
        ],
        "benchmark_kpis": {
            "Order accuracy": "≥ 98%",
            "On-time-in-full (OTIF)": "≥ 95%",
            "DSO (Days Sales Outstanding)": "≤ 35 days",
            "Perfect order rate": "≥ 90%",
            "Credit-to-order lead time": "≤ 4 hours",
            "Collection effectiveness index": "≥ 85%",
        },
        "structural_flaws": [
            "Fragmented credit-check logic across channels",
            "Manual allocation of constrained inventory",
            "No exception aggregation between fulfillment and billing",
            "Invoice disputes not routed back to root cause",
        ],
        "best_practices": [
            "Unified order capture across all channels",
            "Automated credit scoring with exception review",
            "ATP (Available-to-Promise) driven allocation",
            "Customer self-service portal for order status",
            "Aging-bucket-driven collection worklists",
        ],
    },
    "Issue Resolution": {
        "avg_cycle_time_target": {"value": "4–24 hours", "hours": 8},
        "typical_variants": "10–25",
        "common_bottlenecks": [
            "Triage and routing",
            "Escalation hand-offs",
            "Root-cause analysis",
            "Customer communication gaps",
        ],
        "benchmark_kpis": {
            "First Contact Resolution (FCR)": "≥ 70%",
            "Mean Time to Resolve (MTTR)": "≤ 8 hours",
            "Reopen rate": "≤ 10%",
            "SLA compliance": "≥ 95%",
            "CSAT": "≥ 4.2 / 5",
            "Backlog aging (open > 7d)": "≤ 5%",
        },
        "structural_flaws": [
            "Over-reliance on ad-hoc escalation chains",
            "No structured severity-to-SLA mapping",
            "Knowledge base under-utilised during triage",
            "Closure without RCA in > 30% of cases",
        ],
        "best_practices": [
            "Intelligent routing via classification models",
            "Severity-based SLA matrices",
            "Mandatory RCA for P1/P2 issues",
            "Living knowledge base with contribution incentives",
            "Proactive customer notification at milestones",
        ],
    },
    "Employee Onboarding": {
        "avg_cycle_time_target": {"value": "3–5 days", "hours": 72},
        "typical_variants": "5–10",
        "common_bottlenecks": [
            "IT provisioning (laptop, accounts)",
            "Badge / facility access setup",
            "Manager availability for orientation",
            "HR document collection",
        ],
        "benchmark_kpis": {
            "Time-to-Productivity": "≤ 14 days",
            "Onboarding completion rate": "≥ 98%",
            "New-hire satisfaction": "≥ 4.3 / 5",
            "Day-1 readiness": "≥ 90%",
            "Probation pass rate": "≥ 92%",
            "IT provisioning lead time": "≤ 24 hours",
        },
        "structural_flaws": [
            "Parallel tasks without explicit join dependencies",
            "No clear process owner across HR / IT / Facilities",
            "Manual document collection prone to rework loops",
            "Onboarding plan not customised by role/level",
        ],
        "best_practices": [
            "Pre-boarding digital workflow triggered on offer accept",
            "Role-based onboarding templates",
            "Cross-functional SLA contract (HR/IT/Facilities)",
            "Buddy system + 30/60/90 check-ins",
            "Automated IT provisioning via IAM integration",
        ],
    },
    "Invoice Processing": {
        "avg_cycle_time_target": {"value": "2–4 days", "hours": 72},
        "typical_variants": "5–9",
        "common_bottlenecks": [
            "Manual data entry",
            "Exception handling (PO mismatch / missing GRN)",
            "Approval routing",
            "Posting to ERP",
        ],
        "benchmark_kpis": {
            "Straight-through processing rate": "≥ 75%",
            "Cost per invoice": "≤ $3",
            "Invoice cycle time": "≤ 48 hours",
            "Duplicate detection rate": "100%",
            "Exception rate": "≤ 15%",
            "Early-payment discount capture": "≥ 80%",
        },
        "structural_flaws": [
            "No OCR/automation — manual entry dominates",
            "Exceptions handled in silo without feedback to procurement",
            "Approval matrix too rigid / too flat",
            "No separation of standard vs. exception paths",
        ],
        "best_practices": [
            "Invoice capture automation (OCR + ML classification)",
            "Rules-based exception routing with targeted reviewer pools",
            "Dynamic approval thresholds",
            "Supplier portal for invoice submission",
            "Continuous feedback loop to reduce upstream errors",
        ],
    },
    "Customer Service": {
        "avg_cycle_time_target": {"value": "5–15 minutes (first contact)", "hours": 0.2},
        "typical_variants": "15–40",
        "common_bottlenecks": [
            "IVR / routing configuration",
            "Agent availability",
            "Knowledge lookup during call",
            "After-call work / wrap-up",
        ],
        "benchmark_kpis": {
            "Average Handle Time (AHT)": "≤ 6 minutes",
            "First Contact Resolution (FCR)": "≥ 75%",
            "Service Level (80/20)": "≥ 80%",
            "CSAT": "≥ 4.3 / 5",
            "Abandon rate": "≤ 5%",
            "Agent utilization": "70–85%",
        },
        "structural_flaws": [
            "Over-segmentation of queues increasing transfers",
            "Knowledge fragmented across systems",
            "Wrap-up not standardized → data quality issues",
            "No proactive outreach despite outbound capability",
        ],
        "best_practices": [
            "Skills-based routing with dynamic queue assignment",
            "Unified agent desktop with embedded knowledge",
            "Structured wrap-up codes with validation",
            "Proactive contact for high-risk cases",
            "Quality monitoring with coaching loops",
        ],
    },
    "Change Management": {
        "avg_cycle_time_target": {"value": "1–10 days (by risk tier)", "hours": 48},
        "typical_variants": "3–7",
        "common_bottlenecks": [
            "CAB (Change Advisory Board) scheduling",
            "Risk assessment completeness",
            "Implementation window availability",
            "Post-implementation review (PIR) backlog",
        ],
        "benchmark_kpis": {
            "Change success rate": "≥ 95%",
            "Emergency change ratio": "≤ 10%",
            "CAB turnaround": "≤ 48 hours",
            "Change lead time": "≤ 5 days",
            "PIR completion for failed changes": "100%",
            "Unauthorized change rate": "0%",
        },
        "structural_flaws": [
            "CAB as bottleneck rather than enabler",
            "Risk scoring subjective / inconsistent",
            "No link to release and deployment calendar",
            "PIR skipped for minor-severity failures",
        ],
        "best_practices": [
            "Standard change pre-approval templates",
            "Automated risk scoring from CMDB data",
            "Integrated change–release–deploy pipeline",
            "Mandatory PIR for all Sev-1/Sev-2 changes",
            "Trend analysis feeding back into change policy",
        ],
    },
    "Risk Assessment": {
        "avg_cycle_time_target": {"value": "5–15 days", "hours": 240},
        "typical_variants": "4–8",
        "common_bottlenecks": [
            "Data gathering from disparate sources",
            "Risk scoring consensus",
            "Mitigation plan approval",
            "Monitoring cadence drift",
        ],
        "benchmark_kpis": {
            "Assessment cycle time": "≤ 10 days",
            "Risk register coverage": "100% of in-scope assets",
            "Mitigation plan on-time completion": "≥ 85%",
            "Residual risk reduction": "≥ 20% YoY",
            "Assessment frequency adherence": "≥ 95%",
            "Risk events predicted pre-occurrence": "≥ 30%",
        },
        "structural_flaws": [
            "Manual spreadsheets with no version control",
            "Scoring rubric not standardized across assessors",
            "No continuous monitoring — point-in-time snapshots only",
            "Mitigation ownership ambiguous",
        ],
        "best_practices": [
            "Centralized GRC platform with audit trail",
            "Quantified risk scoring (likelihood × impact) with calibration",
            "Continuous risk monitoring via telemetry integration",
            "Clear RACI for each mitigation action",
            "Risk appetite statements linked to scoring thresholds",
        ],
    },
}

# Normalised lookup index — allows case / hyphen / whitespace insensitive match.
_LOOKUP_INDEX: Dict[str, str] = {
    k.lower().replace("-", " ").replace("_", " ").strip(): k
    for k in KNOWLEDGE_BASE
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _normalise(name: str) -> str:
    return name.lower().replace("-", " ").replace("_", " ").strip()


@dataclass
class BriefResult:
    """Container for a generated executive brief."""

    markdown: str
    html: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Domain Lookup
# ──────────────────────────────────────────────────────────────────────────────


def research_process_type(
    process_name: str, use_web_fallback: bool = True
) -> Dict[str, Any]:
    """Look up best-practice knowledge for a given business process type.

    Parameters
    ----------
    process_name : str
        Human-readable process name, e.g. "Procure-to-Pay", "Order-to-Cash".
    use_web_fallback : bool, default True
        If the process is not in the built-in knowledge base, attempt a
        lightweight web search to assemble a synthetic entry.

    Returns
    -------
    dict
        A dictionary with keys: ``process_type``, ``found`` (bool),
        ``source`` ("knowledge_base" | "web" | "unknown"),
        ``data`` (the entry dict), and optionally ``search_query``.
    """
    key = _LOOKUP_INDEX.get(_normalise(process_name))

    if key:
        logger.info("Knowledge-base hit for '%s' → '%s'", process_name, key)
        return {
            "process_type": key,
            "found": True,
            "source": "knowledge_base",
            "data": KNOWLEDGE_BASE[key],
        }

    # ── Fallback: web search ──────────────────────────────────────────────
    if use_web_fallback:
        try:
            synthetic = _web_fallback(process_name)
            if synthetic:
                return synthetic
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("Web fallback failed for '%s': %s", process_name, exc)

    # ── Last resort: return a stub ─────────────────────────────────────────
    logger.warning("No knowledge found for '%s'; returning stub entry.", process_name)
    return {
        "process_type": process_name,
        "found": False,
        "source": "unknown",
        "data": _stub_entry(process_name),
    }


def _web_fallback(process_name: str) -> Optional[Dict[str, Any]]:
    """Attempt a lightweight web search to build a synthetic knowledge entry.

    Uses the ``requests`` library if available and queries a public search
    endpoint.  This is intentionally conservative — it degrades gracefully
    when offline.  The resulting entry is marked ``source="web"`` and flagged
    as lower-confidence.
    """
    try:
        import requests  # type: ignore
    except Exception:
        logger.info("requests not available — skipping web fallback.")
        return None

    query = (
        f"{process_name} process best practice KPI benchmark cycle time bottlenecks"
    )
    search_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": process_name,
        "format": "json",
        "srlimit": 3,
    }

    try:
        resp = requests.get(search_url, params=params, timeout=8)
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
    except Exception as exc:
        logger.info("Web search request failed: %s", exc)
        return None

    # Build a synthetic entry using whatever we can glean.
    snippets = " ".join(r.get("snippet", "") for r in results)
    # Strip HTML tags from snippets.
    snippets = re.sub(r"<[^>]+>", " ", snippets)

    # Heuristic extraction of numeric benchmarks from snippets.
    cycle_hours = _extract_number(snippets, default=120)
    variants = "unknown"

    return {
        "process_type": process_name,
        "found": True,
        "source": "web",
        "search_query": query,
        "data": {
            "avg_cycle_time_target": {
                "value": f"~{cycle_hours} hours (web estimate)",
                "hours": cycle_hours,
            },
            "typical_variants": variants,
            "common_bottlenecks": [
                "Insufficient data — verify with domain expert",
                "Likely approval / handoff delays (generic)",
            ],
            "benchmark_kpis": {
                "Cycle time": f"≤ {cycle_hours} hours (web estimate)",
                "Note": "Benchmarks derived from public search — validate before use.",
            },
            "structural_flaws": [
                "Not yet assessed — web-derived entry",
            ],
            "best_practices": [
                "Conduct focused process discovery before benchmarking",
                "Engage SME for domain-specific benchmarks",
            ],
        },
        "confidence": "low",
    }


def _extract_number(text: str, default: int = 0) -> int:
    """Extract the first integer from *text*, or return *default*."""
    match = re.search(r"\b(\d+)\b", text)
    return int(match.group(1)) if match else default


def _stub_entry(process_name: str) -> Dict[str, Any]:
    """Return a minimal placeholder entry for an unknown process type."""
    return {
        "avg_cycle_time_target": {"value": "unknown", "hours": 0},
        "typical_variants": "unknown",
        "common_bottlenecks": ["Not yet mapped"],
        "benchmark_kpis": {"Cycle time": "TBD"},
        "structural_flaws": ["Not yet assessed"],
        "best_practices": ["Define process scope and re-run analysis"],
    }


# ──────────────────────────────────────────────────────────────────────────────
# 2. Executive Brief Generation
# ──────────────────────────────────────────────────────────────────────────────


def generate_executive_brief(
    process_name: str,
    pm4py_diagnostics: Dict[str, Any],
    domain_knowledge: Dict[str, Any],
) -> str:
    """Generate a structured Markdown "AI Executive Evaluation Brief".

    Parameters
    ----------
    process_name : str
        The business process under analysis.
    pm4py_diagnostics : dict
        Output from the PM4py analytics layer (Layer B).  Expected keys
        (all optional but recommended): ``variant_count``, ``total_cases``,
        ``avg_cycle_time_hours``, ``bottleneck_activities``, ``conformance``,
        ``fitness``, ``precision``, ``generalization``, ``simplicity``,
        ``deviations``, ``process_model_summary``.
    domain_knowledge : dict
        The ``data`` sub-dict returned by :func:`research_process_type`.

    Returns
    -------
    str
        Markdown-formatted executive brief.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ptype = domain_knowledge.get("process_type", process_name) if isinstance(
        domain_knowledge, dict
    ) and "process_type" in domain_knowledge else process_name

    # When domain_knowledge is the full research_process_type response, extract .data
    if isinstance(domain_knowledge, dict) and "data" in domain_knowledge:
        dk = domain_knowledge["data"]
    else:
        dk = domain_knowledge  # already the inner data dict

    # ── Pull PM4py values with safe defaults ───────────────────────────────
    variant_count = pm4py_diagnostics.get("variant_count", "N/A")
    total_cases = pm4py_diagnostics.get("total_cases", "N/A")
    avg_cycle = pm4py_diagnostics.get("avg_cycle_time_hours", "N/A")
    bottlenecks = pm4py_diagnostics.get("bottleneck_activities", [])
    fitness = pm4py_diagnostics.get("fitness")
    precision = pm4py_diagnostics.get("precision")
    generalization = pm4py_diagnostics.get("generalization")
    simplicity = pm4py_diagnostics.get("simplicity")
    deviations = pm4py_diagnostics.get("deviations", [])
    model_summary = pm4py_diagnostics.get("process_model_summary", "")

    # ── Domain values ──────────────────────────────────────────────────────
    target_cycle = dk.get("avg_cycle_time_target", {})
    target_val = target_cycle.get("value", "N/A") if isinstance(target_cycle, dict) else str(target_cycle)
    target_hours = target_cycle.get("hours", 0) if isinstance(target_cycle, dict) else 0
    typical_variants = dk.get("typical_variants", "N/A")
    dom_bottlenecks = dk.get("common_bottlenecks", [])
    kpis = dk.get("benchmark_kpis", {})
    flaws = dk.get("structural_flaws", [])
    practices = dk.get("best_practices", [])

    # ── Compute Process Health Score (0–100) ───────────────────────────────
    health_score, health_grade = _compute_health_score(
        pm4py_diagnostics, avg_cycle, target_hours
    )

    # ── Build sections ─────────────────────────────────────────────────────
    md_lines: List[str] = []
    md_lines.append(f"# AI Executive Evaluation Brief")
    md_lines.append("")
    md_lines.append(f"**Process:** {ptype}  ")
    md_lines.append(f"**Generated:** {now}  ")
    md_lines.append(f"**Analysis Engine:** PM4py × AutoResearch Domain Intelligence")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # ── Executive Summary ──────────────────────────────────────────────────
    md_lines.append("## 1. Executive Summary")
    md_lines.append("")
    summary = _exec_summary(
        ptype, total_cases, variant_count, avg_cycle, target_val, health_score, health_grade
    )
    md_lines.append(summary)
    md_lines.append("")

    # ── Process Health Score ────────────────────────────────────────────────
    md_lines.append("## 2. Process Health Score")
    md_lines.append("")
    md_lines.append(f"| Metric | Value |")
    md_lines.append(f"|---|---|")
    md_lines.append(f"| **Overall Score** | **{health_score}/100 ({health_grade})** |")
    if fitness is not None:
        md_lines.append(f"| Fitness | {fitness:.3f} |" if isinstance(fitness, float) else f"| Fitness | {fitness} |")
    if precision is not None:
        md_lines.append(f"| Precision | {precision:.3f} |" if isinstance(precision, float) else f"| Precision | {precision} |")
    if generalization is not None:
        md_lines.append(f"| Generalization | {generalization:.3f} |" if isinstance(generalization, float) else f"| Generalization | {generalization} |")
    if simplicity is not None:
        md_lines.append(f"| Simplicity | {simplicity:.3f} |" if isinstance(simplicity, float) else f"| Simplicity | {simplicity} |")
    md_lines.append(f"| Cases Analyzed | {total_cases} |")
    md_lines.append(f"| Variants Detected | {variant_count} |")
    md_lines.append("")

    # ── Benchmark Comparison ───────────────────────────────────────────────
    md_lines.append("## 3. Benchmark Comparison")
    md_lines.append("")
    md_lines.append(f"| KPI | Client Actual | Domain Benchmark | Gap |")
    md_lines.append(f"|---|---|---|---|")
    # Cycle time row
    actual_cycle = f"{avg_cycle} h" if isinstance(avg_cycle, (int, float)) else str(avg_cycle)
    bench_cycle = f"{target_val}"
    gap = _gap_label(avg_cycle, target_hours)
    md_lines.append(f"| Avg. Cycle Time | {actual_cycle} | {bench_cycle} | {gap} |")
    # Variants row
    md_lines.append(f"| Process Variants | {variant_count} | {typical_variants} | {_variant_gap(variant_count, typical_variants)} |")
    # Additional KPI rows
    for kpi_name, kpi_bench in kpis.items():
        md_lines.append(f"| {kpi_name} | — (not measured) | {kpi_bench} | TBD |")
    md_lines.append("")

    # ── Key Findings ────────────────────────────────────────────────────────
    md_lines.append("## 4. Key Findings")
    md_lines.append("")
    findings = _key_findings(
        pm4py_diagnostics, bottlenecks, dom_bottlenecks, flaws, deviations
    )
    for f in findings:
        md_lines.append(f"- {f}")
    md_lines.append("")

    # ── Risk Indicators ─────────────────────────────────────────────────────
    md_lines.append("## 5. Risk Indicators")
    md_lines.append("")
    risks = _risk_indicators(
        pm4py_diagnostics, bottlenecks, dom_bottlenecks, flaws, deviations
    )
    if risks:
        for r in risks:
            md_lines.append(f"- ⚠️ {r}")
    else:
        md_lines.append("- No critical risk indicators detected.")
    md_lines.append("")

    # ── Recommendations ────────────────────────────────────────────────────
    md_lines.append("## 6. Recommendations")
    md_lines.append("")
    recs = _recommendations(
        bottlenecks, dom_bottlenecks, flaws, practices, deviations, health_score
    )
    for i, rec in enumerate(recs, 1):
        md_lines.append(f"{i}. {rec}")
    md_lines.append("")

    # ── Footer ──────────────────────────────────────────────────────────────
    md_lines.append("---")
    md_lines.append("")
    md_lines.append(
        "*This brief was auto-generated by the Consulting Process Analysis Platform "
        "combining PM4py process mining diagnostics with domain knowledge from the "
        "AutoResearch knowledge base. Scores and benchmarks are indicative and should "
        "be validated with subject-matter experts before executive action.*"
    )
    md_lines.append("")

    return "\n".join(md_lines)


def _compute_health_score(
    pm4py_diagnostics: Dict[str, Any], avg_cycle: Any, target_hours: float
) -> Tuple[int, str]:
    """Compute a 0–100 health score from available diagnostics.

    Weighting (normalised to 100 when components present):
      Fitness        30 pts
      Precision      20 pts
      Generalization 15 pts
      Simplicity     10 pts
      Cycle time     25 pts
    """
    score = 0.0
    max_score = 0.0

    fitness = pm4py_diagnostics.get("fitness")
    precision = pm4py_diagnostics.get("precision")
    generalization = pm4py_diagnostics.get("generalization")
    simplicity = pm4py_diagnostics.get("simplicity")

    def _val(v, weight):
        nonlocal score, max_score
        max_score += weight
        if v is not None and isinstance(v, (int, float)):
            score += min(max(v, 0.0), 1.0) * weight

    _val(fitness, 30)
    _val(precision, 20)
    _val(generalization, 15)
    _val(simplicity, 10)

    # Cycle time component
    max_score += 25
    if (
        isinstance(avg_cycle, (int, float))
        and target_hours
        and target_hours > 0
    ):
        ratio = target_hours / max(avg_cycle, 0.01)
        # If actual ≤ target → full marks; if actual is 2× target → 0 marks.
        ct_score = max(0.0, min(ratio, 1.0)) * 25
        score += ct_score

    if max_score == 0:
        return 50, "C (Insufficient Data)"

    normalised = round((score / max_score) * 100)

    if normalised >= 85:
        grade = "A (Excellent)"
    elif normalised >= 70:
        grade = "B (Good)"
    elif normalised >= 55:
        grade = "C (Moderate)"
    elif normalised >= 40:
        grade = "D (Poor)"
    else:
        grade = "F (Critical)"
    return normalised, grade


def _gap_label(actual: Any, target: float) -> str:
    if not isinstance(actual, (int, float)) or not target or target <= 0:
        return "TBD"
    pct = ((actual - target) / target) * 100
    if pct <= 0:
        return f"✅ On target ({pct:+.1f}%)"
    elif pct <= 20:
        return f"⚠️ Slight overrun (+{pct:.1f}%)"
    elif pct <= 50:
        return f"🔴 Moderate overrun (+{pct:.1f}%)"
    else:
        return f"🛑 Significant overrun (+{pct:.1f}%)"


def _variant_gap(actual: Any, typical: Any) -> str:
    """Rough gap assessment for variant count."""
    if not isinstance(actual, (int, float)):
        return "TBD"
    # Try to parse a range like "6–12" or a single number.
    try:
        nums = re.findall(r"\d+", str(typical))
        if len(nums) >= 2:
            lo, hi = int(nums[0]), int(nums[1])
        elif len(nums) == 1:
            lo = hi = int(nums[0])
        else:
            return "TBD"
    except Exception:
        return "TBD"

    if actual <= lo:
        return "✅ Within range"
    elif actual <= hi:
        return "⚠️ Upper range"
    elif actual <= hi * 1.5:
        return "🔴 Above range"
    else:
        return "🛑 Excessive variants"


def _exec_summary(
    ptype: str,
    total_cases: Any,
    variant_count: Any,
    avg_cycle: Any,
    target_val: Any,
    health_score: int,
    health_grade: str,
) -> str:
    lines = [
        f"This brief presents an AI-driven evaluation of the **{ptype}** process, "
        f"analysing **{total_cases}** cases across **{variant_count}** process variants "
        f"using event-log data processed through PM4py process-mining algorithms.",
        "",
        f"The process achieved an overall health score of **{health_score}/100** "
        f"(**{health_grade}**).",
        "",
    ]
    if isinstance(avg_cycle, (int, float)):
        lines.append(
            f"The average observed cycle time is **{avg_cycle} hours**, "
            f"compared to a domain benchmark of **{target_val}**."
        )
    else:
        lines.append(
            "Cycle time could not be reliably measured from the available event log; "
            "this should be prioritised in the next analysis pass."
        )
    lines.append("")
    lines.append(
        "The following sections provide benchmark comparisons, key findings, "
        "risk indicators, and actionable recommendations."
    )
    return "\n".join(lines)


def _key_findings(
    pm4py_diagnostics: Dict[str, Any],
    bottlenecks: List[Any],
    dom_bottlenecks: List[str],
    flaws: List[str],
    deviations: List[Any],
) -> List[str]:
    findings: List[str] = []

    fitness = pm4py_diagnostics.get("fitness")
    if isinstance(fitness, float) and fitness < 0.85:
        findings.append(
            f"Conformance fitness is **{fitness:.3f}**, indicating that a significant "
            f"share of observed traces deviate from the reference model."
        )
    elif isinstance(fitness, float) and fitness >= 0.95:
        findings.append(
            f"Conformance fitness is **{fitness:.3f}**, indicating strong alignment "
            f"between observed and modelled behaviour."
        )

    precision = pm4py_diagnostics.get("precision")
    if isinstance(precision, float) and precision < 0.7:
        findings.append(
            f"Precision is **{precision:.3f}**, suggesting the model allows behaviour "
            f"not observed in the log — potential under-specification."
        )

    # Bottleneck overlap
    bn_lower = {str(b).lower() for b in bottlenecks}
    dom_lower = {str(b).lower() for b in dom_bottlenecks}
    overlapping = bn_lower & dom_lower
    if overlapping:
        findings.append(
            f"Observed bottlenecks match known domain bottlenecks: "
            f"{', '.join(sorted(overlapping))}."
        )
    if bn_lower - dom_lower:
        findings.append(
            f"Novel bottlenecks not in the domain reference: "
            f"{', '.join(sorted(bn_lower - dom_lower))}."
        )

    if deviations:
        findings.append(
            f"**{len(deviations)}** conformance deviations were detected, "
            f"indicating process variability beyond the reference model."
        )

    if flaws:
        top_flaw = flaws[0] if isinstance(flaws[0], str) else str(flaws[0])
        findings.append(f"Known structural flaw relevant here: {top_flaw}.")

    if not findings:
        findings.append(
            "No significant anomalies detected relative to domain benchmarks. "
            "Process performance appears nominal."
        )

    return findings


def _risk_indicators(
    pm4py_diagnostics: Dict[str, Any],
    bottlenecks: List[Any],
    dom_bottlenecks: List[str],
    flaws: List[str],
    deviations: List[Any],
) -> List[str]:
    risks: List[str] = []

    fitness = pm4py_diagnostics.get("fitness")
    if isinstance(fitness, float) and fitness < 0.75:
        risks.append(
            f"Low conformance fitness ({fitness:.3f}) — high risk of uncontrolled process drift."
        )

    precision = pm4py_diagnostics.get("precision")
    if isinstance(precision, float) and precision < 0.6:
        risks.append(
            f"Low precision ({precision:.3f}) — model permits excessive unobserved behaviour."
        )

    variant_count = pm4py_diagnostics.get("variant_count")
    if isinstance(variant_count, (int, float)) and variant_count > 20:
        risks.append(
            f"High variant count ({variant_count}) — process fragmentation risk, "
            f"indicating lack of standardisation."
        )

    if len(bottlenecks) > 3:
        risks.append(
            f"Multiple bottleneck activities ({len(bottlenecks)}) detected — "
            f"capacity-constraint risk across several stages."
        )

    if len(deviations) > 10:
        risks.append(
            f"Elevated deviation count ({len(deviations)}) — control-gap risk "
            f"requiring governance review."
        )

    for flaw in flaws[:3]:
        risks.append(f"Structural flaw: {flaw}")

    return risks


def _recommendations(
    bottlenecks: List[Any],
    dom_bottlenecks: List[str],
    flaws: List[str],
    practices: List[str],
    deviations: List[Any],
    health_score: int,
) -> List[str]:
    recs: List[str] = []

    # 1 — Bottleneck remediation
    bn_lower = {str(b).lower() for b in bottlenecks}
    dom_lower = {str(b).lower() for b in dom_bottlenecks}
    overlapping = bn_lower & dom_lower
    if overlapping:
        recs.append(
            f"Target the overlapping bottlenecks ({', '.join(sorted(overlapping))}) "
            f"first — these are well-understood domain issues with proven remediations."
        )

    # 2 — Best practices
    for bp in practices[:3]:
        recs.append(f"Adopt best practice: {bp}")

    # 3 — Structural flaws
    for flaw in flaws[:2]:
        recs.append(f"Address structural flaw: {flaw}")

    # 4 — Deviations
    if deviations:
        recs.append(
            f"Establish a conformance-monitoring loop for the {len(deviations)} detected "
            f"deviations; categorise as acceptable vs. requiring corrective action."
        )

    # 5 — Health-tier recommendation
    if health_score < 55:
        recs.append(
            "Given the low health score, initiate a targeted process-redesign sprint "
            "within 30 days, focusing on the highest-impact bottlenecks identified above."
        )
    elif health_score < 70:
        recs.append(
            "Schedule a continuous-improvement review within 60 days to address "
            "moderate gaps and prevent regression."
        )
    else:
        recs.append(
            "Maintain the current trajectory with quarterly health-checks and "
            "incremental optimisation of remaining minor bottlenecks."
        )

    # Deduplicate while preserving order
    seen = set()
    unique_recs: List[str] = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            unique_recs.append(r)
    return unique_recs


# ──────────────────────────────────────────────────────────────────────────────
# 3. Brief Formatter — Markdown → HTML
# ──────────────────────────────────────────────────────────────────────────────


def format_brief_html(brief_markdown: str) -> str:
    """Convert a Markdown brief to styled HTML for the Streamlit dashboard.

    Parameters
    ----------
    brief_markdown : str
        Markdown string (as produced by :func:`generate_executive_brief`).

    Returns
    -------
    str
        HTML string with embedded CSS suitable for ``st.markdown(..., unsafe_allow_html=True)``.
    """
    if _HAS_MARKDOWN:
        body_html = _markdown_lib.markdown(
            brief_markdown,
            extensions=["tables", "fenced_code", "sane_lists", "toc"],
        )
    else:
        body_html = _markdown_to_html_fallback(brief_markdown)

    css = _BRIEF_CSS

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
{css}
</style>
</head>
<body>
<div class="brief-container">
{body_html}
</div>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# Fallback Markdown → HTML converter (no third-party dependency)
# ──────────────────────────────────────────────────────────────────────────────


def _markdown_to_html_fallback(md: str) -> str:
    """A minimal, dependency-free Markdown-to-HTML converter.

    Supports: headings (#..####), bold, italic, tables (pipe), lists,
    horizontal rules, and paragraphs.  Not a full CommonMark implementation
    but sufficient for the brief format generated by this module.
    """
    lines = md.split("\n")
    html_parts: List[str] = []
    in_table = False
    table_rows: List[str] = []
    in_list: Optional[str] = None  # "ul" or "ol"

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return
        html_parts.append('<table class="brief-table">')
        for idx, row in enumerate(table_rows):
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            tag = "th" if idx == 0 else "td"
            html_parts.append(
                "<tr>"
                + "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells)
                + "</tr>"
            )
        html_parts.append("</table>")
        in_table = False
        table_rows = []

    def flush_list():
        nonlocal in_list
        if in_list:
            html_parts.append(f"</{in_list}>")
            in_list = None

    for raw in lines:
        line = raw.rstrip()

        # Table detection
        if line.strip().startswith("|") and line.strip().endswith("|"):
            # Skip separator rows like |---|---|
            if re.match(r"^\|[\s\-:|]+\|$", line.strip()):
                continue
            in_table = True
            table_rows.append(line)
            continue
        elif in_table:
            flush_table()

        # Heading
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            flush_list()
            level = len(m.group(1))
            html_parts.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            continue

        # Horizontal rule
        if re.match(r"^-{3,}$", line.strip()):
            flush_list()
            html_parts.append("<hr/>")
            continue

        # Unordered list
        if re.match(r"^\s*[-•]\s+(.*)", line):
            if in_list != "ul":
                flush_list()
                in_list = "ul"
                html_parts.append("<ul>")
            item = re.match(r"^\s*[-•]\s+(.*)", line).group(1)
            html_parts.append(f"<li>{_inline(item)}</li>")
            continue

        # Ordered list
        if re.match(r"^\s*\d+\.\s+(.*)", line):
            if in_list != "ol":
                flush_list()
                in_list = "ol"
                html_parts.append("<ol>")
            item = re.match(r"^\s*\d+\.\s+(.*)", line).group(1)
            html_parts.append(f"<li>{_inline(item)}</li>")
            continue

        # Blank line
        if not line.strip():
            flush_list()
            html_parts.append("")
            continue

        # Paragraph
        flush_list()
        html_parts.append(f"<p>{_inline(line)}</p>")

    # Flush remaining state
    if in_table:
        flush_table()
    flush_list()

    return "\n".join(html_parts)


def _inline(text: str) -> str:
    """Convert inline Markdown (bold, italic, code) to HTML."""
    # Code spans
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<em>\1</em>", text)
    return text


# ──────────────────────────────────────────────────────────────────────────────
# CSS for the HTML brief
# ──────────────────────────────────────────────────────────────────────────────

_BRIEF_CSS = """
.brief-container {
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    color: #1a1a2e;
    line-height: 1.6;
    max-width: 960px;
    margin: 0 auto;
    padding: 24px 32px;
    background: #ffffff;
    border-radius: 10px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.brief-container h1 {
    font-size: 1.8em;
    color: #0f3460;
    border-bottom: 3px solid #e94560;
    padding-bottom: 10px;
    margin-top: 0;
}
.brief-container h2 {
    font-size: 1.35em;
    color: #16213e;
    margin-top: 28px;
    padding-bottom: 6px;
    border-bottom: 1px solid #ddd;
}
.brief-container h3 {
    font-size: 1.15em;
    color: #16213e;
    margin-top: 20px;
}
.brief-container p { margin: 10px 0; }
.brief-container strong { color: #0f3460; }
.brief-container ul, .brief-container ol { margin: 8px 0 8px 20px; }
.brief-container li { margin: 4px 0; }
.brief-container hr {
    border: none;
    border-top: 1px solid #e0e0e0;
    margin: 24px 0;
}
.brief-table {
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    font-size: 0.92em;
}
.brief-table th {
    background: #0f3460;
    color: #fff;
    text-align: left;
    padding: 10px 14px;
    border: 1px solid #0f3460;
}
.brief-table td {
    padding: 8px 14px;
    border: 1px solid #e0e0e0;
}
.brief-table tr:nth-child(even) td { background: #f7f9fc; }
.brief-container code {
    background: #f0f0f5;
    padding: 2px 5px;
    border-radius: 4px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 0.9em;
}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Convenience: full pipeline
# ──────────────────────────────────────────────────────────────────────────────


def run_research(
    process_name: str, pm4py_diagnostics: Dict[str, Any], use_web_fallback: bool = True
) -> BriefResult:
    """Convenience pipeline: research → brief → HTML.

    Returns a :class:`BriefResult` with ``markdown``, ``html``, and ``metadata``.
    """
    research = research_process_type(process_name, use_web_fallback=use_web_fallback)
    brief_md = generate_executive_brief(
        process_name, pm4py_diagnostics, research
    )
    brief_html = format_brief_html(brief_md)

    return BriefResult(
        markdown=brief_md,
        html=brief_html,
        metadata={
            "process_type": research.get("process_type"),
            "source": research.get("source"),
            "found": research.get("found"),
            "generated_at": datetime.datetime.now().isoformat(),
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# CLI / smoke test
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Research Agent — smoke test")
    parser.add_argument("--process", default="Procure-to-Pay", help="Process name to look up")
    parser.add_argument("--html", action="store_true", help="Also output HTML")
    args = parser.parse_args()

    # Mock PM4py diagnostics
    mock_diagnostics = {
        "variant_count": 9,
        "total_cases": 4200,
        "avg_cycle_time_hours": 168,
        "bottleneck_activities": ["PO approval routing", "3-way match exceptions"],
        "fitness": 0.82,
        "precision": 0.71,
        "generalization": 0.88,
        "simplicity": 0.90,
        "deviations": ["SKIP_GRN", "MANUAL_PO", "LATE_APPROVAL"],
    }

    result = run_research(args.process, mock_diagnostics, use_web_fallback=True)
    print(result.markdown)
    if args.html:
        print("\n--- HTML (first 500 chars) ---")
        print(result.html[:500])
