"""Declarative compliance engine + BPMN conformance."""

from __future__ import annotations

import os

from process_blueprint.compliance import (
    check_rules,
    FREIGHT_SOP_RULES,
    write_reference_bpmn,
    bpmn_conformance,
)
from tests.freight_log import build_freight_log


def test_rules_catch_breaches_in_dirty_log():
    df = build_freight_log(400, seed=11, deviations=True)
    rules = check_rules(df, FREIGHT_SOP_RULES)["rules"]
    assert rules["sanctions_check_missing"]["violations"] > 0
    assert rules["claim_outside_9_day_window"]["violations"] > 0
    assert "SOP 1.2" in rules["sanctions_check_missing"]["label"]


def test_clean_log_has_no_breaches():
    df = build_freight_log(300, seed=5, deviations=False)
    rules = check_rules(df, FREIGHT_SOP_RULES)["rules"]
    assert sum(r["violations"] for r in rules.values()) == 0


def test_bpmn_conformance_flags_deviations(tmp_path):
    # Reference BPMN discovered from a clean "to-be" log…
    clean = build_freight_log(300, seed=3, deviations=False)
    bpmn_path = os.path.join(tmp_path, "reference.bpmn")
    write_reference_bpmn(clean, bpmn_path)
    assert os.path.getsize(bpmn_path) > 0

    # …a deviation-laden log should not perfectly conform to it.
    dirty = build_freight_log(300, seed=11, deviations=True)
    res = bpmn_conformance(dirty, bpmn_path)
    assert 0.0 <= res["log_fitness"] <= 1.0
    assert res["log_fitness"] < 1.0

    # the clean log fits its own model at least as well as the dirty one
    clean_res = bpmn_conformance(clean, bpmn_path)
    assert clean_res["log_fitness"] >= res["log_fitness"]
