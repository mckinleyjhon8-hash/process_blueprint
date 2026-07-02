"""Elite Phase E1: insights (pm4py activation), benchmarks, discovery completeness."""

from __future__ import annotations

from process_blueprint.engine import analyze_dataframe
from process_blueprint.benchmarks import match_family, apply_benchmarks
from process_blueprint.discovery_completeness import compute as completeness
from process_blueprint.facts import ProcessFacts


# ---------------------------------------------------------------- insights --
def test_flow_performance_dfg(sample_facts):
    """The performance DFG must carry frequency AND wait stats per edge."""
    assert sample_facts.flow["n_edges"] > 0
    edge = sample_facts.flow["edges"][0]
    assert edge["frequency"] > 0
    assert edge["mean_wait_seconds"] >= 0
    assert "median_wait_seconds" in edge


def test_time_profile_percentiles_and_coverage(sample_facts):
    tp = sample_facts.time_profile
    assert tp["p10_seconds"] <= tp["p50_seconds"] <= tp["p90_seconds"]
    assert tp["heavy_tail_ratio"] >= 1.0
    assert 0 < tp["top_variant_coverage_pct"] <= 100
    assert tp["exception_rate_pct"] == round(100 - tp["top5_coverage_pct"], 1)
    # P2P sample: rework variant exists, so FPY < 100
    assert tp["fpy_pct"] < 100


def test_resources_from_freight_log():
    """The freight log carries org:resource — roles/handovers/SPOF must appear."""
    from tests.freight_log import build_freight_log

    facts = analyze_dataframe(build_freight_log(80, seed=11), process_type="UK Freight Brokerage")
    res = facts.resources
    assert res["n_resources"] >= 10
    assert res["roles"][0]["n_events"] > 0
    assert any(h["count"] > 0 for h in res["handovers"])
    assert isinstance(res["single_points_of_failure"], list)
    # roles are named business roles, not blank
    assert all(r["resource"] for r in res["roles"])


def test_resources_absent_without_column(sample_facts):
    """P2P sample has no org:resource — resources must be empty, not crash."""
    assert sample_facts.resources == {}


# -------------------------------------------------------------- benchmarks --
def test_family_matching():
    assert match_family("Procure-to-Pay") == "accounts_payable"
    assert match_family("Order-to-Cash") == "order_fulfilment"
    assert match_family("Customer Onboarding") == "customer_onboarding"
    assert match_family("UK Freight Brokerage") == "generic"


def test_benchmark_positions_have_quartiles_and_sources(sample_facts):
    b = sample_facts.benchmarks
    assert b["family"] == "accounts_payable"
    by_metric = {p["metric"]: p for p in b["positions"]}
    lead = by_metric["lead_time_days"]
    # P2P sample avg ~2.5 days beats the 2.5-day top-quartile edge → Q4
    assert lead["quartile"] == "Q4"
    assert lead["target_value"] is None  # already top quartile
    assert lead["source"] and lead["grade"]
    assert lead["provenance"] == "measured"


def test_quartile_direction_lower_and_higher():
    facts = ProcessFacts(
        process_type="Accounts Payable", source_file="x",
        n_events=10, n_cases=5, n_activities=3, n_variants=2,
        avg_cycle_time_seconds=10 * 86400.0,  # 10 days: between p25(12) and median(8) → Q2
        median_cycle_time_seconds=9 * 86400.0,
    )
    facts.time_profile = {"fpy_pct": 97.0, "rework_case_rate_pct": 3.0,
                          "exception_rate_pct": 5.0, "heavy_tail_ratio": 2.0}
    b = apply_benchmarks(facts)
    by_metric = {p["metric"]: p for p in b["positions"]}
    assert by_metric["lead_time_days"]["quartile"] == "Q2"
    assert by_metric["lead_time_days"]["target_value"] == 5  # moderate ambition → p75
    assert by_metric["fpy_pct"]["quartile"] == "Q4"           # 97 ≥ p75 (96), higher-is-better
    assert by_metric["fpy_pct"]["target_value"] is None       # top quartile: hold, don't chase


def test_plausibility_flags_absurd_values():
    facts = ProcessFacts(
        process_type="Accounts Payable", source_file="x",
        n_events=10, n_cases=5, n_activities=3, n_variants=1,
        avg_cycle_time_seconds=200 * 86400.0,  # 200 days — outside plausible range
        median_cycle_time_seconds=1.0,
    )
    b = apply_benchmarks(facts)
    lead = next(p for p in b["positions"] if p["metric"] == "lead_time_days")
    assert lead["plausibility"] == "fail"


# ---------------------------------------------------- discovery completeness --
def test_log_auto_evidences_process_domain(sample_facts):
    d = sample_facts.discovery
    # a good event log alone must lift the Process domain past its Must gate
    assert d["domains"]["process"]["score"] >= 60
    # but Financial/Systems need human answers — they start below Must
    assert d["domains"]["systems"]["score"] < 55
    assert d["roi_gate"] == "blocked"
    assert any(g["domain"] == "financial" for g in d["top_gaps"])
    # every missing critical item carries the playbook's follow-up question
    assert all(g["question"] for g in d["top_gaps"])


def test_manual_answers_move_the_gates(sample_facts):
    answers = {
        "systems.system_list": True, "systems.data_flows": True, "systems.re_entry": True,
        "data.input_fields": True, "data.sources": True,
        "financial.fte_count": True, "financial.fte_cost": True,
        "financial.cost_per_txn": True, "financial.error_cost": True,
        # P2P log has no org:resource, so the operator confirms these manually
        "people.roles": True, "people.spof": True,
        "people.skills": True, "people.delegation": True,
        "compliance.regulations": True, "compliance.audit_findings": True,
        "process.owner": True,
    }
    d = completeness(sample_facts, manual_answers=answers, has_sop_rules=True)
    assert d["domains"]["systems"]["score"] >= 55
    assert d["domains"]["financial"]["score"] >= 40
    assert d["overall"] > sample_facts.discovery["overall"]
    assert d["roi_gate"] in ("caveated", "pass")


def test_facts_v11_roundtrip(sample_facts):
    """New layers must survive the Supabase jsonb roundtrip."""
    rebuilt = ProcessFacts.from_dict(sample_facts.to_dict())
    assert rebuilt.flow == sample_facts.flow
    assert rebuilt.time_profile == sample_facts.time_profile
    assert rebuilt.benchmarks == sample_facts.benchmarks
    assert rebuilt.discovery["overall"] == sample_facts.discovery["overall"]
    assert rebuilt.schema_version == "1.1"
