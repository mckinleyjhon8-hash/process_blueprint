"""End-to-end test on the comprehensive enterprise P2P log (moderate size)."""

from __future__ import annotations

import pytest

from process_blueprint.engine import analyze_dataframe
from tests.enterprise_log import build_enterprise_log


@pytest.fixture(scope="module")
def enterprise_facts():
    df = build_enterprise_log(n_cases=250, seed=7)
    return df, analyze_dataframe(df, process_type="Procure-to-Pay")


def test_log_is_rich(enterprise_facts):
    df, facts = enterprise_facts
    assert facts.n_cases == 250
    assert facts.n_events > 2500            # ~12-16 events/case
    assert facts.n_activities >= 14         # full activity set incl. exceptions
    assert facts.n_variants >= 15           # genuinely many distinct paths


def test_conformance_computed(enterprise_facts):
    _, facts = enterprise_facts
    assert facts.model.fitness is not None
    assert 0.0 < facts.model.fitness <= 1.0
    assert facts.model.precision is not None


def test_bottlenecks_and_rework(enterprise_facts):
    _, facts = enterprise_facts
    assert facts.bottlenecks, "expected bottlenecks in a realistic log"
    # rework loops exist (re-approval, re-match, re-receive)
    assert facts.rework_activities, "expected rework in a realistic log"
    repeated = set(facts.rework_activities)
    assert repeated & {"Match Invoice", "Receive Goods", "Approve Requisition",
                       "Approve Purchase Order", "Inspect Goods", "Create Purchase Requisition"}


def test_cycle_time_realistic(enterprise_facts):
    _, facts = enterprise_facts
    # business-hours timing over many steps -> days, not seconds
    assert facts.avg_cycle_time_seconds > 3600 * 24


def test_facts_serialisable(enterprise_facts):
    _, facts = enterprise_facts
    payload = facts.to_json()
    assert '"schema_version": "1.0"' in payload
