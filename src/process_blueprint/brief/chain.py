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
from .providers import build_llm
from . import redact


@dataclass
class BriefResult:
    audience: str
    markdown: str
    health_score: Optional[int]
    grade: str
    model_name: str
    redaction_warnings: List[str] = field(default_factory=list)


def default_llm(provider: Optional[str] = None, model: Optional[str] = None):
    """Construct the real chat model for the configured provider.

    Provider is `LLM_PROVIDER` (anthropic | openai | openrouter); default
    anthropic / claude-opus-4-8. Needs the matching provider API key in the env.
    """
    return build_llm(provider=provider, model=model)


def generate_brief(
    facts: ProcessFacts,
    audience: str = "internal",
    llm: Any = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    evidence: Optional[List[dict]] = None,
    stakeholder: Optional[dict] = None,
    kb: Any = None,
    engagement_id: Optional[str] = None,
) -> BriefResult:
    """Generate an executive brief from ProcessFacts for the given audience.

    Pass `llm=` to inject any LangChain chat model (used in tests), or
    `provider=`/`model=` to pick anthropic/openai/openrouter at call time.

    Phase 3: pass `evidence=` directly, or `kb=` (a knowledge store) to retrieve
    benchmark/methodology/client-doc evidence for this process. `stakeholder=`
    supplies the qualitative WHY (pain points, goals).
    """
    audience = audience.lower().strip()
    if audience not in ("internal", "client"):
        raise ValueError("audience must be 'internal' or 'client'")

    if evidence is None and kb is not None:
        from ..knowledge import retrieve_evidence

        findings = ", ".join(
            f"{b.source} to {b.target}" for b in facts.bottlenecks[:3]
        )
        evidence = retrieve_evidence(
            kb, facts.process_type, findings_text=findings, engagement_id=engagement_id
        )

    digest = build_context(facts, audience, evidence=evidence, stakeholder=stakeholder)
    prompt = build_prompt(audience)
    model_llm = llm if llm is not None else default_llm(provider=provider, model=model)

    chain = prompt | model_llm | StrOutputParser()
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
    # ChatAnthropic exposes .model; ChatOpenAI exposes .model_name.
    model_name = (
        getattr(model_llm, "model", None)
        or getattr(model_llm, "model_name", None)
        or type(model_llm).__name__
    )

    return BriefResult(
        audience=audience,
        markdown=markdown,
        health_score=score,
        grade=grade,
        model_name=str(model_name),
        redaction_warnings=warnings,
    )
