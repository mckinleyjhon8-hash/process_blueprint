"""
context.py — turn ProcessFacts into a compact, LLM-ready digest.

Audience-aware by construction:
  * internal → includes model_quality (algorithm, fitness, precision, ...).
  * client   → omits all conformance/tooling fields, so the client-facing model
    physically cannot leak them. This is the strongest guarantee in the system.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..facts import ProcessFacts
from .scoring import health_score


def _hours(seconds: float) -> float:
    return round((seconds or 0.0) / 3600.0, 1)


def build_context(
    facts: ProcessFacts,
    audience: str = "internal",
    evidence: Optional[List[Dict[str, Any]]] = None,
    stakeholder: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the digest dict passed to the prompt for the given audience.

    `evidence` — retrieved benchmark/methodology/client-doc chunks (Phase 3).
    `stakeholder` — the WHY behind the data (pain points, goals) — closes the
    BABOK Elicitation gap. Both are safe for either audience (business language).
    """
    score, grade = health_score(facts)

    digest: Dict[str, Any] = {
        "process_type": facts.process_type,
        "volumes": {
            "cases": facts.n_cases,
            "events": facts.n_events,
            "activities": facts.n_activities,
            "distinct_paths": facts.n_variants,
        },
        "avg_cycle_time_hours": facts.avg_cycle_time_hours,
        "median_cycle_time_hours": _hours(facts.median_cycle_time_seconds),
        "health": {"score": score, "grade": grade},
        "slowest_handoffs": [
            {
                "from": b.source,
                "to": b.target,
                "avg_wait_hours": _hours(b.mean_wait_seconds),
                "occurrences": b.occurrences,
            }
            for b in facts.bottlenecks[:5]
        ],
        "repeated_steps": dict(list(facts.rework_activities.items())[:5]),
        "entry_points": facts.start_activities,
        "exit_points": facts.end_activities,
    }

    if audience.lower() == "internal":
        digest["model_quality"] = {
            "algorithm": facts.model.algorithm,
            "fitness": facts.model.fitness,
            "precision": facts.model.precision,
            "generalization": facts.model.generalization,
            "simplicity": facts.model.simplicity,
        }

    if evidence:
        digest["benchmark_evidence"] = [
            {"title": e.get("title"), "content": e.get("content")} for e in evidence
        ]
    if stakeholder:
        digest["stakeholder_input"] = stakeholder

    return digest
