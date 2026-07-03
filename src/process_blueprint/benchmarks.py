"""
benchmarks.py — quartile benchmark engine (Elite Phase E1b).

Implements the Benchmark Reference playbook's core discipline:
"benchmark as evidence, not truth."

  * Seeded UK-baseline quartile tables (p25 / median / p75 / top-quartile) for
    the SME process families we can score from event-log-derived metrics.
    Every figure carries source + grade + date — publicly-citable ranges from
    the playbook, not fabricated precision.
  * Direction-aware quartile positioning (lower-is-better vs higher-is-better).
  * One-quartile-per-cycle target selection (never target more than one
    quartile jump per improvement cycle).
  * Plausibility thresholds + the zero-claims rule (a zero on an *estimated*
    figure usually means "not measured", not "perfect" — measured E1 zeros
    are legitimate).

Values are data, not code: swap or extend the tables without touching logic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .facts import ProcessFacts

# --------------------------------------------------------------------------- #
# Seeded benchmark data — UK baseline, SME (10–250 staff).
# Source: SME Process-Performance Benchmark Reference v1.0 (2026-06-30), §2,
# which cites APQC OSB / IOFM / SCOR / Forrester / HDI / CIPD ranges.
# --------------------------------------------------------------------------- #
_D = "lower"   # lower is better
_U = "higher"  # higher is better

FAMILIES: Dict[str, Dict[str, Any]] = {
    "accounts_payable": {
        "label": "Accounts Payable / Procure-to-Pay",
        # Verified framework codes (apqc_scor_framework_reference v3.0, 2026-07-02):
        # PCF v8.0 moved AP under 9.0 Manage Financial Resources.
        "framework": {"apqc_pcf_v8": "9.5 Manage AP and expense reimbursements",
                      "scor_v14": "S1.5 Authorize Supplier Payment"},
        "aliases": ["accounts payable", "procure-to-pay", "procure to pay", "p2p",
                    "purchase-to-pay", "invoice processing", "invoice"],
        "metrics": {
            "lead_time_days": {"p25": 12, "median": 8, "p75": 5, "top": 2.5, "direction": _D,
                               "unit": "days", "source": "IOFM AP Benchmark 2023", "grade": "B+"},
            "fpy_pct": {"p25": 85, "median": 92, "p75": 96, "top": 98.5, "direction": _U,
                        "unit": "%", "source": "APQC OSB (cited ranges) 2023", "grade": "B"},
            "rework_rate_pct": {"p25": 8, "median": 5, "p75": 2.5, "top": 1.0, "direction": _D,
                                "unit": "%", "source": "IOFM 2023", "grade": "B+"},
            "exception_rate_pct": {"p25": 20, "median": 12, "p75": 7, "top": 3, "direction": _D,
                                   "unit": "%", "source": "IOFM 2023", "grade": "B"},
        },
    },
    "order_fulfilment": {
        "label": "Order Fulfilment / Order-to-Cash",
        "framework": {"apqc_pcf_v8": "4.4.3 Operate warehousing (pick/pack/ship)",
                      "scor_v14": "F1 Fulfill Stocked Product"},
        "aliases": ["order fulfilment", "order fulfillment", "order-to-cash", "order to cash",
                    "o2c", "fulfilment", "fulfillment"],
        "metrics": {
            "lead_time_days": {"p25": 7, "median": 4, "p75": 2, "top": 1, "direction": _D,
                               "unit": "days", "source": "SCOR v14.0 (ASCM 2025)", "grade": "B+"},
            "fpy_pct": {"p25": 88, "median": 94, "p75": 97, "top": 99.5, "direction": _U,
                        "unit": "%", "source": "SCOR v14.0 (ASCM 2025)", "grade": "B+"},
            "exception_rate_pct": {"p25": 15, "median": 8, "p75": 4, "top": 1.5, "direction": _D,
                                   "unit": "%", "source": "SCOR v14.0 / APQC 2023", "grade": "B"},
        },
    },
    "customer_onboarding": {
        "label": "Customer Onboarding",
        "framework": {"apqc_pcf_v8": "3.5.2 Manage customers and accounts",
                      "scor_v14": None},
        "aliases": ["customer onboarding", "onboarding", "client onboarding", "kyc"],
        "metrics": {
            "lead_time_days": {"p25": 10, "median": 5, "p75": 2, "top": 0.5, "direction": _D,
                               "unit": "days", "source": "Forrester Onboarding 2022", "grade": "B"},
            "fpy_pct": {"p25": 65, "median": 80, "p75": 90, "top": 97, "direction": _U,
                        "unit": "%", "source": "Forrester 2022", "grade": "B"},
            "exception_rate_pct": {"p25": 25, "median": 15, "p75": 8, "top": 3, "direction": _D,
                                   "unit": "%", "source": "Forrester 2022", "grade": "B"},
        },
    },
    "customer_support": {
        "label": "Customer Support / Issue Resolution",
        "framework": {"apqc_pcf_v8": "6.2.2 Manage customer service problems, requests, and inquiries",
                      "scor_v14": None},
        "aliases": ["customer support", "customer service", "issue resolution", "ticketing",
                    "support", "helpdesk", "service desk"],
        "metrics": {
            "exception_rate_pct": {"p25": 20, "median": 12, "p75": 6, "top": 3, "direction": _D,
                                   "unit": "%", "source": "HDI Benchmark 2023", "grade": "B"},
        },
    },
    "payroll": {
        "label": "Payroll Processing",
        # PCF v8.0 moved payroll under 7.0 HR (was grouped with Finance in v7)
        "framework": {"apqc_pcf_v8": "7.5.4 Administer Payroll", "scor_v14": None},
        "aliases": ["payroll"],
        "metrics": {
            "fpy_pct": {"p25": 90, "median": 96, "p75": 99, "top": 99.8, "direction": _U,
                        "unit": "%", "source": "CIPD Payroll 2023", "grade": "B+"},
            "exception_rate_pct": {"p25": 10, "median": 5, "p75": 2, "top": 0.5, "direction": _D,
                                   "unit": "%", "source": "CIPD/APQC 2023", "grade": "B+"},
        },
    },
    "recruitment": {
        "label": "Recruitment & Hiring",
        "framework": {"apqc_pcf_v8": "7.2.2 Recruit/Source candidates", "scor_v14": None},
        "aliases": ["recruitment", "hiring", "talent acquisition"],
        "metrics": {
            "lead_time_days": {"p25": 45, "median": 30, "p75": 18, "top": 10, "direction": _D,
                               "unit": "days", "source": "SHRM/CIPD 2023", "grade": "B"},
            "exception_rate_pct": {"p25": 25, "median": 15, "p75": 8, "top": 3, "direction": _D,
                                   "unit": "%", "source": "SHRM 2023", "grade": "C"},
        },
    },
    # Fallback: generic SME transactional-process thresholds (KB §2.1–2.3 VSM ranges)
    "generic": {
        "label": "Generic SME transactional process",
        "framework": {"apqc_pcf_v8": None, "scor_v14": None},
        "aliases": [],
        "metrics": {
            "rework_rate_pct": {"p25": 8, "median": 5, "p75": 2, "top": 1, "direction": _D,
                                "unit": "%", "source": "Lean Toolbox / KB VSM ranges 2016-23", "grade": "B"},
            "exception_rate_pct": {"p25": 20, "median": 12, "p75": 7, "top": 3, "direction": _D,
                                   "unit": "%", "source": "KB complexity C3 ranges", "grade": "B"},
            "fpy_pct": {"p25": 85, "median": 92, "p75": 96, "top": 98.5, "direction": _U,
                        "unit": "%", "source": "KB VSM ranges", "grade": "B"},
        },
    },
}

# Plausibility ranges per metric (Benchmark Reference §4.2, log-scoreable subset).
PLAUSIBILITY: Dict[str, Dict[str, Any]] = {
    "lead_time_days": {"low": 0.02, "high": 90, "warn_low": 0.1, "warn_high": 60},
    "fpy_pct": {"low": 40, "high": 100, "warn_low": 60, "warn_high": 99.5},
    "rework_rate_pct": {"low": 0, "high": 40, "warn_low": 0, "warn_high": 20},
    "exception_rate_pct": {"low": 0, "high": 100, "warn_low": 0, "warn_high": 60},
    "heavy_tail_ratio": {"low": 1.0, "high": 50, "warn_low": 1.0, "warn_high": 8},
}


def match_family(process_type: str) -> str:
    """Map a free-text process type onto a benchmark family (else 'generic')."""
    p = (process_type or "").lower()
    for fam, spec in FAMILIES.items():
        if any(alias in p for alias in spec["aliases"]):
            return fam
    return "generic"


def _quartile(value: float, m: Dict[str, Any]) -> str:
    """Direction-aware quartile position (Q1 worst → Q4 best).

    Bands follow the playbook strictly from p25/median/p75; the `top` (p90+)
    figure is not a band edge — it is the aggressive target for Q3 performers.
    """
    p25, med, p75 = m["p25"], m["median"], m["p75"]
    if m["direction"] == _D:  # lower is better; the p25 column is the worst edge
        if value <= p75:
            return "Q4"
        if value <= med:
            return "Q3"
        if value <= p25:
            return "Q2"
        return "Q1"
    if value >= p75:
        return "Q4"
    if value >= med:
        return "Q3"
    if value >= p25:
        return "Q2"
    return "Q1"


def _target(quartile: str, m: Dict[str, Any]) -> Optional[float]:
    """Ambition ladder (playbook §4.1): Q1→median (conservative), Q2→p75
    (moderate), Q3→top-quartile (aggressive), Q4→None (diminishing returns)."""
    ladder = {"Q1": m["median"], "Q2": m["p75"], "Q3": m["top"], "Q4": None}
    return ladder[quartile]


def _plausibility(metric: str, value: float, provenance: str) -> Dict[str, Any]:
    spec = PLAUSIBILITY.get(metric)
    if spec is None:
        return {"flag": "pass", "note": None}
    if value < spec["low"] or value > spec["high"]:
        return {"flag": "fail",
                "note": f"outside plausible SME range [{spec['low']}–{spec['high']}]"}
    if value < spec["warn_low"] or value > spec["warn_high"]:
        return {"flag": "warning",
                "note": f"beyond typical SME range [{spec['warn_low']}–{spec['warn_high']}]"}
    # zero-claims rule: a zero that was *estimated* is almost always unmeasured
    if value == 0 and metric in ("rework_rate_pct", "exception_rate_pct") \
            and provenance not in ("measured",):
        return {"flag": "warning", "note": "zero claim on an estimated figure — likely not measured"}
    return {"flag": "pass", "note": None}


def _metric_values(facts: ProcessFacts) -> Dict[str, float]:
    """Pull the benchmarkable metric values out of the facts (all E1/measured)."""
    tp = facts.time_profile or {}
    vals: Dict[str, float] = {
        "lead_time_days": round(facts.avg_cycle_time_seconds / 86400.0, 2),
    }
    for key in ("fpy_pct", "rework_case_rate_pct", "exception_rate_pct", "heavy_tail_ratio"):
        if tp.get(key) is not None:
            vals["rework_rate_pct" if key == "rework_case_rate_pct" else key] = float(tp[key])
    return vals


def apply_benchmarks(facts: ProcessFacts) -> Dict[str, Any]:
    """Position the run's measured metrics against the peer quartiles.

    Returns the structure stored at ``facts.benchmarks`` — every position keeps
    its source + grade so the deliverable can cite it, and a plausibility flag
    so nonsense numbers are caught before they reach a client.
    """
    family = match_family(facts.process_type)
    spec = FAMILIES[family]
    values = _metric_values(facts)

    positions: List[Dict[str, Any]] = []
    for metric, value in values.items():
        m = spec["metrics"].get(metric) or FAMILIES["generic"]["metrics"].get(metric)
        provenance = facts.provenance.get(metric, "measured")
        plaus = _plausibility(metric, value, provenance)
        entry: Dict[str, Any] = {
            "metric": metric,
            "value": value,
            "provenance": provenance,
            "plausibility": plaus["flag"],
            "plausibility_note": plaus["note"],
        }
        if m is not None:
            q = _quartile(value, m)
            target = _target(q, m)
            gap = None
            if target is not None and value:
                gap = round(abs(value - target) / abs(value) * 100.0, 1)
            entry.update(
                unit=m["unit"], direction=m["direction"],
                p25=m["p25"], median=m["median"], p75=m["p75"], top_quartile=m["top"],
                quartile=q, target_value=target, gap_pct=gap,
                source=m["source"], grade=m["grade"],
            )
        positions.append(entry)

    return {
        "family": family,
        "family_label": spec["label"],
        # verified taxonomy codes (PCF v8.0 2026-02-25 · SCOR v14.0 ASCM 2025)
        "framework": spec.get("framework", {}),
        "baseline": "UK SME (10–250 staff)",
        "principle": "benchmark as evidence, not truth — ranges, not targets",
        "positions": positions,
    }
