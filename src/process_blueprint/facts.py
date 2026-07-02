"""
facts.py — the ProcessFacts contract.

This is the single source of truth produced by the mining engine and consumed
by every downstream layer (LLM brief generator, dashboard, Supabase persistence).
Nothing downstream re-reads the raw event log; it all reads ProcessFacts.

Design rules:
  * Pure data — no pm4py imports here, so it can be (de)serialised anywhere.
  * Everything JSON-serialisable via `to_dict()` / `to_json()`.
  * `schema_version` is bumped whenever the shape changes, so persisted facts
    in Supabase remain interpretable.
"""

from __future__ import annotations

import json
import datetime as _dt
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.1"  # 1.1: flow / time_profile / resources / batching /
                        #      benchmarks / provenance / discovery (all additive)


@dataclass
class ModelQuality:
    """Conformance / quality metrics for the discovered process model.

    All metrics are 0..1 (higher is better) or None when not computable.
    These are the fields the old health-score relied on but never received —
    the root cause of the always-"F" grade. They are now populated for real.
    """

    algorithm: str
    fitness: Optional[float] = None          # token-based replay log fitness
    fitness_alignments: Optional[float] = None  # alignment-based (more exact, slower)
    precision: Optional[float] = None
    generalization: Optional[float] = None
    simplicity: Optional[float] = None


@dataclass
class Bottleneck:
    """A directly-follows transition with high waiting time."""

    source: str
    target: str
    mean_wait_seconds: float
    occurrences: int


@dataclass
class Variant:
    """A distinct end-to-end activity sequence and how often it occurs."""

    sequence: Tuple[str, ...]
    frequency: int


@dataclass
class ProcessFacts:
    """Typed, serialisable summary of one process-mining analysis run."""

    # --- identity / context ---
    process_type: str
    source_file: str

    # --- volumes ---
    n_events: int
    n_cases: int
    n_activities: int
    n_variants: int

    # --- time ---
    avg_cycle_time_seconds: float
    median_cycle_time_seconds: float

    # --- structure ---
    start_activities: Dict[str, int] = field(default_factory=dict)
    end_activities: Dict[str, int] = field(default_factory=dict)
    activity_frequencies: Dict[str, int] = field(default_factory=dict)

    # --- model quality ---
    model: ModelQuality = field(
        default_factory=lambda: ModelQuality(algorithm="none")
    )

    # --- diagnostics ---
    bottlenecks: List[Bottleneck] = field(default_factory=list)
    top_variants: List[Variant] = field(default_factory=list)
    rework_activities: Dict[str, int] = field(default_factory=dict)

    # --- v1.1 insight layers (plain dicts/lists: JSON-shaped by construction) ---
    flow: Dict[str, Any] = field(default_factory=dict)          # performance DFG
    time_profile: Dict[str, Any] = field(default_factory=dict)  # percentiles, coverage
    resources: Dict[str, Any] = field(default_factory=dict)     # roles, handovers, SPOF
    batching: List[Dict[str, Any]] = field(default_factory=list)
    benchmarks: Dict[str, Any] = field(default_factory=dict)    # quartile positions
    provenance: Dict[str, str] = field(default_factory=dict)    # metric -> evidence grade
    discovery: Dict[str, Any] = field(default_factory=dict)     # completeness scoring

    # --- provenance ---
    schema_version: str = SCHEMA_VERSION
    generated_at: str = field(
        default_factory=lambda: _dt.datetime.now(_dt.timezone.utc).isoformat()
    )
    notifications: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        """Plain dict, with tuples coerced to lists for JSON compatibility."""
        d = asdict(self)
        d["top_variants"] = [
            {"sequence": list(v["sequence"]), "frequency": v["frequency"]}
            for v in d["top_variants"]
        ]
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProcessFacts":
        """Rebuild a ProcessFacts from its serialised form (e.g. a Supabase jsonb)."""
        m = d.get("model") or {}
        model = ModelQuality(
            algorithm=m.get("algorithm", "none"),
            fitness=m.get("fitness"),
            fitness_alignments=m.get("fitness_alignments"),
            precision=m.get("precision"),
            generalization=m.get("generalization"),
            simplicity=m.get("simplicity"),
        )
        bottlenecks = [
            Bottleneck(
                source=b["source"], target=b["target"],
                mean_wait_seconds=b["mean_wait_seconds"], occurrences=b["occurrences"],
            )
            for b in d.get("bottlenecks", [])
        ]
        variants = [
            Variant(sequence=tuple(v["sequence"]), frequency=v["frequency"])
            for v in d.get("top_variants", [])
        ]
        return cls(
            process_type=d.get("process_type", "Unknown"),
            source_file=d.get("source_file", ""),
            n_events=d.get("n_events", 0),
            n_cases=d.get("n_cases", 0),
            n_activities=d.get("n_activities", 0),
            n_variants=d.get("n_variants", 0),
            avg_cycle_time_seconds=d.get("avg_cycle_time_seconds", 0.0),
            median_cycle_time_seconds=d.get("median_cycle_time_seconds", 0.0),
            start_activities=d.get("start_activities", {}),
            end_activities=d.get("end_activities", {}),
            activity_frequencies=d.get("activity_frequencies", {}),
            model=model,
            bottlenecks=bottlenecks,
            top_variants=variants,
            rework_activities=d.get("rework_activities", {}),
            flow=d.get("flow", {}),
            time_profile=d.get("time_profile", {}),
            resources=d.get("resources", {}),
            batching=d.get("batching", []),
            benchmarks=d.get("benchmarks", {}),
            provenance=d.get("provenance", {}),
            discovery=d.get("discovery", {}),
            schema_version=d.get("schema_version", SCHEMA_VERSION),
            generated_at=d.get("generated_at", ""),
            notifications=d.get("notifications", []),
        )

    @property
    def avg_cycle_time_hours(self) -> float:
        return round(self.avg_cycle_time_seconds / 3600.0, 4)
