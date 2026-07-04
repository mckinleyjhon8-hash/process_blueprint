"""Elite Phase E4: deterministic research-calibrated ROI engine."""

from __future__ import annotations

import pytest

from process_blueprint.facts import ProcessFacts
from process_blueprint.roi import compute, default_inputs

FULL_INPUTS = {
    "category": "rpa",
    "volume_per_month": 500,
    "fte_count": 2,
    "gross_salary_gbp": 30000,
    "fte_multiplier": 1.30,
    "build_cost_gbp": 20000,
    "licence_gbp_per_month": 400,
    "error_rate_pct": 4.0,
    "cost_per_error_gbp": 25,
    "conversion_path": "hire_avoided",
    "discount_rate_pct": 15,
}


def test_uncomputed_shell_lists_missing_inputs(sample_facts):
    out = sample_facts.roi
    assert out["computed"] is False
    assert "fte_count" in out["missing_inputs"]
    assert "build_cost_gbp" in out["missing_inputs"]
    # log-provable seeds are present (E1), finance stays operator-stated
    assert out["inputs"]["volume_per_month"] is not None
    assert out["gate"] in ("blocked", "caveated", "pass")


def test_full_computation_and_calibrated_constants(sample_facts):
    out = compute(sample_facts, FULL_INPUTS)
    assert out["computed"] is True
    # research calibration: P2P → accounts_payable family → 75% STP ceiling
    assert out["stp_ceiling_pct"] == 75
    assert out["tco"]["contingency_pct"] == 15  # RPA
    # conservative curve is the research-calibrated 40/70/90
    assert out["scenarios"]["conservative"]["realisation_curve"] == [0.40, 0.70, 0.90]
    # labour benefit = 2 × 30,000 × 1.30 × 0.75 = £58,500
    labour = next(b for b in out["benefits"] if b["id"] == "labour")
    assert labour["annual_gbp"] == 58500
    assert labour["convertibility"] == "cashable"


def test_error_floor_never_zero(sample_facts):
    out = compute(sample_facts, FULL_INPUTS)
    err = next(b for b in out["benefits"] if b["id"] == "error_reduction")
    # post = max(0.4, 4.0×0.2)=0.8 → delta 3.2% × 6,000/yr × £25 = £4,800
    assert err["annual_gbp"] == 4800
    assert "0.8%" in err["label"]


def test_convertibility_test_excludes_capacity_from_npv(sample_facts):
    cash = compute(sample_facts, FULL_INPUTS)
    capacity = compute(sample_facts, {**FULL_INPUTS, "conversion_path": "not_converted"})
    assert capacity["capacity_annual_gbp"] == 58500
    assert capacity["cashable_annual_gbp"] < cash["cashable_annual_gbp"]
    # NPV must drop when labour is only capacity
    assert capacity["scenarios"]["base"]["npv_gbp"] < cash["scenarios"]["base"]["npv_gbp"]
    labour = next(b for b in capacity["benefits"] if b["id"] == "labour")
    assert "CAPACITY" in labour["note"]


def test_scenarios_are_monotonic(sample_facts):
    out = compute(sample_facts, FULL_INPUTS)
    s = out["scenarios"]
    assert s["conservative"]["npv_gbp"] < s["base"]["npv_gbp"] < s["optimistic"]["npv_gbp"]
    pb = [s[k]["payback_months"] for k in ("optimistic", "base", "conservative")]
    assert all(p is not None for p in pb)
    assert pb[0] <= pb[1] <= pb[2]


def test_ai_category_uses_slower_curve_and_higher_contingency(sample_facts):
    out = compute(sample_facts, {**FULL_INPUTS, "category": "ai"})
    assert out["scenarios"]["conservative"]["realisation_curve"] == [0.25, 0.55, 0.80]
    assert out["tco"]["contingency_pct"] == 27  # int(0.275*100)
    assert out["stp_ceiling_pct"] == 75  # LLM ceiling


def test_risk_adjustment_uses_e3_evs(sample_facts):
    out = compute(sample_facts, FULL_INPUTS)
    assert out["risk_ev_gbp"] > 0  # engine attaches conservative E3 assessment
    base = out["scenarios"]["base"]
    assert base["risk_adjusted_npv_gbp"] < base["npv_gbp"]


def test_npv_math_hand_checked(sample_facts):
    """Simple case, hand-computed: flows [-100, 60, 60, 60] @10% → NPV ≈ 49.21k."""
    out = compute(sample_facts, {**FULL_INPUTS,
                                 "discount_rate_pct": 10})
    flows = out["scenarios"]["base"]["cash_flows"]
    import math
    manual = sum(cf / (1.1 ** t) for t, cf in enumerate(flows))
    assert math.isclose(manual, out["scenarios"]["base"]["npv_gbp"], rel_tol=0.01)


def test_gate_passthrough_from_discovery(sample_facts):
    out = compute(sample_facts, FULL_INPUTS)
    assert out["gate"] == sample_facts.discovery["roi_gate"]
    assert out["provenance_note"].startswith("Volume and error rate are measured")


def test_roi_survives_roundtrip(sample_facts):
    rebuilt = ProcessFacts.from_dict(sample_facts.to_dict())
    assert rebuilt.roi["computed"] == sample_facts.roi["computed"]
