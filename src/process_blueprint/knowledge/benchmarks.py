"""
benchmarks.py — domain KPI benchmarks per process type (firm-wide knowledge).

These are the "what good looks like" targets the brief compares the client's
actuals against. Concise, business-language summaries (safe for client output).
One Chunk per process type, source="benchmark".
"""

from __future__ import annotations

from typing import Dict, List

from .types import Chunk

BENCHMARKS: Dict[str, Dict[str, str]] = {
    "Procure-to-Pay": {
        "cycle_target": "5-7 days end-to-end",
        "kpis": "touchless PO ratio >=70%, first-pass match rate >=85%, cost <= EUR 3/invoice, on-time delivery >=95%",
        "bottlenecks": "PO approval routing, supplier confirmation delay, 3-way match exceptions, invoice approval backlog",
        "best_practices": "tiered approval thresholds by spend band, catalogue-based touchless POs, automated 3-way match with exception-only review",
    },
    "Order-to-Cash": {
        "cycle_target": "1-3 days",
        "kpis": "order accuracy >=98%, on-time-in-full >=95%, DSO <=35 days, perfect order rate >=90%",
        "bottlenecks": "credit-hold decisions, order-entry rework, pick-pack-ship coordination, AR collection follow-up",
        "best_practices": "unified order capture, automated credit scoring, available-to-promise allocation, self-service order status",
    },
    "Issue Resolution": {
        "cycle_target": "4-24 hours",
        "kpis": "first-contact resolution >=70%, MTTR <=8h, reopen rate <=10%, SLA compliance >=95%",
        "bottlenecks": "triage and routing, escalation hand-offs, root-cause analysis, customer communication gaps",
        "best_practices": "intelligent routing, severity-based SLA matrices, mandatory RCA for P1/P2, living knowledge base",
    },
    "Employee Onboarding": {
        "cycle_target": "3-5 days",
        "kpis": "time-to-productivity <=14 days, completion rate >=98%, day-1 readiness >=90%, IT provisioning <=24h",
        "bottlenecks": "IT provisioning, badge/access setup, manager availability, HR document collection",
        "best_practices": "pre-boarding triggered on offer accept, role-based templates, cross-functional SLA, automated IT provisioning",
    },
    "Invoice Processing": {
        "cycle_target": "2-4 days",
        "kpis": "straight-through processing >=75%, cost <= EUR 3/invoice, cycle time <=48h, duplicate detection 100%",
        "bottlenecks": "manual data entry, PO/GRN mismatch exceptions, approval routing, ERP posting",
        "best_practices": "capture automation, rules-based exception routing, dynamic approval thresholds, supplier portal",
    },
    "Customer Service": {
        "cycle_target": "5-15 minutes first contact",
        "kpis": "average handle time <=6 min, first-contact resolution >=75%, service level 80/20, abandon rate <=5%",
        "bottlenecks": "IVR/routing config, agent availability, knowledge lookup, after-call work",
        "best_practices": "skills-based routing, unified agent desktop, structured wrap-up codes, proactive outreach",
    },
    "Change Management": {
        "cycle_target": "1-10 days by risk tier",
        "kpis": "change success rate >=95%, emergency change ratio <=10%, CAB turnaround <=48h, unauthorised changes 0%",
        "bottlenecks": "CAB scheduling, risk-assessment completeness, implementation windows, post-implementation review backlog",
        "best_practices": "standard pre-approved changes, automated risk scoring, integrated change-release-deploy, mandatory PIR for Sev-1/2",
    },
    "Risk Assessment": {
        "cycle_target": "5-15 days",
        "kpis": "assessment cycle <=10 days, register coverage 100% in-scope, mitigation on-time >=85%, frequency adherence >=95%",
        "bottlenecks": "data gathering, risk-scoring consensus, mitigation-plan approval, monitoring cadence drift",
        "best_practices": "centralised GRC platform, quantified likelihood x impact scoring, continuous monitoring, clear RACI per mitigation",
    },
}


def benchmark_chunks() -> List[Chunk]:
    """Return one retrievable Chunk per process type."""
    chunks: List[Chunk] = []
    for ptype, d in BENCHMARKS.items():
        content = (
            f"{ptype} industry benchmarks. "
            f"Target cycle time: {d['cycle_target']}. "
            f"Key targets: {d['kpis']}. "
            f"Common bottlenecks: {d['bottlenecks']}. "
            f"Best practices: {d['best_practices']}."
        )
        chunks.append(
            Chunk(
                source="benchmark",
                title=f"{ptype} benchmarks",
                content=content,
                metadata={"process_type": ptype},
            )
        )
    return chunks
