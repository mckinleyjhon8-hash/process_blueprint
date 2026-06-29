"""Phase-2 tests: ProcessFacts -> brief. Uses a fake chat model (no API key)."""

from __future__ import annotations

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from process_blueprint.brief import generate_brief, build_context, health_score
from process_blueprint.brief import redact


def _fake(text: str) -> FakeListChatModel:
    return FakeListChatModel(responses=[text])


# --- scoring ---------------------------------------------------------------
def test_health_score_on_sample(sample_facts):
    score, grade = health_score(sample_facts)
    # fitness 1.0, precision ~0.97, gen ~0.82, simplicity ~0.89 -> ~94 -> A
    assert score is not None
    assert score >= 85
    assert grade.startswith("A")


def test_health_score_handles_missing_metrics(sample_facts):
    import copy

    f = copy.deepcopy(sample_facts)
    f.model.fitness = None
    f.model.precision = None
    f.model.generalization = None
    f.model.simplicity = None
    score, grade = health_score(f)
    assert score is None
    assert "insufficient" in grade.lower()


# --- audience-aware context (leak prevention by construction) ---------------
def test_internal_digest_includes_model_quality(sample_facts):
    d = build_context(sample_facts, "internal")
    assert "model_quality" in d
    assert d["model_quality"]["fitness"] is not None


def test_client_digest_omits_model_quality(sample_facts):
    d = build_context(sample_facts, "client")
    assert "model_quality" not in d          # the model never even sees it
    assert "health" in d                      # business-safe summary still present


# --- brief generation ------------------------------------------------------
def test_internal_brief_generation(sample_facts):
    canned = "# Brief\n## 1. Executive Summary\nFitness 1.0 via inductive miner."
    result = generate_brief(sample_facts, audience="internal", llm=_fake(canned))
    assert result.audience == "internal"
    assert result.markdown == canned
    assert result.health_score >= 85
    assert result.model_name  # records which model produced it


def test_client_brief_clean_has_no_warnings(sample_facts):
    clean = (
        "# Process Brief\n## 1. Executive Summary\n"
        "Invoice approvals add about 53 hours of delay, costing time and money."
    )
    result = generate_brief(sample_facts, audience="client", llm=_fake(clean))
    assert result.audience == "client"
    assert result.redaction_warnings == []


def test_client_brief_flags_leaked_internal_terms(sample_facts):
    leaky = "Our pm4py conformance analysis of the event log found issues."
    result = generate_brief(sample_facts, audience="client", llm=_fake(leaky))
    assert "pm4py" in result.redaction_warnings
    assert "conformance" in result.redaction_warnings
    assert "event log" in result.redaction_warnings


def test_invalid_audience_raises(sample_facts):
    import pytest

    with pytest.raises(ValueError):
        generate_brief(sample_facts, audience="nonsense", llm=_fake("x"))


# --- redact unit -----------------------------------------------------------
def test_redact_scan_and_clean():
    assert redact.scan("uses pm4py and a Petri net") == ["petri net", "pm4py"]
    cleaned = redact.clean("uses pm4py here")
    assert "pm4py" not in cleaned.lower()


def test_redact_no_false_positives():
    # 'xes' must not match inside 'indexes'/'taxes'; 'dfg' not inside words.
    assert redact.scan("we reviewed indexes, taxes and boxes of invoices") == []
    # but a genuine standalone term is still caught
    assert "xes" in redact.scan("exported to data.xes")
    assert "event log" in redact.scan("the raw event log was ingested")
