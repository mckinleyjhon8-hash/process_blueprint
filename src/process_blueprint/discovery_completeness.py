"""
discovery_completeness.py — the Discovery playbook's completeness model (E1c).

Six domains (Process, Systems, Data, Financial, People, Compliance), each a
point-scored checklist with **Must** thresholds. The engine auto-grants every
item the event log can prove (that's the tool's superpower — a log upload
instantly evidences most of the Process domain at E1 grade); the operator
answers the rest as guided yes/no items, each carrying the playbook's exact
follow-up question so a junior consultant knows what to go and ask.

Gates implemented:
  * per-domain Must / Should / Complete levels
  * overall = min(domains)×0.4 + mean(domains)×0.4 + all-Musts-met×20
  * ROI gate: overall <50 → blocked · 50–70 → caveated · ≥70 → pass
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .facts import ProcessFacts

# --------------------------------------------------------------------------- #
# Auto signals — what the event log itself can evidence (all E1 / measured)
# --------------------------------------------------------------------------- #
def _auto_signals(facts: ProcessFacts, has_sop_rules: bool) -> Dict[str, bool]:
    flow_edges = (facts.flow or {}).get("edges", [])
    branching = len({e["source"] for e in flow_edges}) < len(flow_edges)
    res = facts.resources or {}
    tp = facts.time_profile or {}
    return {
        "process.step_list": bool(facts.activity_frequencies),
        "process.step_sequence": bool(facts.top_variants),
        "process.step_times": bool(flow_edges),
        "process.wait_times": bool(facts.bottlenecks or flow_edges),
        "process.decision_points": branching,
        "process.exception_paths": tp.get("exception_rate_pct") is not None
        and facts.n_variants > 1,
        "process.handoffs": bool(res.get("handovers")),
        "process.variation": facts.n_variants > 0,
        "systems.log_availability": True,  # we are literally analysing one
        "data.data_quality": facts.n_events > 0,
        "data.data_format": True,  # digital, structured — it parsed
        "data.volume_trend": facts.n_events > 0,
        "financial.volume": facts.n_cases > 0,
        "people.roles": bool(res.get("roles")),
        "people.spof": "single_points_of_failure" in res,
        "people.capacity": bool(facts.bottlenecks) and bool(res),
        "compliance.mandatory_controls": has_sop_rules,
        "compliance.control_effectiveness": has_sop_rules,
    }


# --------------------------------------------------------------------------- #
# Domain checklists — points / Must flags / follow-up questions (playbook §3.2)
# --------------------------------------------------------------------------- #
def _item(id_: str, label: str, points: int, critical: bool, question: str,
          auto: bool = False) -> Dict[str, Any]:
    return {"id": id_, "label": label, "points": points, "critical": critical,
            "question": question, "auto": auto}


DOMAINS: Dict[str, Dict[str, Any]] = {
    "process": {
        "label": "Process", "must": 60, "should": 75, "complete": 90,
        "items": [
            _item("process.step_list", "Step list (incl. undocumented)", 20, True,
                  "What happens between the steps we see — anything in between?", auto=True),
            _item("process.step_sequence", "Actual step sequence", 15, True,
                  "Then what happens? What's the very next thing you do?", auto=True),
            _item("process.step_times", "Time per step (with range)", 15, True,
                  "How long does this step take — what's fast? What's slow?", auto=True),
            _item("process.wait_times", "Wait time per step (with cause)", 10, False,
                  "What are you waiting for at this point?", auto=True),
            _item("process.decision_points", "Decision points with rules", 10, True,
                  "How do you decide whether to do X or Y — what determines the path?", auto=True),
            _item("process.exception_paths", "Exception paths + frequency", 10, True,
                  "What happens when this isn't a standard case — how often?", auto=True),
            _item("process.handoffs", "Hand-off points (who, what, format)", 10, False,
                  "Who do you hand this to? What exactly do you give them?", auto=True),
            _item("process.owner", "Process owner named", 5, False,
                  "Who is accountable for this process working well?"),
            _item("process.variation", "Variation between operators", 5, False,
                  "Does everyone do this the same way, or are there different methods?", auto=True),
        ],
    },
    "systems": {
        "label": "Systems", "must": 55, "should": 75, "complete": 90,
        "items": [
            _item("systems.system_list", "Every system touched, listed", 25, True,
                  "What systems do you use during this process — list every one."),
            _item("systems.data_flows", "Data flow between systems mapped", 20, True,
                  "How does data get from system A to system B — automatic or manual?"),
            _item("systems.re_entry", "Re-entry points counted", 20, True,
                  "Do you ever type the same information into more than one system?"),
            _item("systems.integration_status", "Integration status known", 15, False,
                  "Are the systems connected, or do you transfer data manually?"),
            _item("systems.access", "Access / licensing constraints", 10, False,
                  "Does everyone who needs access to the system have it?"),
            _item("systems.log_availability", "System log availability", 10, False,
                  "Does the system keep an activity log we could extract?", auto=True),
        ],
    },
    "data": {
        "label": "Data", "must": 45, "should": 70, "complete": 90,
        "items": [
            _item("data.input_fields", "Input data fields identified", 20, True,
                  "What information do you need before you can begin this step?"),
            _item("data.sources", "Source of each input known", 20, True,
                  "Where does each data field come from — who provides it, which system?"),
            _item("data.data_quality", "Data quality issues assessed", 15, True,
                  "How often is the data you receive wrong, incomplete, or late?", auto=True),
            _item("data.data_format", "Format documented (digital/paper)", 15, False,
                  "In what format do you receive the input — form, email, spreadsheet, paper?",
                  auto=True),
            _item("data.volume_trend", "Volume and growth trend", 10, False,
                  "Is the volume growing, stable, or declining?", auto=True),
            _item("data.retention", "Retention / archival requirements", 10, False,
                  "How long must this data be kept — any regulatory requirement?"),
            _item("data.ownership", "Data ownership assigned", 10, False,
                  "Who is responsible for this data being accurate and complete?"),
        ],
    },
    "financial": {
        "label": "Financial", "must": 40, "should": 65, "complete": 85,
        "items": [
            _item("financial.fte_count", "FTE allocation to the process", 20, True,
                  "How many people work on this, and what % of their time?"),
            _item("financial.fte_cost", "Fully-loaded FTE cost", 15, True,
                  "What is the fully-loaded cost per FTE (salary + NI + pension + overhead)?"),
            _item("financial.volume", "Monthly transaction volume", 15, True,
                  "How many transactions per month?", auto=True),
            _item("financial.cost_per_txn", "Cost per transaction", 15, False,
                  "What does it cost to process one transaction?"),
            _item("financial.error_cost", "Error / rework cost", 10, False,
                  "When an error occurs, how much time or money does fixing it take?"),
            _item("financial.penalty_cost", "Late penalties / missed discounts", 10, False,
                  "Do you incur late fees or miss early-payment discounts? How much?"),
            _item("financial.tech_cost", "Technology / licence cost", 10, False,
                  "What does the supporting system licence cost?"),
            _item("financial.revenue_impact", "Revenue impact", 5, False,
                  "Does this process's speed or quality affect retention or revenue?"),
        ],
    },
    "people": {
        "label": "People", "must": 40, "should": 65, "complete": 85,
        "items": [
            _item("people.roles", "Roles involved (who does what)", 20, True,
                  "Who does each step — what role, not what person?", auto=True),
            _item("people.spof", "Single-points-of-failure identified", 20, True,
                  "If this person is off sick, who else can do this step?", auto=True),
            _item("people.skills", "Skill / training level per role", 15, False,
                  "What training does someone need before they can do this step?"),
            _item("people.delegation", "Approval / delegation depth", 15, False,
                  "How many levels of approval does this process require?"),
            _item("people.capacity", "Capacity constraint located", 15, False,
                  "Is this role a bottleneck — do they have a queue of work waiting?", auto=True),
            _item("people.cross_training", "Cross-training status", 10, False,
                  "How many people can cover this role in an absence?"),
            _item("people.satisfaction", "Staff frustration signals", 5, False,
                  "What do people say about this process — is it a frustration point?"),
        ],
    },
    "compliance": {
        "label": "Compliance", "must": 50, "should": 70, "complete": 90,
        "items": [
            _item("compliance.regulations", "Applicable regulations identified", 25, True,
                  "What regulations or standards govern this process?"),
            _item("compliance.mandatory_controls", "Mandatory controls documented", 25, True,
                  "Which steps are required by regulation — which can't be removed?", auto=True),
            _item("compliance.audit_findings", "Recent audit findings known", 15, False,
                  "Any audit findings or non-conformances on this process?"),
            _item("compliance.control_effectiveness", "Control effectiveness checked", 15, False,
                  "When did the control step last catch a real error?", auto=True),
            _item("compliance.compliance_cost", "Compliance effort quantified", 10, False,
                  "How much time is spent specifically on compliance activities?"),
            _item("compliance.reg_change", "Regulatory change horizon", 10, False,
                  "Any upcoming regulatory changes that will affect this process?"),
        ],
    },
}


def compute(
    facts: ProcessFacts,
    manual_answers: Optional[Dict[str, bool]] = None,
    has_sop_rules: bool = False,
) -> Dict[str, Any]:
    """Score all six domains; auto-grant what the log proves, apply the gates."""
    manual = manual_answers or {}
    auto = _auto_signals(facts, has_sop_rules)

    domains_out: Dict[str, Any] = {}
    scores: List[float] = []
    all_musts_met = True
    top_gaps: List[Dict[str, str]] = []

    for name, spec in DOMAINS.items():
        total = sum(i["points"] for i in spec["items"])
        earned = 0
        items_out = []
        for item in spec["items"]:
            # auto items fall back to manual confirmation when the log can't
            # evidence them (e.g. roles/SPOF on a log without org:resource)
            auto_granted = item["auto"] and bool(auto.get(item["id"]))
            granted = auto_granted or bool(manual.get(item["id"]))
            status = ("auto" if auto_granted
                      else "manual" if granted
                      else "missing")
            if granted:
                earned += item["points"]
            elif item["critical"]:
                top_gaps.append({"domain": name, "item": item["label"],
                                 "question": item["question"]})
            items_out.append({**{k: item[k] for k in
                                 ("id", "label", "points", "critical", "question")},
                              "granted": granted, "status": status})
        score = round(100.0 * earned / total, 1)
        scores.append(score)
        level = ("complete" if score >= spec["complete"]
                 else "should" if score >= spec["should"]
                 else "must" if score >= spec["must"]
                 else "below_must")
        if score < spec["must"]:
            all_musts_met = False
        domains_out[name] = {
            "label": spec["label"], "score": score, "level": level,
            "must": spec["must"], "should": spec["should"], "complete": spec["complete"],
            "items": items_out,
        }

    overall = round(min(scores) * 0.4 + (sum(scores) / len(scores)) * 0.4
                    + (20.0 if all_musts_met else 0.0), 1)
    roi_gate = ("pass" if overall >= 70
                else "caveated" if overall >= 50
                else "blocked")

    return {
        "domains": domains_out,
        "overall": overall,
        "all_musts_met": all_musts_met,
        "roi_gate": roi_gate,
        "roi_gate_note": {
            "pass": "Evidence base sufficient for a client-facing ROI case.",
            "caveated": "ROI may be presented only with wide confidence bands and explicit caveats.",
            "blocked": "No ROI calculation may be presented — critical discovery gaps remain.",
        }[roi_gate],
        "top_gaps": top_gaps[:8],
    }
