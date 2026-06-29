"""
brief — Phase 2: turn ProcessFacts into an executive brief via LangChain + Claude.

Two audiences:
  * "internal" — full mechanics (algorithm, conformance scores) for consultants.
  * "client"   — results only, in business language; the conformance/tooling
    details are never even put in the model's input (see context.build_context),
    and a deterministic guard scans the output for any leaked internal terms.

Public surface:
    from process_blueprint.brief import generate_brief, BriefResult
    generate_brief(facts, audience="client", llm=None)  # llm injectable for tests
"""

from .chain import generate_brief, default_llm, BriefResult
from .scoring import health_score
from .context import build_context
from . import redact

__all__ = [
    "generate_brief",
    "default_llm",
    "BriefResult",
    "health_score",
    "build_context",
    "redact",
]
