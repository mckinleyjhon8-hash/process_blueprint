"""
redesign.py — the Redesign playbook's heuristic engine (Elite Phase E2).

Deterministic TO-BE generation: each redesign heuristic (H1–H12) carries a
*trigger detector* that fires on measured evidence in ProcessFacts, and a
*delta model* that applies the playbook's cited improvement ranges to the
measured baseline — so every recommendation is traceable:

    trigger evidence (E1, measured) → heuristic (cited range) → computed delta

Discipline enforced from the playbook:
  * ECRS order of attack — Eliminate → Simplify → Standardise → Automate →
    Augment_AI. Automation recommendations are HARD-GATED behind unresolved
    E/S/S recommendations on the same targets ("don't pave the cow-path").
  * Every recommendation carries its pre-condition warning (hidden controls,
    separation of duties, economic batch quantities…).
  * Aggregate opportunity is capped against the benchmark gap (§6.3 —
    exceeding it means double-counting or inflation, and we say so).

The LLM never invents these numbers; it writes around them.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .facts import ProcessFacts

# playbook §5.2 typical improvement ranges (fractions of the affected baseline)
RANGES = {
    "H2": (0.20, 0.40),   # Combine: lead-time cut at eliminated hand-offs
    "H4": (0.40, 0.70),   # Triage: standard-path lead-time cut
    "H5": (0.30, 0.60),   # Parallelism
    "H6": (0.50, 0.80),   # Batch-to-flow: batch-wait removal
    "H7": (0.20, 0.40),   # Pull/WIP limits (Little's Law)
    "H8": (0.60, 0.95),   # Poka-yoke: error-rate cut
    "H9": (0.70, 0.95),   # Automation: step process-time cut
    "H11": (0.30, 0.60),  # Control relocation: rework-cost cut
    "H12": (0.70, 0.90),  # Integration: re-entry time cut
}

DISPOSITION_ORDER = ["Eliminate", "Simplify", "Standardise", "Automate", "Augment_AI"]


def _fmt_h(seconds: float) -> str:
    h = seconds / 3600.0
    return f"{h / 24:.1f}d" if h >= 48 else f"{h:.1f}h"


def _rec(
    heuristic: str,
    name: str,
    disposition: str,
    annotation: str,
    targets: List[str],
    trigger_evidence: str,
    move: str,
    precondition: str,
    phase: int,
    delta: Optional[Dict[str, Any]] = None,
    quadrangle: Optional[Dict[str, str]] = None,
    source: str = "Reijers & Liman Mansar 2005; Redesign playbook §2",
) -> Dict[str, Any]:
    return {
        "heuristic": heuristic,
        "name": name,
        "disposition": disposition,
        "annotation": annotation,
        "targets": targets,
        "trigger_evidence": trigger_evidence,   # measured (E1) — why this fired
        "move": move,                            # what to actually do
        "precondition": precondition,            # what to verify before doing it
        "phase": phase,                          # 0 foundation · 1 quick win · 2 automation · 3 AI
        "delta": delta or {},                    # computed TO-BE effect (cited range × baseline)
        "quadrangle": quadrangle or {},          # time/cost/quality/flexibility direction
        "provenance": "trigger: measured (E1) · delta: heuristic range (E2/E3)",
        "source": source,
        "gated_by": [],                          # filled for Automate/Augment_AI (ECRS gate)
    }


def _delta(metric: str, scope: str, baseline_seconds: float, rng: Tuple[float, float],
           unit: str = "seconds") -> Dict[str, Any]:
    lo, hi = rng
    return {
        "metric": metric,
        "scope": scope,
        "baseline": round(baseline_seconds, 1),
        "unit": unit,
        "reduction_pct_range": [int(lo * 100), int(hi * 100)],
        "to_be_range": [round(baseline_seconds * (1 - hi), 1),
                        round(baseline_seconds * (1 - lo), 1)],
    }


# --------------------------------------------------------------------------- #
# Trigger detectors — each returns a list of recommendations
# --------------------------------------------------------------------------- #
def _h6_batch_to_flow(facts: ProcessFacts) -> List[Dict[str, Any]]:
    out = []
    for b in (facts.batching or [])[:3]:
        out.append(_rec(
            "H6", "Batch-to-Flow", "Simplify", "Simplify [Rearrange: batch→flow]",
            [b["activity"]],
            f"Batch processing detected at '{b['activity']}' ({b['resource']}, "
            f"{b['batch_type']}, {b['n_batches']} batches observed).",
            "Process items on arrival instead of accumulating batches; if a genuine "
            "setup cost exists, reduce setup first (SMED) then shrink the batch.",
            "Confirm there is no economic batch quantity (real setup/changeover cost) "
            "before forcing one-piece flow.",
            1,
            quadrangle={"time": "+", "cost": "=", "quality": "+", "flexibility": "+"},
            source="Rother & Shook 2003; Little 1961; Redesign playbook H6",
        ))
    return out


def _h8_error_proofing(facts: ProcessFacts) -> List[Dict[str, Any]]:
    if not facts.rework_activities:
        return []
    top = list(facts.rework_activities.items())[:3]
    tp = facts.time_profile or {}
    rework_rate = tp.get("rework_case_rate_pct")
    acts = [a for a, _ in top]
    evidence = ", ".join(f"'{a}' repeats {n}× across cases" for a, n in top)
    if rework_rate is not None:
        evidence += f"; {rework_rate}% of cases contain at least one rework loop"
    delta = None
    if rework_rate:
        delta = _delta("rework_case_rate_pct", "whole process", rework_rate,
                       RANGES["H8"], unit="pct_points")
    return [_rec(
        "H8", "Error-Proofing (Poka-Yoke)", "Standardise",
        "Standardise [Poka-Yoke: constrain inputs at the rework sources]",
        acts,
        evidence + ".",
        "Constrain the inputs that feed these steps (dropdowns, mandatory fields, "
        "format validation, scan instead of key) so the error cannot occur; keep an "
        "'other' path routed to manual review.",
        "Error types must be classifiable first; do not over-constrain legitimate "
        "edge cases (error-proof the 80%, gate the 20%).",
        1,
        delta=delta,
        quadrangle={"time": "=", "cost": "+", "quality": "+", "flexibility": "-"},
        source="Shingo 1986; Redesign playbook H8",
    )]


def _h11_control_relocation(facts: ProcessFacts) -> List[Dict[str, Any]]:
    """Rework concentrated late in the happy path → move the check earlier."""
    if not facts.rework_activities or not facts.top_variants:
        return []
    happy = list(facts.top_variants[0].sequence)
    n = len(happy)
    late = [a for a in facts.rework_activities
            if a in happy and happy.index(a) >= (2 * n) // 3]
    if not late:
        return []
    a = late[0]
    return [_rec(
        "H11", "Control Relocation (fail-fast)", "Simplify",
        f"Simplify [Rearrange: move the check that catches '{a}' errors earlier]",
        [a],
        f"Rework at '{a}' occurs at position {happy.index(a) + 1} of {n} on the "
        f"dominant path — errors are being caught late, after value has been added.",
        "Move the validation to the earliest point where its input data exists, so "
        "failures stop the case before downstream work is invested.",
        "The earlier data must be current enough not to create false positives, and "
        "no regulation may require the check at its current position.",
        1,
        quadrangle={"time": "+", "cost": "+", "quality": "=", "flexibility": "="},
        source="Shingo 1986; Redesign playbook H11",
    )]


def _h4_triage(facts: ProcessFacts) -> List[Dict[str, Any]]:
    tp = facts.time_profile or {}
    exc = tp.get("exception_rate_pct")
    if exc is None or exc < 30:
        return []
    baseline = facts.avg_cycle_time_seconds
    return [_rec(
        "H4", "Triage / Case-Type Split", "Simplify",
        "Simplify [Triage: split standard vs exception paths]",
        ["process-level"],
        f"{exc}% of cases run outside the five most common paths "
        f"({facts.n_variants} distinct variants for {facts.n_cases} cases) — one "
        f"flow is serving very different case types.",
        "Insert an objective triage at intake (value / case-type / complexity); give "
        "standard cases a lean fast path and route exceptions to a full path.",
        "Triage criteria must be objective and cheap (<5% of process time); keep it "
        "to 2–3 paths — over-splitting adds maintenance burden.",
        1,
        delta=_delta("lead_time_seconds", "standard-path cases", baseline, RANGES["H4"]),
        quadrangle={"time": "+", "cost": "+", "quality": "=", "flexibility": "+"},
        source="Reijers & Liman Mansar 2005; Redesign playbook H4",
    )]


def _h5_parallelism(facts: ProcessFacts) -> List[Dict[str, Any]]:
    """Pairs observed in BOTH orders across variants have no hard dependency."""
    variants = facts.top_variants or []
    if len(variants) < 2:
        return []
    order: Dict[Tuple[str, str], int] = {}
    for v in variants:
        seq = list(v.sequence)
        for i, a in enumerate(seq):
            for b in seq[i + 1:]:
                if a != b:
                    order[(a, b)] = order.get((a, b), 0) + v.frequency
    flexible = [
        (a, b) for (a, b), n in order.items()
        if (b, a) in order and n >= 2 and order[(b, a)] >= 2 and a < b
    ]
    if not flexible:
        return []
    pairs = flexible[:3]
    evidence = "; ".join(
        f"'{a}' and '{b}' occur in both orders across common variants" for a, b in pairs
    )
    # baseline: waits on the flow edges between these pairs, if measured
    edges = {(e["source"], e["target"]): e for e in (facts.flow or {}).get("edges", [])}
    wait = sum(
        edges.get((a, b), edges.get((b, a), {})).get("mean_wait_seconds", 0.0)
        for a, b in pairs
    )
    return [_rec(
        "H5", "Parallelism", "Simplify",
        "Simplify [Rearrange: run order-independent steps in parallel]",
        [f"{a} ∥ {b}" for a, b in pairs],
        evidence + " — the log itself proves no hard dependency.",
        "Fork these steps to run simultaneously and join before the next dependent "
        "step; lead time drops from the sum to the max of the branch times.",
        "Verify no shared bottleneck resource serves both branches, or they will "
        "queue anyway and only add coupling.",
        1,
        delta=_delta("lead_time_seconds", "affected hand-offs", wait, RANGES["H5"])
        if wait > 0 else None,
        quadrangle={"time": "+", "cost": "=", "quality": "=", "flexibility": "-"},
        source="Reijers & Liman Mansar 2005; Redesign playbook H5",
    )]


def _h7_pull(facts: ProcessFacts) -> List[Dict[str, Any]]:
    """Queue behaviour: mean wait ≫ median wait on a heavy edge = WIP piling up."""
    edges = (facts.flow or {}).get("edges", [])
    queues = [
        e for e in edges
        if e["frequency"] >= max(5, facts.n_cases // 10)
        and e["median_wait_seconds"] > 0
        and e["mean_wait_seconds"] / e["median_wait_seconds"] >= 3.0
        and e["mean_wait_seconds"] >= 3600
    ]
    queues.sort(key=lambda e: -e["mean_wait_seconds"])
    if not queues:
        return []
    e = queues[0]
    return [_rec(
        "H7", "Pull System / WIP Limits", "Standardise",
        f"Standardise [Pull: WIP-limited queue at '{e['target']}']",
        [f"{e['source']} → {e['target']}"],
        f"Hand-off '{e['source']} → {e['target']}' waits {_fmt_h(e['mean_wait_seconds'])} "
        f"on average but only {_fmt_h(e['median_wait_seconds'])} at the median — the "
        f"tail is queue formation, not work.",
        "Set a WIP limit at the receiving step and make the queue visible; upstream "
        "produces only on a pull signal (Little's Law: halve WIP, halve wait).",
        "Management must accept upstream idle time; start the WIP limit at the "
        "current average queue depth and tighten gradually.",
        1,
        delta=_delta("wait_seconds", f"{e['source']} → {e['target']}",
                     e["mean_wait_seconds"], RANGES["H7"]),
        quadrangle={"time": "+", "cost": "+", "quality": "+", "flexibility": "+"},
        source="Little 1961; Rother & Shook 2003; Redesign playbook H7",
    )]


def _spof_standardise(facts: ProcessFacts) -> List[Dict[str, Any]]:
    spof = (facts.resources or {}).get("single_points_of_failure", [])
    if not spof:
        return []
    shown = spof[:5]
    return [_rec(
        "SOP", "Standard Work + Cross-Training", "Standardise",
        "Standardise [SOP + cross-training at single-point-of-failure steps]",
        shown,
        f"{len(spof)} activities are performed by exactly one role — an absence "
        f"stops the process (e.g. {', '.join(shown[:3])}).",
        "Document standard work for these steps and cross-train at least one backup "
        "per step; SPOF elimination is also the precondition for later automation.",
        "Prioritise the SPOF steps that sit on the dominant path or at bottlenecks.",
        0,
        quadrangle={"time": "=", "cost": "=", "quality": "+", "flexibility": "+"},
        source="KB §2.4 root-cause patterns; Liker 2021",
    )]


def _h9_automation(facts: ProcessFacts) -> List[Dict[str, Any]]:
    """Automation candidates — HARD-GATED by the ECRS sequence + preconditions."""
    tp = facts.time_profile or {}
    vol = tp.get("volume_per_month")
    exc = tp.get("exception_rate_pct")
    if not facts.top_variants:
        return []
    happy = list(facts.top_variants[0].sequence)
    freq = facts.activity_frequencies or {}
    # candidates: high-volume happy-path activities (the standardisable core)
    candidates = [a for a in happy if freq.get(a, 0) >= facts.n_cases][:4]
    if not candidates:
        return []

    blockers: List[str] = []
    if vol is not None and vol < 50:
        blockers.append(f"volume {vol}/month is below the 50/month automation floor")
    if exc is not None and exc > 30:
        blockers.append(f"exception rate {exc}% exceeds the 30% ceiling — Standardise_First")

    rec = _rec(
        "H9", "Task Automation (post-redesign)", "Automate",
        "Automate [rule-based happy-path steps — ONLY after E/S/S resolve]",
        candidates,
        f"These steps run in every case on the dominant path "
        f"({tp.get('top_variant_coverage_pct', '?')}% coverage"
        + (f", ~{vol}/month" if vol is not None else "") + ").",
        "Encode the step logic as rules/workflow after the Eliminate–Simplify–"
        "Standardise dispositions above are resolved; route exceptions to humans.",
        "Cardinal rule: automating a step that should have been eliminated is paving "
        "the cow-path. Inputs must be digital and the step rule-based.",
        2,
        delta=_delta("step_process_time", "automated steps",
                     0.0, RANGES["H9"]) | {"note": "quantify after E/S/S resolve"},
        quadrangle={"time": "+", "cost": "+", "quality": "+", "flexibility": "-"},
        source="Hammer 1990; Willcocks 2017; Redesign playbook H9",
    )
    rec["blockers"] = blockers
    return [rec]


# --------------------------------------------------------------------------- #
def generate(facts: ProcessFacts) -> Dict[str, Any]:
    """Run every trigger detector, enforce ECRS gating, aggregate the prize."""
    recs: List[Dict[str, Any]] = []
    for detector in (_spof_standardise, _h6_batch_to_flow, _h8_error_proofing,
                     _h11_control_relocation, _h4_triage, _h5_parallelism,
                     _h7_pull, _h9_automation):
        try:
            recs.extend(detector(facts))
        except Exception:  # pragma: no cover — a detector must never kill the run
            continue

    # ECRS hard gate: every Automate/Augment_AI rec is gated by all open E/S/S recs
    ess_ids = [f"{r['heuristic']}:{r['name']}" for r in recs
               if r["disposition"] in ("Eliminate", "Simplify", "Standardise")]
    for r in recs:
        if r["disposition"] in ("Automate", "Augment_AI"):
            r["gated_by"] = ess_ids

    recs.sort(key=lambda r: (r["phase"], DISPOSITION_ORDER.index(r["disposition"])))

    # aggregate lead-time opportunity, capped at the benchmark gap (§6.3)
    total_lo = total_hi = 0.0
    for r in recs:
        d = r.get("delta") or {}
        if d.get("metric") in ("lead_time_seconds", "wait_seconds") and d.get("baseline"):
            lo, hi = d["reduction_pct_range"]
            total_lo += d["baseline"] * lo / 100.0
            total_hi += d["baseline"] * hi / 100.0
    total_hi = min(total_hi, facts.avg_cycle_time_seconds * 0.9)

    cap_note = None
    lead_pos = next((p for p in (facts.benchmarks or {}).get("positions", [])
                     if p["metric"] == "lead_time_days" and p.get("target_value")), None)
    if lead_pos:
        gap_seconds = max(
            (lead_pos["value"] - lead_pos["target_value"]) * 86400.0, 0.0
        )
        if gap_seconds and total_hi > gap_seconds:
            total_hi = gap_seconds
            cap_note = (
                "Aggregate opportunity capped at the benchmark gap to the next "
                "quartile target — anything beyond it indicates double-counting "
                "or inflated estimates (playbook §6.3)."
            )

    return {
        "sequence": DISPOSITION_ORDER,
        "recommendations": recs,
        "n_recommendations": len(recs),
        "aggregate": {
            "lead_time_reduction_seconds_range": [round(total_lo, 1), round(total_hi, 1)],
            "baseline_lead_time_seconds": facts.avg_cycle_time_seconds,
            "realisation_phasing": {"Y1": "50–70%", "Y2": "70–90%", "Y3": "90–100%"},
            "cap_note": cap_note,
        },
        "principle": "Never pave the cow-path: Eliminate → Simplify → Standardise "
                     "→ Automate → Augment_AI, in that order.",
    }
