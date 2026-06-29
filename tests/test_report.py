"""Tests for the branded HTML report builder."""

from __future__ import annotations

from process_blueprint.engine import analyze_dataframe
from process_blueprint.report import build_report_html

_BRIEF = """# Procure-to-Pay — Executive Brief

## 1. Executive Summary
The process is well structured but invoice approvals add delay.

## 2. Recommendations
- Introduce tiered approval thresholds
- Assign post-approval ownership
"""


def test_client_report_is_self_contained_and_safe(sample_facts):
    html = build_report_html(sample_facts, _BRIEF, audience="client")
    assert html.startswith("<!DOCTYPE html>")
    assert "Procure-to-Pay" in html
    assert "Primary process flow" in html and "<svg" in html
    assert "Executive Summary" in html
    # client deliverable must NOT expose engine mechanics
    assert "Model quality" not in html
    assert "fitness" not in html.lower()


def test_internal_report_includes_model_quality(sample_facts):
    html = build_report_html(sample_facts, _BRIEF, audience="internal")
    assert "Model quality" in html
    assert "Fitness" in html


def test_report_renders_compliance(sample_facts):
    compliance = {
        "n_cases": 100,
        "rules": {
            "sanctions_check_missing": {"violations": 6, "pct_of_cases": 6.0, "example_cases": []},
        },
    }
    html = build_report_html(sample_facts, _BRIEF, audience="client", compliance=compliance)
    assert "SOP compliance check" in html
    assert "Sanctions check skipped" in html


def test_report_without_brief_degrades_gracefully(sample_facts):
    html = build_report_html(sample_facts, None, audience="client")
    assert "has not been generated" in html
