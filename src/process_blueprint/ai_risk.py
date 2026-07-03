"""
ai_risk.py — the AI Decision & Risk engine (Elite Phase E3).

Implements the AI Decision & Risk playbook as deterministic logic:

  * §0.2 decision tree — rules > classical ML > LLM > human. The engine walks
    the tree per automation opportunity: what the log can answer is auto-
    derived; what needs a human is surfaced as an explicit question, and the
    route stays conservative (Keep_Manual / pending) until answered.
  * §2.2 data-readiness gating — five dimensions (0–5) with per-pattern hard
    minimums; failure defers AI behind Digitise_First / Standardise_First.
  * §3 HITL design — stakes-based human-in/on/over-the-loop selection with
    confidence thresholds. High stakes or ADM-regulated ⇒ human-in-the-loop,
    no auto-processing, non-negotiable.
  * §4 risk register — R1–R5 AI risks + the KB's project risks, quantified as
    expected values (probability × impact midpoints, pre/post mitigation).
  * ADM gate — jurisdiction-aware automated-decision-making requirements
    seeded from the regulatory landscape reference (research date 2026-07-02).
    Every entry carries a freshness stamp and a verify-against-regulator note:
    this domain moves quarterly and is NEVER presented as static truth.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .facts import ProcessFacts

RESEARCH_DATE = "2026-07-02"  # compliance landscape research date (re-verify quarterly)

# --------------------------------------------------------------------------- #
# §4.2 AI risk catalogue — midpoint probabilities / impacts (typical SME, GBP)
# --------------------------------------------------------------------------- #
AI_RISKS: List[Dict[str, Any]] = [
    {"id": "R1", "category": "AI_Hallucination",
     "label": "Hallucination / factual error reaches production",
     "pre_pct": 30, "post_pct": 7.5, "impact_gbp": 5000,
     "mitigation": "HITL review, confidence thresholds, groundedness checks, hallucination budget"},
    {"id": "R2", "category": "AI_Privacy_GDPR",
     "label": "Personal data sent to AI without DPIA/DPA safeguards",
     "pre_pct": 40, "post_pct": 7.5, "impact_gbp": 15000,
     "mitigation": "DPIA before deployment, DPA with provider, PII filtering, data minimisation"},
    {"id": "R3", "category": "AI_Cost_Overrun",
     "label": "Runaway API/compute cost",
     "pre_pct": 22, "post_pct": 5, "impact_gbp": 3000,
     "mitigation": "Per-transaction cost limits, spend caps, agent step limits, alerts at 80%"},
    {"id": "R4", "category": "AI_Model_Drift",
     "label": "Model accuracy degrades as data distribution shifts",
     "pre_pct": 50, "post_pct": 15, "impact_gbp": 10000,
     "mitigation": "Monthly accuracy monitoring, retrain trigger at −5%, OOD detection"},
    {"id": "R5", "category": "AI_Over_Reliance",
     "label": "Staff trust AI uncritically and stop catching errors",
     "pre_pct": 60, "post_pct": 25, "impact_gbp": 5000,
     "mitigation": "Explicit approve actions, injected known-error tests, 'AI suggests, you decide' training"},
]

# KB §7.2 project risks (apply to any automation, AI or rules)
PROJECT_RISKS: List[Dict[str, Any]] = [
    {"id": "P1", "category": "Data_Quality", "label": "Source data quality undermines automation",
     "pre_pct": 40, "post_pct": 15, "impact_gbp": 8000,
     "mitigation": "Data audit before build; validation rules at entry"},
    {"id": "P2", "category": "Scope_Creep", "label": "Requirements grow during build",
     "pre_pct": 32, "post_pct": 12, "impact_gbp": 10000,
     "mitigation": "Fixed scope agreement; change control"},
    {"id": "P3", "category": "Integration_Failure", "label": "Legacy systems resist integration",
     "pre_pct": 27, "post_pct": 10, "impact_gbp": 15000,
     "mitigation": "Technical proof-of-concept before commitment"},
    {"id": "P4", "category": "User_Adoption", "label": "Staff resist or work around the new process",
     "pre_pct": 30, "post_pct": 12, "impact_gbp": 6000,
     "mitigation": "Early involvement, training, visible quick wins"},
]

# --------------------------------------------------------------------------- #
# ADM landscape per jurisdiction (regulatory landscape reference, 2026-07-02)
# --------------------------------------------------------------------------- #
ADM_LANDSCAPE: Dict[str, Dict[str, Any]] = {
    "UK": {
        "label": "United Kingdom (UK-GDPR + DPA 2018)",
        "regulator": "ICO — ico.org.uk",
        "adm_rule": "Art 22 UK-GDPR: right not to be subject to solely automated decisions with "
                    "legal/significant effect; meaningful human review must be able to overturn.",
        "requirements": [
            "Human review with authority and competence to overturn (rubber-stamping = still 'solely automated')",
            "Mechanism for the individual to contest and obtain human intervention",
            "Transparency: document logic, significance and safeguards (Art 13/14)",
            "DPIA if processing personal data at scale or profiling",
        ],
        "verify": "Data (Use and Access) Act 2025 recasts the ADM regime — phase-in dates and "
                  "updated ICO guidance MUST be checked at ico.org.uk before relying on this gate.",
    },
    "EU": {
        "label": "European Union (EU-GDPR + AI Act 2024/1689)",
        "regulator": "EDPB / AI Office — edpb.europa.eu, eur-lex.europa.eu",
        "adm_rule": "Art 22 EU-GDPR plus the AI Act: HR/credit/eligibility systems are Annex III "
                    "high-risk — risk management, logging, human oversight, conformity duties.",
        "requirements": [
            "Art 22 safeguards (human intervention, contest) for solely automated decisions",
            "If Annex III high-risk (employment, credit, essential services): full AI Act high-risk duties",
            "Chatbot/AI-interaction transparency (users must know it's AI)",
            "DPIA + possible FRIA for high-risk deployments",
        ],
        "verify": "AI Act high-risk obligations phase in ~Aug 2026 (≈now) — confirm exact in-force "
                  "status against eur-lex.europa.eu before gating.",
    },
    "US": {
        "label": "United States (state patchwork + sector laws)",
        "regulator": "FTC + state AGs/CPPA — iapp.org tracker",
        "adm_rule": "No federal ADM right. California CPRA ADMT opt-out; CO/VA/CT profiling opt-outs; "
                    "most state laws require a data protection assessment for profiling.",
        "requirements": [
            "Check the specific states of affected individuals (CA strictest; ~18+ states in force)",
            "Provide profiling/ADMT opt-out where state law grants it",
            "Data protection assessment for profiling or sensitive data",
            "Sector overlays: HIPAA (health), GLBA (finance), FTC §5 for unfair AI practices",
        ],
        "verify": "State count changes quarterly; CPPA ADMT regulations may be finalised — "
                  "check iapp.org tracker and cppa.ca.gov.",
    },
    "KSA": {
        "label": "Saudi Arabia (PDPL, onshore)",
        "regulator": "SDAIA — sdaia.gov.sa",
        "adm_rule": "No statutory Art-22 equivalent, but consent-primary regime; financial data is "
                    "SENSITIVE; cross-border transfer has NO SCC mechanism.",
        "requirements": [
            "Explicit consent as the primary lawful basis (incl. financial data)",
            "Sending personal data to a foreign-hosted LLM is likely unlawful without consent/pseudonymisation",
            "Data localisation: prefer in-Kingdom processing",
            "Criminal liability exists for unlawful sensitive-data processing — specialist advice mandatory",
        ],
        "verify": "SDAIA transfer regulations evolve — check sdaia.gov.sa; criminal exposure makes "
                  "legal counsel non-optional here.",
    },
    "UAE_ONSHORE": {
        "label": "UAE onshore (Federal Decree-Law 45/2021)",
        "regulator": "UAE Data Office",
        "adm_rule": "No statutory Art-22 equivalent; consent-primary; financial data sensitive; "
                    "no SCC mechanism for transfers.",
        "requirements": [
            "Explicit consent for sensitive categories (incl. financial data)",
            "Foreign-hosted AI processing requires consent or adequacy — verify before design",
            "Criminal liability exists for certain violations",
        ],
        "verify": "Executive-regulation detail evolving — verify with UAE Data Office guidance.",
    },
    "UAE_DIFC": {
        "label": "UAE DIFC (Law No. 5/2020 — GDPR-like)",
        "regulator": "DIFC Commissioner of Data Protection — dp.difc.ae",
        "adm_rule": "Art-22 equivalent: right to human intervention for solely automated decisions "
                    "with legal/significant effect; SCCs and UK/EU adequacy available.",
        "requirements": [
            "Human-intervention right for solely automated significant decisions",
            "Transfers: DIFC adequacy (UK/EU) or SCCs + transfer impact assessment",
        ],
        "verify": "Check dp.difc.ae for post-2023-amendment updates.",
    },
    "CA": {
        "label": "Canada (PIPEDA; Quebec Law 25 strictest)",
        "regulator": "OPC — priv.gc.ca; CAI (Quebec) — cai.gouv.qc.ca",
        "adm_rule": "PIPEDA: consent + openness for ADM with significant effects. Quebec Law 25: "
                    "advance notice, right to observations and explanation, mandatory PIA.",
        "requirements": [
            "Inform individuals about ADM in advance (Quebec: statutory)",
            "Provide explanation + human recourse on request",
            "Quebec: PIA mandatory for such processing and for data leaving Quebec",
        ],
        "verify": "Bill C-27 / AIDA status uncertain — check priv.gc.ca; Law 25 final phases at cai.gouv.qc.ca.",
    },
}

# --------------------------------------------------------------------------- #
# §2.2 data-readiness dimensions + per-pattern minimums
# --------------------------------------------------------------------------- #
READINESS_DIMS = ["volume", "quality", "structure", "labelling", "recency"]

PATTERN_MINIMUMS: Dict[str, Dict[str, Any]] = {
    "Classification": {"total": 15, "critical": ["volume", "labelling"]},
    "Extraction": {"total": 15, "critical": ["volume", "quality"]},
    "Prediction": {"total": 15, "critical": ["volume", "recency"]},
    "RAG_Assistant": {"total": 12, "critical": ["quality", "structure"]},
    "Copilot": {"total": 10, "critical": ["structure", "recency"]},
    "Agent": {"total": 12, "critical": ["structure", "quality"]},
    "Conversational": {"total": 15, "critical": ["volume", "labelling"]},
}


def _volume_score(n_records: int) -> int:
    if n_records <= 0:
        return 0
    for score, floor in ((5, 5000), (4, 1000), (3, 200), (2, 50)):
        if n_records > floor:
            return score
    return 1


def seed_readiness(facts: ProcessFacts) -> Dict[str, Any]:
    """Auto-seed the five dimensions from what the event log proves; the
    operator confirms/overrides the rest (quality of source data, labels)."""
    return {
        "volume": {"score": _volume_score(facts.n_cases), "basis": "auto",
                   "note": f"{facts.n_cases} historical cases in the log"},
        "quality": {"score": 3, "basis": "assumed",
                    "note": "Log parsed cleanly; source-data error rate unconfirmed — operator to verify"},
        "structure": {"score": 5, "basis": "auto",
                      "note": "Fully digital, consistent schema (it parsed into the canonical log)"},
        "labelling": {"score": 1, "basis": "assumed",
                      "note": "Outcome labels unconfirmed — operator to verify labelled examples exist"},
        "recency": {"score": 4, "basis": "auto",
                    "note": "Log covers the current operating period"},
    }


def _readiness_gate(readiness: Dict[str, Any], pattern: str) -> Dict[str, Any]:
    spec = PATTERN_MINIMUMS.get(pattern)
    scores = {d: int(readiness[d]["score"]) for d in READINESS_DIMS}
    total = sum(scores.values())
    if spec is None:
        return {"total": total, "minimum": None, "gate": "n/a", "failing": []}
    failing = [d for d in spec["critical"] if scores[d] < 3]
    gate = "pass" if total >= spec["total"] and not failing else "fail"
    precursors = []
    if gate == "fail":
        if scores["volume"] < 3 or scores["recency"] < 3:
            precursors.append("Digitise_First")
        if scores["quality"] < 3 or scores["labelling"] < 3 or scores["structure"] < 3:
            precursors.append("Standardise_First")
    return {"total": total, "minimum": spec["total"], "critical": spec["critical"],
            "failing": failing, "gate": gate, "precursors": sorted(set(precursors))}


# --------------------------------------------------------------------------- #
# §3 HITL selection — stakes decide, compliance overrides
# --------------------------------------------------------------------------- #
def _hitl(stakes: str, adm_applies: bool) -> Dict[str, Any]:
    if adm_applies or stakes == "high":
        return {"pattern": "human_in_the_loop",
                "auto_process_threshold": None,
                "rationale": ("ADM-regulated or error cost >£500: a human acts on every AI output. "
                              "Never auto-process. Non-negotiable (playbook AP-AI4).")}
    if stakes == "medium":
        return {"pattern": "human_on_the_loop", "auto_process_threshold": 0.90,
                "rationale": "Error cost £50–£500: review low-confidence outputs + 10% random sample."}
    return {"pattern": "human_over_the_loop", "auto_process_threshold": 0.80,
            "rationale": "Error cost <£50 with deterministic guardrails: humans set rules and monitor weekly."}


# --------------------------------------------------------------------------- #
# §0.2 the decision tree
# --------------------------------------------------------------------------- #
QUESTIONS = {
    "rule_expressible": "Can the decision/action be written as IF/THEN rules a domain expert "
                        "could whiteboard in 30 minutes?",
    "task_type": "What is the task? (classification / extraction / prediction / language / multi_step / none)",
    "error_tolerance_ok": "Can a ~5% error rate be caught by human review without catastrophic impact?",
    "groundable": "Can outputs be grounded in retrieved documents (RAG) rather than model memory?",
    "stakes": "Error cost per incident: low (<£50) / medium (£50–£500) / high (>£500 or regulated)?",
    "affects_individuals": "Does the automated step make decisions that significantly affect individuals "
                           "(credit, employment, eligibility, pricing)?",
    "solely_automated": "Would the decision take effect without meaningful human review?",
}

_ML_PATTERNS = {"classification": "Classification", "extraction": "Extraction",
                "prediction": "Prediction"}


def _walk_tree(a: Dict[str, Any], readiness: Dict[str, Any]) -> Dict[str, Any]:
    """Returns route + trace + open questions. Conservative until answered."""
    trace: List[str] = []
    open_q: List[str] = []

    rule = a.get("rule_expressible")
    if rule is True:
        trace.append("Q1 rule-expressible → YES: deterministic rules win. No AI.")
        return {"route": "Automate_Rules", "pattern": None, "trace": trace, "open_questions": []}
    if rule is None:
        open_q.append("rule_expressible")
        trace.append("Q1 rule-expressible → UNANSWERED (rules always win if yes)")
    else:
        trace.append("Q1 rule-expressible → no")

    task = a.get("task_type")
    if task in _ML_PATTERNS:
        pattern = _ML_PATTERNS[task]
        gate = _readiness_gate(readiness, pattern)
        if gate["gate"] == "pass":
            trace.append(f"Q2 structured {task} with sufficient data → Augment_AI ({pattern})")
            return {"route": "Augment_AI", "pattern": pattern, "trace": trace,
                    "open_questions": open_q}
        trace.append(f"Q2 structured {task} but data-readiness FAILED "
                     f"({gate['total']}/{gate['minimum']}, weak: {', '.join(gate['failing']) or '—'}) "
                     f"→ defer: {', '.join(gate['precursors'])}")
        return {"route": "Defer", "pattern": pattern, "trace": trace, "open_questions": open_q}

    if task == "language":
        if a.get("error_tolerance_ok") is False:
            trace.append("Q3 unstructured language but error tolerance unacceptable → Keep_Manual")
            return {"route": "Keep_Manual", "pattern": None, "trace": trace, "open_questions": open_q}
        if a.get("groundable") is False:
            trace.append("Q3 language, ungroundable → Keep_Manual (uncontrolled hallucination risk)")
            return {"route": "Keep_Manual", "pattern": None, "trace": trace, "open_questions": open_q}
        missing = [q for q in ("error_tolerance_ok", "groundable") if a.get(q) is None]
        if missing:
            open_q += missing
            trace.append("Q3 unstructured language → pending tolerance/groundability answers")
            return {"route": "Pending", "pattern": "RAG_Assistant", "trace": trace,
                    "open_questions": open_q + missing}
        gate = _readiness_gate(readiness, "RAG_Assistant")
        if gate["gate"] == "pass":
            trace.append("Q3 language, tolerant, groundable → Augment_AI (RAG_Assistant, HITL mandatory)")
            return {"route": "Augment_AI", "pattern": "RAG_Assistant", "trace": trace,
                    "open_questions": open_q}
        trace.append(f"Q3 language fits but corpus readiness failed → defer: {', '.join(gate['precursors'])}")
        return {"route": "Defer", "pattern": "RAG_Assistant", "trace": trace, "open_questions": open_q}

    if task == "multi_step":
        if a.get("stakes") == "low":
            trace.append("Q4 autonomous multi-step, low stakes → Augment_AI (Agent, approval gate at end)")
            return {"route": "Augment_AI", "pattern": "Agent", "trace": trace, "open_questions": open_q}
        trace.append("Q4 autonomous multi-step at medium/high stakes → Keep_Manual "
                     "(no autonomous high-stakes agents for SMEs)")
        return {"route": "Keep_Manual", "pattern": None, "trace": trace, "open_questions": open_q}

    if task is None:
        open_q.append("task_type")
        trace.append("Task type unanswered → route pending (conservative default: Keep_Manual)")
        return {"route": "Pending", "pattern": None, "trace": trace, "open_questions": open_q}

    trace.append("No AI pattern fits → Keep_Manual (a valid, mature answer)")
    return {"route": "Keep_Manual", "pattern": None, "trace": trace, "open_questions": open_q}


# --------------------------------------------------------------------------- #
def _risk_register(is_ai: bool) -> List[Dict[str, Any]]:
    rows = []
    for r in (AI_RISKS if is_ai else []) + PROJECT_RISKS:
        rows.append({
            **{k: r[k] for k in ("id", "category", "label", "mitigation", "impact_gbp")},
            "pre_probability_pct": r["pre_pct"],
            "post_probability_pct": r["post_pct"],
            "pre_ev_gbp": round(r["pre_pct"] / 100 * r["impact_gbp"], 0),
            "post_ev_gbp": round(r["post_pct"] / 100 * r["impact_gbp"], 0),
        })
    return rows


def assess(facts: ProcessFacts, answers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Full E3 assessment for a run's automation candidates."""
    a = answers or {}
    jurisdiction = a.get("jurisdiction", "UK")
    adm = ADM_LANDSCAPE.get(jurisdiction, ADM_LANDSCAPE["UK"])

    # readiness: auto-seed, then apply operator overrides {dim: 0..5}
    readiness = seed_readiness(facts)
    for dim, val in (a.get("readiness") or {}).items():
        if dim in readiness:
            readiness[dim] = {"score": max(0, min(5, int(val))), "basis": "operator",
                              "note": "Operator-confirmed"}

    # candidates come from the redesign engine's automation recommendation
    h9 = next((r for r in (facts.redesign or {}).get("recommendations", [])
               if r.get("heuristic") == "H9"), None)
    targets = h9["targets"] if h9 else []

    tree = _walk_tree(a, readiness)

    stakes = a.get("stakes") or "high"  # unknown stakes are treated as high — conservative
    stakes_assumed = a.get("stakes") is None
    adm_applies = bool(a.get("affects_individuals")) and bool(a.get("solely_automated", True))
    hitl = _hitl(stakes, adm_applies)

    is_ai = tree["route"] in ("Augment_AI", "Pending", "Defer") and tree.get("pattern") is not None
    register = _risk_register(is_ai)

    # anti-pattern guards (§5)
    checks = []
    if h9 and h9.get("gated_by"):
        checks.append({"id": "AP-AI1", "status": "blocked",
                       "note": f"{len(h9['gated_by'])} Eliminate/Simplify/Standardise recommendations "
                               f"unresolved — AI on an un-redesigned process automates waste."})
    else:
        checks.append({"id": "AP-AI1", "status": "pass", "note": "ECRS sequence resolved."})
    if a.get("rule_expressible") is True and a.get("task_type") in _ML_PATTERNS:
        checks.append({"id": "AP-AI2", "status": "fail",
                       "note": "Rules suffice — a rules engine is auditable, free to run and doesn't drift."})
    else:
        checks.append({"id": "AP-AI2", "status": "pass", "note": "Rules-first check applied in the tree."})
    checks.append({"id": "AP-AI3",
                   "status": "pass" if tree["route"] != "Defer" else "deferred",
                   "note": "No-data-no-AI gate enforced by the readiness minimums."})
    checks.append({"id": "AP-AI4", "status": "pass",
                   "note": f"HITL enforced by stakes rule → {hitl['pattern']}."})

    return {
        "jurisdiction": jurisdiction,
        "targets": targets,
        "decision": tree,
        "data_readiness": {
            "dimensions": readiness,
            "gate_by_pattern": {p: _readiness_gate(readiness, p)["gate"] for p in PATTERN_MINIMUMS},
            "for_route": _readiness_gate(readiness, tree["pattern"]) if tree.get("pattern") else None,
        },
        "hitl": {**hitl, "stakes": stakes, "stakes_assumed": stakes_assumed},
        "adm_gate": {
            "applies": adm_applies,
            "answered": a.get("affects_individuals") is not None,
            **adm,
            "research_date": RESEARCH_DATE,
            "freshness_warning": "Regulatory positions verified as of the research date only — "
                                 "re-verify against the regulator before any client-facing gate.",
        },
        "risk_register": register,
        "total_risk_ev_gbp": {
            "pre_mitigation": round(sum(r["pre_ev_gbp"] for r in register), 0),
            "post_mitigation": round(sum(r["post_ev_gbp"] for r in register), 0),
        },
        "anti_pattern_checks": checks,
        "open_questions": [{"id": q, "question": QUESTIONS[q]} for q in
                           dict.fromkeys(tree["open_questions"]
                                         + ([] if a.get("stakes") else ["stakes"])
                                         + ([] if a.get("affects_individuals") is not None
                                            else ["affects_individuals"]))],
        "principle": "Rules beat ML beats LLM beats guessing — use the simplest approach that "
                     "passes the gates; Keep_Manual is a valid answer.",
    }
