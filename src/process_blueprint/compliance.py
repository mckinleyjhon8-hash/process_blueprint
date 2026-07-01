"""
compliance.py — declarative SOP conformance + BPMN conformance.

Two complementary ways to check a real event log against a documented process:

1. `check_rules(df, rules)` — a tiny *declarative* rule engine (the kind a full
   DECLARE/log-skeleton checker generalises). Each rule is a dict:
     - existence:    activity must occur (optionally only when `when` occurred)
     - precedence:   `before` must occur before `after`
     - within_days:  `b` must occur within `days` calendar days of `a`
   Returns per-rule violation counts + example cases. This generalises the
   hand-written freight check; `FREIGHT_SOP_RULES` encodes the SOP controls.

2. `bpmn_conformance(df, bpmn_path)` — checks the log against a *documented*
   BPMN model (e.g. a `.bpmn20.xml`) via pm4py: read BPMN → Petri net →
   token-replay fitness, plus the activities present in the log but not the
   model. `write_reference_bpmn(df, path)` discovers a BPMN to use as the
   reference (e.g. from a known-good "to-be" log).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"
_KEYS = dict(activity_key=ACT, timestamp_key=TS, case_id_key=CASE)


# --- the UK freight-brokerage SOP controls, expressed declaratively ---------
FREIGHT_SOP_RULES: List[Dict[str, Any]] = [
    {"id": "sanctions_check_missing",
     "label": "Sanctions check skipped on a booking · SOP 1.2",
     "kind": "existence", "activity": "Sanctions Check", "when": "Customer Accepts Quote"},
    {"id": "ocrs_check_missing",
     "label": "OCRS health gate skipped before award · SOP 4.7",
     "kind": "existence", "activity": "OCRS Check", "when": "Award Carrier"},
    {"id": "cmr_after_pickup",
     "label": "CMR issued after pickup · SOP 5.1",
     "kind": "precedence", "before": "Issue CMR", "after": "Confirm Pickup"},
    {"id": "kyc_after_award",
     "label": "Carrier KYC after award · SOP 2.3/4",
     "kind": "precedence", "before": "Carrier KYC", "after": "Award Carrier"},
    {"id": "claim_outside_9_day_window",
     "label": "Claim outside BIFA 9-day window · SOP 7.6",
     "kind": "within_days", "a": "Confirm Delivery", "b": "Handle Claim", "days": 9},
]


def check_rules(df: pd.DataFrame, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run a set of declarative rules over an event log; return a findings report."""
    found: Dict[str, List[str]] = {r["id"]: [] for r in rules}

    for case_id, g in df.sort_values(TS).groupby(CASE):
        acts = set(g[ACT])
        first_ts = dict(g.groupby(ACT)[TS].min())
        for r in rules:
            k = r["kind"]
            if k == "existence":
                scope_ok = r.get("when") is None or r["when"] in acts
                if scope_ok and r["activity"] not in acts:
                    found[r["id"]].append(case_id)
            elif k == "precedence":
                b, a = r["before"], r["after"]
                if b in first_ts and a in first_ts and first_ts[b] > first_ts[a]:
                    found[r["id"]].append(case_id)
            elif k == "within_days":
                a, b = r["a"], r["b"]
                if a in first_ts and b in first_ts:
                    if (first_ts[b] - first_ts[a]).days > r["days"]:
                        found[r["id"]].append(case_id)

    n = int(df[CASE].nunique())
    rule_meta = {r["id"]: r.get("label", r["id"]) for r in rules}
    return {
        "n_cases": n,
        "rules": {
            rid: {
                "label": rule_meta[rid],
                "violations": len(cases),
                "pct_of_cases": round(100 * len(cases) / n, 1) if n else 0.0,
                "example_cases": cases[:3],
            }
            for rid, cases in found.items()
        },
    }


# --- BPMN conformance (against a documented model) --------------------------
def write_reference_bpmn(df: pd.DataFrame, path: str) -> str:
    """Discover a BPMN model from a (reference) log and write it to `path`."""
    import pm4py

    bpmn = pm4py.discover_bpmn_inductive(df, **_KEYS)
    pm4py.write_bpmn(bpmn, path, auto_layout=False)  # layout needs Graphviz; conformance doesn't
    return path


def bpmn_conformance(df: pd.DataFrame, bpmn_path: str) -> Dict[str, Any]:
    """Check the log against a documented BPMN model; return fitness + deviations."""
    import pm4py

    bpmn = pm4py.read_bpmn(bpmn_path)
    net, im, fm = pm4py.convert_to_petri_net(bpmn)
    fit = pm4py.fitness_token_based_replay(df, net, im, fm, **_KEYS)

    model_acts = {t.label for t in net.transitions if t.label is not None}
    log_acts = set(str(a) for a in df[ACT].unique())
    return {
        "log_fitness": round(float(fit.get("log_fitness", 0.0)), 4),
        "pct_fitting_traces": round(float(fit.get("percentage_of_fitting_traces", 0.0)), 1),
        "model_activities": len(model_acts),
        "log_activities": len(log_acts),
        "activities_not_in_model": sorted(log_acts - model_acts),
    }
