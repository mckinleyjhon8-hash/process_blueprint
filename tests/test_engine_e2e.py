"""End-to-end Phase-1 tests: event log → ProcessFacts."""

from __future__ import annotations

import json

from process_blueprint import analyze, ProcessFacts
from process_blueprint.engine import analyze_dataframe


def test_facts_volumes(sample_df):
    facts = analyze_dataframe(sample_df, process_type="Procure-to-Pay")
    assert isinstance(facts, ProcessFacts)
    assert facts.n_cases == 60
    assert facts.n_activities == 6          # 6 distinct activities
    assert facts.n_variants == 3            # happy / rework / skip
    assert facts.avg_cycle_time_seconds > 0
    assert facts.median_cycle_time_seconds > 0


def test_conformance_is_actually_computed(sample_df):
    """The original bug: fitness/precision were never populated. They must be now."""
    facts = analyze_dataframe(sample_df, algorithm="inductive")
    assert facts.model.algorithm == "inductive"
    assert facts.model.fitness is not None
    assert 0.0 <= facts.model.fitness <= 1.0
    # Model discovered from its own log should fit well.
    assert facts.model.fitness > 0.8
    assert facts.model.precision is not None


def test_bottleneck_is_the_injected_one(sample_df):
    facts = analyze_dataframe(sample_df)
    assert facts.bottlenecks, "expected at least one bottleneck"
    # The synthetic log injects long waits straight after 'Approve PO'.
    assert facts.bottlenecks[0].source == "Approve PO"
    assert facts.bottlenecks[0].mean_wait_seconds > 0


def test_rework_detected(sample_df):
    facts = analyze_dataframe(sample_df)
    # The rework variant repeats 'Approve PO' within a case.
    assert "Approve PO" in facts.rework_activities
    assert facts.rework_activities["Approve PO"] >= 1


def test_start_end_activities(sample_df):
    facts = analyze_dataframe(sample_df)
    assert "Create PO" in facts.start_activities
    assert "Pay Invoice" in facts.end_activities


def test_facts_json_roundtrip(sample_df):
    facts = analyze_dataframe(sample_df)
    payload = facts.to_json()
    parsed = json.loads(payload)
    assert parsed["schema_version"] == "1.0"
    assert parsed["n_cases"] == 60
    assert isinstance(parsed["top_variants"], list)
    assert isinstance(parsed["top_variants"][0]["sequence"], list)


def test_analyze_from_csv(sample_csv):
    facts = analyze(sample_csv, process_type="Procure-to-Pay")
    assert facts.n_cases == 60
    assert facts.source_file == sample_csv
    assert facts.model.fitness is not None


def test_facts_from_dict_roundtrip(sample_facts):
    """Supabase stores facts as jsonb; from_dict must rebuild an equivalent object."""
    rebuilt = ProcessFacts.from_dict(sample_facts.to_dict())
    assert rebuilt.n_cases == sample_facts.n_cases
    assert rebuilt.n_variants == sample_facts.n_variants
    assert rebuilt.model.fitness == sample_facts.model.fitness
    assert len(rebuilt.bottlenecks) == len(sample_facts.bottlenecks)
    assert rebuilt.bottlenecks[0].source == sample_facts.bottlenecks[0].source
    assert tuple(rebuilt.top_variants[0].sequence) == tuple(sample_facts.top_variants[0].sequence)
