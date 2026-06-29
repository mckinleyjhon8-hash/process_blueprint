"""
process_blueprint — internal process-mining & consulting-intelligence engine.

Public surface (Phase 1):
    from process_blueprint import analyze, ProcessFacts

`analyze(file_path, ...)` runs the full Phase-1 pipeline (ingest → discover →
conform → diagnose → KPIs) and returns a typed :class:`ProcessFacts` object,
the single contract every downstream layer (LLM brief, dashboard, Supabase)
consumes.
"""

from .facts import ProcessFacts, ModelQuality, Bottleneck, Variant
from .engine import analyze

__all__ = [
    "analyze",
    "ProcessFacts",
    "ModelQuality",
    "Bottleneck",
    "Variant",
]

__version__ = "0.1.0"
