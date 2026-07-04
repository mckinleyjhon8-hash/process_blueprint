"""
roi.py — the deterministic ROI / investment-appraisal engine (Elite Phase E4).

Every number is computed from stated inputs and research-calibrated constants —
the LLM writes *around* these figures, never invents them. Calibration follows
`roi_investment_research_reference.md` (2026-07-02), which corrected the
playbook's optimistic defaults against empirical data:

  * Realisation curves: RPA 40/70/90% (Y1/Y2/Y3 conservative) — AI 25/55/80%.
  * STP ceilings: never assume 100% straight-through; AP 75%, onboarding 60%,
    generic RPA 80%, LLM extraction 75%.
  * Fully-loaded FTE multiplier: ×1.30 UK typical (2025/26 employer NI).
  * TCO contingency: 15% (RPA) / 27.5% (AI) — empirical overrun mean ≈27%.
  * Post-automation error rate floors at 0.4% — automation shifts errors,
    it does not eliminate them.

Disciplines from the playbooks:
  * 7-component TCO (build, licence, maintenance, exception upkeep, change,
    training, decommission) + contingency.
  * Convertibility test: labour benefit is only CASHABLE with a named
    conversion path (hire avoided / overtime eliminated / reallocation to
    billable); otherwise it is CAPACITY and excluded from cash NPV.
  * Risk-adjusted view: post-mitigation risk EVs (E3) subtracted from benefit.
  * Discovery ROI gate passthrough: a blocked gate means this may not be
    presented to a client at all.

Financial inputs are operator-stated (E3/E4 evidence) — the output carries
that provenance and a wide-band warning; the log only seeds volume and errors.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .facts import ProcessFacts

# --------------------------------------------------------------------------- #
# Research-calibrated constants (roi_investment_research_reference, 2026-07-02)
# --------------------------------------------------------------------------- #
REALISATION = {
    "rpa": {"conservative": [0.40, 0.70, 0.90], "base": [0.55, 0.80, 0.95],
            "optimistic": [0.60, 0.85, 0.95]},
    "ai": {"conservative": [0.25, 0.55, 0.80], "base": [0.35, 0.65, 0.85],
           "optimistic": [0.45, 0.70, 0.90]},
}
BENEFIT_ADJ = {"conservative": 0.80, "base": 1.00, "optimistic": 1.10}
CONTINGENCY = {"rpa": 0.15, "ai": 0.275}
STP_CEILINGS = {"accounts_payable": 0.75, "customer_onboarding": 0.60,
                "order_fulfilment": 0.70, "generic": 0.80, "ai": 0.75}
ERROR_FLOOR_PCT = 0.4          # post-automation errors never reach zero
ERROR_RESIDUAL_FACTOR = 0.2    # post = max(floor, 20% of baseline)
DEFAULT_DISCOUNT = 0.15        # mid-range SME hurdle rate (build-up method)
DEFAULT_FTE_MULTIPLIER = 1.30  # UK 2025/26 typical loaded cost

CONVERSION_PATHS = {
    "hire_avoided": "cashable",
    "overtime_eliminated": "cashable",
    "reallocation_billable": "cashable",
    "not_converted": "capacity",
}

INPUT_FIELDS = [
    # id, label, kind, required
    {"id": "category", "label": "Automation category", "kind": "select:rpa,ai", "required": True},
    {"id": "volume_per_month", "label": "Transactions per month", "kind": "number", "required": True},
    {"id": "fte_count", "label": "FTEs on this process", "kind": "number", "required": True},
    {"id": "gross_salary_gbp", "label": "Average gross salary (£/yr)", "kind": "number", "required": True},
    {"id": "fte_multiplier", "label": "Loaded-cost multiplier", "kind": "select:1.20,1.30,1.45", "required": False},
    {"id": "build_cost_gbp", "label": "Build / implementation (£ one-off)", "kind": "number", "required": True},
    {"id": "licence_gbp_per_month", "label": "Licence / platform (£/month)", "kind": "number", "required": True},
    {"id": "error_rate_pct", "label": "Baseline error rate (%)", "kind": "number", "required": False},
    {"id": "cost_per_error_gbp", "label": "Cost per error (£)", "kind": "number", "required": False},
    {"id": "other_annual_benefit_gbp", "label": "Other annual benefit (£, e.g. discounts captured)",
     "kind": "number", "required": False},
    {"id": "conversion_path", "label": "How is freed labour converted?",
     "kind": "select:" + ",".join(CONVERSION_PATHS), "required": True},
    {"id": "discount_rate_pct", "label": "Discount rate (%)", "kind": "number", "required": False},
]


def default_inputs(facts: ProcessFacts) -> Dict[str, Any]:
    """Seed what the log can prove (E1); everything financial stays operator-stated."""
    tp = facts.time_profile or {}
    return {
        "category": "rpa",
        "volume_per_month": tp.get("volume_per_month"),
        "error_rate_pct": tp.get("rework_case_rate_pct"),
        "fte_multiplier": DEFAULT_FTE_MULTIPLIER,
        "discount_rate_pct": DEFAULT_DISCOUNT * 100,
        "conversion_path": "not_converted",  # conservative until the operator names one
    }


def _stp_ceiling(facts: ProcessFacts, category: str) -> float:
    if category == "ai":
        return STP_CEILINGS["ai"]
    family = (facts.benchmarks or {}).get("family", "generic")
    return STP_CEILINGS.get(family, STP_CEILINGS["generic"])


def _npv(rate: float, flows: List[float]) -> float:
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))


def _payback_months(flows_monthly_y0: float, monthly_net: List[float]) -> Optional[float]:
    """Months until cumulative cash turns non-negative (36-month horizon)."""
    cum = flows_monthly_y0
    for m in range(1, 37):
        cum += monthly_net[(m - 1) // 12]
        if cum >= 0:
            return float(m)
    return None


def compute(facts: ProcessFacts, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Full 3-year appraisal. Missing required inputs → uncomputed shell."""
    merged = {**default_inputs(facts), **{k: v for k, v in (inputs or {}).items()
                                          if v is not None}}
    missing = [f["id"] for f in INPUT_FIELDS
               if f["required"] and merged.get(f["id"]) in (None, "", 0)]
    base_shell = {
        "computed": False,
        "inputs": merged,
        "input_fields": INPUT_FIELDS,
        "missing_inputs": missing,
        "gate": (facts.discovery or {}).get("roi_gate", "blocked"),
        "gate_note": (facts.discovery or {}).get("roi_gate_note", ""),
        "provenance_note": "Volume and error rate are measured from the log (E1); all "
                           "financial inputs are operator-stated (E3/E4) — present ranges, "
                           "not points.",
    }
    if missing:
        return base_shell

    category = str(merged["category"]).lower()
    curve_set = REALISATION["ai" if category == "ai" else "rpa"]
    volume_yr = float(merged["volume_per_month"]) * 12.0
    loaded_fte = float(merged["fte_count"]) * float(merged["gross_salary_gbp"]) \
        * float(merged.get("fte_multiplier") or DEFAULT_FTE_MULTIPLIER)
    stp = _stp_ceiling(facts, category)
    rate = float(merged.get("discount_rate_pct") or DEFAULT_DISCOUNT * 100) / 100.0

    # ---- benefit register (annual, steady-state, pre-realisation) ----------
    labour_annual = loaded_fte * stp
    conversion = str(merged.get("conversion_path", "not_converted"))
    labour_class = CONVERSION_PATHS.get(conversion, "capacity")

    err_base = float(merged.get("error_rate_pct") or 0.0)
    err_post = max(ERROR_FLOOR_PCT, err_base * ERROR_RESIDUAL_FACTOR) if err_base else 0.0
    error_annual = max(0.0, (err_base - err_post) / 100.0) * volume_yr \
        * float(merged.get("cost_per_error_gbp") or 0.0)

    other_annual = float(merged.get("other_annual_benefit_gbp") or 0.0)

    benefits = [
        {"id": "labour", "label": f"Labour capacity released ({int(stp*100)}% STP ceiling applied)",
         "annual_gbp": round(labour_annual, 0), "convertibility": labour_class,
         "conversion_path": conversion,
         "note": None if labour_class == "cashable" else
         "No conversion path named — counted as CAPACITY, excluded from cash NPV "
         "(playbook convertibility test)."},
        {"id": "error_reduction", "label": f"Error reduction ({err_base}% → {err_post:.1f}%, floor applied)",
         "annual_gbp": round(error_annual, 0), "convertibility": "cashable",
         "conversion_path": "cost_avoided", "note": None},
        {"id": "other", "label": "Other stated benefits",
         "annual_gbp": round(other_annual, 0), "convertibility": "cashable",
         "conversion_path": "stated", "note": None},
    ]
    double_count_warnings = []
    if error_annual > 0 and labour_class == "cashable":
        double_count_warnings.append(
            "Check overlap: if error rework time is part of the released labour, "
            "count it once (double-count register).")

    cashable_annual = sum(b["annual_gbp"] for b in benefits if b["convertibility"] == "cashable")
    capacity_annual = sum(b["annual_gbp"] for b in benefits if b["convertibility"] == "capacity")

    # ---- 7-component 3-year TCO --------------------------------------------
    build = float(merged["build_cost_gbp"])
    licence_3yr = float(merged["licence_gbp_per_month"]) * 36.0
    maintenance_3yr = build * 0.15 * 3
    exceptions_yr = volume_yr * (1 - stp)
    hourly = (float(merged["gross_salary_gbp"]) *
              float(merged.get("fte_multiplier") or DEFAULT_FTE_MULTIPLIER)) / 1720.0
    exception_upkeep_3yr = exceptions_yr * (10.0 / 60.0) * hourly * 3  # ~10 min each
    change_3yr = build * 0.10 * 3
    training = build * 0.10
    decommission = build * 0.05
    subtotal = build + licence_3yr + maintenance_3yr + exception_upkeep_3yr \
        + change_3yr + training + decommission
    contingency = subtotal * CONTINGENCY["ai" if category == "ai" else "rpa"]
    tco = {
        "build": round(build, 0), "licence_3yr": round(licence_3yr, 0),
        "maintenance_3yr": round(maintenance_3yr, 0),
        "exception_upkeep_3yr": round(exception_upkeep_3yr, 0),
        "change_3yr": round(change_3yr, 0), "training": round(training, 0),
        "decommission": round(decommission, 0),
        "contingency": round(contingency, 0),
        "contingency_pct": int(CONTINGENCY["ai" if category == "ai" else "rpa"] * 100),
        "total_3yr": round(subtotal + contingency, 0),
    }
    recurring_yr = (licence_3yr + maintenance_3yr + exception_upkeep_3yr + change_3yr) / 3.0
    oneoff = build + training + decommission + contingency

    # ---- risk adjustment (E3 post-mitigation EVs) ---------------------------
    risk_ev = float(((facts.ai_assessment or {}).get("total_risk_ev_gbp") or {})
                    .get("post_mitigation", 0.0))

    # ---- scenarios -----------------------------------------------------------
    scenarios = {}
    for name, curve in curve_set.items():
        adj = BENEFIT_ADJ[name]
        annual = cashable_annual * adj
        flows = [-oneoff] + [annual * curve[y] - recurring_yr for y in range(3)]
        risk_flows = [flows[0]] + [f - risk_ev / 3.0 for f in flows[1:]]
        total_benefit = sum(annual * curve[y] for y in range(3))
        scenarios[name] = {
            "realisation_curve": curve,
            "annual_benefit_gbp": round(annual, 0),
            "cash_flows": [round(f, 0) for f in flows],
            "npv_gbp": round(_npv(rate, flows), 0),
            "risk_adjusted_npv_gbp": round(_npv(rate, risk_flows), 0),
            "payback_months": _payback_months(-oneoff, [annual * curve[y] / 12.0
                                                        - recurring_yr / 12.0
                                                        for y in range(3)]),
            "roi_3yr_pct": round((total_benefit - tco["total_3yr"])
                                 / tco["total_3yr"] * 100.0, 0),
        }

    return {
        **base_shell,
        "computed": True,
        "missing_inputs": [],
        "category": category,
        "stp_ceiling_pct": int(stp * 100),
        "discount_rate_pct": round(rate * 100, 1),
        "benefits": benefits,
        "cashable_annual_gbp": round(cashable_annual, 0),
        "capacity_annual_gbp": round(capacity_annual, 0),
        "double_count_warnings": double_count_warnings,
        "tco": tco,
        "risk_ev_gbp": round(risk_ev, 0),
        "scenarios": scenarios,
        "cost_of_delay_gbp_per_month": round(scenarios["base"]["annual_benefit_gbp"] / 12.0, 0),
        "calibration_note": "Realisation curves, STP ceilings, contingency and error floors "
                            "follow roi_investment_research_reference (2026-07-02) — "
                            "conservative by design; vendor projections would be higher.",
    }
