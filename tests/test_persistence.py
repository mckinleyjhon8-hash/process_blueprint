"""Tests for the ProcessFacts -> Supabase row mapping (pure, no network)."""

from __future__ import annotations

from process_blueprint.engine import analyze_dataframe
from process_blueprint.persistence import run_row, facts_row


def test_run_row_shape(sample_df):
    facts = analyze_dataframe(sample_df, process_type="Procure-to-Pay")
    row = run_row(facts, engagement_id="eng-123")
    assert row["engagement_id"] == "eng-123"
    assert row["n_cases"] == 60
    assert row["algorithm"] == "inductive"
    assert row["status"] == "completed"


def test_facts_row_shape_and_jsonb(sample_df):
    facts = analyze_dataframe(sample_df, process_type="Procure-to-Pay")
    row = facts_row(facts, run_id="run-456")
    assert row["run_id"] == "run-456"
    assert row["schema_version"] == "1.1"
    assert row["n_variants"] == 3
    # queryable columns mirror the model metrics
    assert row["model_fitness"] == facts.model.fitness
    assert row["model_precision"] == facts.model.precision
    # full contract preserved in the jsonb payload
    assert isinstance(row["facts"], dict)
    assert row["facts"]["n_cases"] == 60
    assert "bottlenecks" in row["facts"]
