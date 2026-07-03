"""Elite Phase E3: AI decision tree, data-readiness gates, HITL, risk EVs, ADM gate."""

from __future__ import annotations

from process_blueprint.ai_risk import assess, seed_readiness
from process_blueprint.facts import ProcessFacts


# ------------------------------------------------------------- decision tree --
def test_rules_always_win(sample_facts):
    out = assess(sample_facts, {"rule_expressible": True, "task_type": "classification"})
    assert out["decision"]["route"] == "Automate_Rules"
    assert out["decision"]["pattern"] is None
    # AP-AI2 guard fires: AI was contemplated where rules suffice
    ap2 = next(c for c in out["anti_pattern_checks"] if c["id"] == "AP-AI2")
    assert ap2["status"] == "fail"


def test_ml_route_requires_data(sample_facts):
    """Classification with unconfirmed labels must DEFER, not proceed."""
    out = assess(sample_facts, {"rule_expressible": False, "task_type": "classification"})
    assert out["decision"]["route"] == "Defer"
    assert "Standardise_First" in out["data_readiness"]["for_route"]["precursors"]
    # labels confirmed but the 60-case log still fails the volume critical (≥3):
    # the sample alone is not a training set — still Defer. Correct per playbook.
    still = assess(sample_facts, {"rule_expressible": False, "task_type": "classification",
                                  "readiness": {"labelling": 4}})
    assert still["decision"]["route"] == "Defer"
    assert "volume" in still["data_readiness"]["for_route"]["failing"]
    # operator confirms the true historical volume AND labels → gate passes
    out2 = assess(sample_facts, {"rule_expressible": False, "task_type": "classification",
                                 "readiness": {"labelling": 4, "volume": 4}})
    assert out2["decision"]["route"] == "Augment_AI"
    assert out2["decision"]["pattern"] == "Classification"


def test_llm_route_blocked_without_grounding(sample_facts):
    out = assess(sample_facts, {"rule_expressible": False, "task_type": "language",
                                "error_tolerance_ok": True, "groundable": False})
    assert out["decision"]["route"] == "Keep_Manual"


def test_high_stakes_agent_kept_manual(sample_facts):
    out = assess(sample_facts, {"rule_expressible": False, "task_type": "multi_step",
                                "stakes": "high"})
    assert out["decision"]["route"] == "Keep_Manual"
    out2 = assess(sample_facts, {"rule_expressible": False, "task_type": "multi_step",
                                 "stakes": "low"})
    assert out2["decision"]["route"] == "Augment_AI"
    assert out2["decision"]["pattern"] == "Agent"


def test_unanswered_questions_stay_conservative(sample_facts):
    out = assess(sample_facts)  # no answers at all
    assert out["decision"]["route"] == "Pending"
    open_ids = {q["id"] for q in out["open_questions"]}
    assert {"task_type", "stakes", "affects_individuals"} <= open_ids
    # unknown stakes are treated as HIGH → human-in-the-loop
    assert out["hitl"]["stakes"] == "high"
    assert out["hitl"]["stakes_assumed"] is True
    assert out["hitl"]["pattern"] == "human_in_the_loop"


# ---------------------------------------------------------------- HITL rules --
def test_hitl_by_stakes(sample_facts):
    med = assess(sample_facts, {"stakes": "medium"})
    assert med["hitl"]["pattern"] == "human_on_the_loop"
    assert med["hitl"]["auto_process_threshold"] == 0.90
    low = assess(sample_facts, {"stakes": "low"})
    assert low["hitl"]["pattern"] == "human_over_the_loop"
    # ADM overrides stakes: individuals affected + solely automated ⇒ in-the-loop
    adm = assess(sample_facts, {"stakes": "low", "affects_individuals": True,
                                "solely_automated": True})
    assert adm["hitl"]["pattern"] == "human_in_the_loop"
    assert adm["adm_gate"]["applies"] is True


# ------------------------------------------------------------------ risk EVs --
def test_ai_risk_register_matches_playbook_example(sample_facts):
    """Post-mitigation AI EV ≈ £4,400 (playbook §4.3 worked example)."""
    out = assess(sample_facts, {"rule_expressible": False, "task_type": "classification",
                                "readiness": {"labelling": 4}})
    ai_rows = [r for r in out["risk_register"] if r["id"].startswith("R")]
    assert len(ai_rows) == 5
    assert sum(r["post_ev_gbp"] for r in ai_rows) == 4400
    # project risks always present; pre-mitigation EV strictly higher than post
    totals = out["total_risk_ev_gbp"]
    assert totals["pre_mitigation"] > totals["post_mitigation"] > 0


def test_rules_route_carries_no_ai_risks(sample_facts):
    out = assess(sample_facts, {"rule_expressible": True})
    assert all(not r["id"].startswith("R") for r in out["risk_register"])
    assert any(r["id"].startswith("P") for r in out["risk_register"])  # project risks remain


# ------------------------------------------------------------------ ADM gate --
def test_adm_gate_is_jurisdiction_aware_with_freshness(sample_facts):
    ksa = assess(sample_facts, {"jurisdiction": "KSA"})
    assert "SDAIA" in ksa["adm_gate"]["regulator"]
    assert any("LLM" in r or "localisation" in r for r in ksa["adm_gate"]["requirements"])
    assert ksa["adm_gate"]["research_date"] == "2026-07-02"
    assert "re-verify" in ksa["adm_gate"]["freshness_warning"].lower()
    eu = assess(sample_facts, {"jurisdiction": "EU"})
    assert "AI Act" in eu["adm_gate"]["adm_rule"]


# ------------------------------------------------------- integration & shape --
def test_engine_attaches_conservative_assessment(sample_facts):
    ai = sample_facts.ai_assessment
    assert ai["decision"]["route"] == "Pending"
    assert ai["jurisdiction"] == "UK"
    # ECRS anti-pattern guard reflects the redesign gate state
    ap1 = next(c for c in ai["anti_pattern_checks"] if c["id"] == "AP-AI1")
    assert ap1["status"] == "blocked"  # P2P has open E/S/S recs gating automation


def test_readiness_autoseed_from_log(sample_facts):
    r = seed_readiness(sample_facts)
    assert r["structure"]["score"] == 5          # it parsed → digital + consistent
    assert r["volume"]["score"] >= 2             # 60 cases
    assert r["labelling"]["score"] == 1          # never assumed without confirmation


def test_assessment_survives_roundtrip(sample_facts):
    rebuilt = ProcessFacts.from_dict(sample_facts.to_dict())
    assert rebuilt.ai_assessment["decision"]["route"] == \
        sample_facts.ai_assessment["decision"]["route"]
