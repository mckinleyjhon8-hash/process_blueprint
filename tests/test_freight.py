"""End-to-end test on the UK freight-brokerage SOP log + the compliance check."""

from __future__ import annotations

import pytest

from process_blueprint.engine import analyze_dataframe
from tests.freight_log import build_freight_log, check_sop_compliance


@pytest.fixture(scope="module")
def freight():
    df = build_freight_log(n_cases=600, seed=11)  # >500 -> alignments skipped (fast)
    return df, analyze_dataframe(df, process_type="UK Freight Brokerage")


def test_log_is_rich_and_sop_shaped(freight):
    df, facts = freight
    assert facts.n_cases == 600
    assert facts.n_activities >= 25          # the full SOP activity set
    assert facts.n_variants >= 20            # many real paths
    # signature SOP activities are present
    acts = set(facts.activity_frequencies)
    assert {"Capture Inquiry", "Award Carrier", "Capture POD", "Close Job"} <= acts


def test_conformance_and_diagnostics(freight):
    _, facts = freight
    assert facts.model.fitness is not None
    assert facts.bottlenecks, "expected bottlenecks (e.g. customs, late claims)"
    assert facts.rework_activities, "expected rework (re-sourcing, etc.)"


def test_compliance_check_catches_injected_breaches(freight):
    df, _ = freight
    report = check_sop_compliance(df)
    rules = report["rules"]
    # the deliberately injected control breaches must be detected
    assert rules["sanctions_check_missing"]["violations"] > 0
    assert rules["ocrs_check_missing"]["violations"] > 0
    assert rules["claim_outside_9_day_window"]["violations"] > 0
    # and these should be a minority, not the whole log
    assert rules["sanctions_check_missing"]["pct_of_cases"] < 15
