"""
chain.py — assemble facts → prompt → Claude → brief.

The LLM is injectable (`llm=`) so the whole pipeline is unit-testable with a fake
chat model and no API key. The real default is Claude Opus 4.8 via langchain-anthropic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, List, Optional

from langchain_core.output_parsers import StrOutputParser

from ..facts import ProcessFacts
from .context import build_context
from .prompts import build_prompt
from .scoring import health_score
from . import redact

# Default model — see the claude-api reference: Opus 4.8 is the most capable
# Opus-tier model and the recommended default. No temperature/budget_tokens
# (removed on 4.8). Override via CLAUDE_MODEL if needed.
DEFAULT_MODEL = "claude-opus-4-8"


@dataclass
class BriefResult:
    audience: str
    markdown: str
    health_score: Optional[int]
    grade: str
    model_name: str
    redaction_warnings: List[str] = field(default_factory=list)


def default_llm(model: Optional[str] = None, max_tokens: int = 4096):
    """Construct the real Claude chat model (lazy import; needs ANTHROPIC_API_KEY)."""
    import os

    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("`pip install langchain-anthropic` to use the real LLM.") from exc

    return ChatAnthropic(
        model=model or os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL),
        max_tokens=max_tokens,
        timeout=120,
    )


def generate_brief(
    facts: ProcessFacts,
    audience: str = "internal",
    llm: Any = None,
) -> BriefResult:
    """Generate an executive brief from ProcessFacts for the given audience."""
    audience = audience.lower().strip()
    if audience not in ("internal", "client"):
        raise ValueError("audience must be 'internal' or 'client'")

    digest = build_context(facts, audience)
    prompt = build_prompt(audience)
    model = llm if llm is not None else default_llm()

    chain = prompt | model | StrOutputParser()
    markdown = chain.invoke(
        {
            "process_type": facts.process_type,
            "digest_json": json.dumps(digest, indent=2, ensure_ascii=False),
        }
    )

    warnings: List[str] = []
    if audience == "client":
        warnings = redact.scan(markdown)

    score, grade = health_score(facts)
    model_name = getattr(model, "model", None) or type(model).__name__

    return BriefResult(
        audience=audience,
        markdown=markdown,
        health_score=score,
        grade=grade,
        model_name=str(model_name),
        redaction_warnings=warnings,
    )
