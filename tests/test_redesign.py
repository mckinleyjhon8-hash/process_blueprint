"""Elite Phase E2: the H1–H12 redesign heuristic engine."""

from __future__ import annotations

from process_blueprint.engine import analyze_dataframe
from process_blueprint.facts import ProcessFacts
from process_blueprint.redesign import generate, DISPOSITION_ORDER


def test_p2p_fires_error_proofing_on_rework(sample_facts):
    """P2P injects an Approve PO rework loop — H8 must catch it with evidence."""
    recs = sample_facts.redesign["recommendations"]
    h8 = next(r for r in recs if r["heuristic"] == "H8")
    assert "Approve PO" in h8["targets"]
    assert h8["disposition"] == "Standardise"
    assert "repeats" in h8["trigger_evidence"]
    # delta computed from the measured rework rate with the cited range
    assert h8["delta"]["reduction_pct_range"] == [60, 95]
    assert h8["source"]


def test_automation_is_hard_gated_by_ecrs(sample_facts):
    """No cow-path paving: every Automate rec is gated by open E/S/S recs."""
    recs = sample_facts.redesign["recommendations"]
    autos = [r for r in recs if r["disposition"] in ("Automate", "Augment_AI")]
    ess = [r for r in recs if r["disposition"] in ("Eliminate", "Simplify", "Standardise")]
    assert autos, "expected an automation candidate on the happy path"
    assert ess, "expected E/S/S recommendations before automation"
    for a in autos:
        assert a["gated_by"], "automation must be gated"
        assert len(a["gated_by"]) == len(ess)


def test_recommendations_ordered_by_phase_then_ecrs(sample_facts):
    recs = sample_facts.redesign["recommendations"]
    keys = [(r["phase"], DISPOSITION_ORDER.index(r["disposition"])) for r in recs]
    assert keys == sorted(keys)


def test_freight_fires_people_and_triage_heuristics():
    from tests.freight_log import build_freight_log

    facts = analyze_dataframe(build_freight_log(80, seed=11),
                              process_type="UK Freight Brokerage")
    recs = facts.redesign["recommendations"]
    by_h = {r["heuristic"] for r in recs}
    # 38 role-level SPOF activities → standard work + cross-training
    assert "SOP" in by_h
    spof = next(r for r in recs if r["heuristic"] == "SOP")
    assert spof["phase"] == 0 and spof["disposition"] == "Standardise"
    # 154-variant log, high exception rate → triage split
    assert "H4" in by_h
    triage = next(r for r in recs if r["heuristic"] == "H4")
    assert triage["delta"]["metric"] == "lead_time_seconds"
    assert triage["delta"]["baseline"] == round(facts.avg_cycle_time_seconds, 1)
    # automation candidates present but carry blockers/gates, never free passes
    h9 = next(r for r in recs if r["heuristic"] == "H9")
    assert isinstance(h9.get("blockers", []), list)
    assert h9["gated_by"]


def test_aggregate_capped_and_phased(sample_facts):
    agg = sample_facts.redesign["aggregate"]
    lo, hi = agg["lead_time_reduction_seconds_range"]
    assert 0 <= lo <= hi
    assert hi <= sample_facts.avg_cycle_time_seconds  # can never exceed baseline
    # research-calibrated conservative floor (roi_investment_research_reference)
    assert agg["realisation_phasing"]["Y1"] == "40–70%"


def test_redesign_survives_roundtrip(sample_facts):
    rebuilt = ProcessFacts.from_dict(sample_facts.to_dict())
    assert rebuilt.redesign["n_recommendations"] == \
        sample_facts.redesign["n_recommendations"]


def test_generate_degrades_on_minimal_facts():
    """Facts without insight layers must not crash the generator."""
    bare = ProcessFacts(process_type="X", source_file="x", n_events=0, n_cases=0,
                        n_activities=0, n_variants=0,
                        avg_cycle_time_seconds=0.0, median_cycle_time_seconds=0.0)
    out = generate(bare)
    assert out["n_recommendations"] == 0
    assert out["recommendations"] == []
