"""
providers.py — pluggable LangChain chat-model factory.

Three providers, selected by the `LLM_PROVIDER` env var (or the `provider` arg):
  * "anthropic"  (default) — Claude via langchain-anthropic. Default model
    `claude-opus-4-8`. No temperature/budget_tokens (removed on Opus 4.8).
  * "openai"     — OpenAI via langchain-openai. Model from OPENAI_MODEL.
  * "openrouter" — OpenRouter (OpenAI-compatible) via langchain-openai pointed at
    https://openrouter.ai/api/v1. Model from OPENROUTER_MODEL (use "vendor/model"
    ids, e.g. "anthropic/claude-opus-4" or "openai/gpt-4o").

All three return a LangChain chat model usable interchangeably in the brief chain.
Provider libraries are imported lazily, so you only need the SDK for the provider
you actually use. API keys come from the provider's standard env var unless passed.

Env vars:
    LLM_PROVIDER                anthropic | openai | openrouter   (default anthropic)
    ANTHROPIC_API_KEY / ANTHROPIC_MODEL
    OPENAI_API_KEY    / OPENAI_MODEL
    OPENROUTER_API_KEY / OPENROUTER_MODEL / OPENROUTER_BASE_URL
    OPENROUTER_REFERRER / OPENROUTER_TITLE   (optional attribution headers)
"""

from __future__ import annotations

import os
from typing import Any, Optional

DEFAULTS = {
    "anthropic": "claude-opus-4-8",
    "openai": "gpt-4o",
    "openrouter": "anthropic/claude-opus-4",
}
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
SUPPORTED = tuple(DEFAULTS.keys())


def build_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    max_tokens: int = 4096,
    timeout: int = 120,
    **kwargs: Any,
):
    """Return a LangChain chat model for the chosen provider."""
    provider = (provider or os.environ.get("LLM_PROVIDER", "anthropic")).lower().strip()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        return ChatAnthropic(
            model=model or os.environ.get("ANTHROPIC_MODEL", DEFAULTS["anthropic"]),
            max_tokens=max_tokens,
            timeout=timeout,
            **({"api_key": key} if key else {}),
            **kwargs,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        key = api_key or os.environ.get("OPENAI_API_KEY")
        return ChatOpenAI(
            model=model or os.environ.get("OPENAI_MODEL", DEFAULTS["openai"]),
            max_tokens=max_tokens,
            timeout=timeout,
            **({"api_key": key} if key else {}),
            **kwargs,
        )

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI

        key = api_key or os.environ.get("OPENROUTER_API_KEY")
        headers = {}
        if os.environ.get("OPENROUTER_REFERRER"):
            headers["HTTP-Referer"] = os.environ["OPENROUTER_REFERRER"]
        if os.environ.get("OPENROUTER_TITLE"):
            headers["X-Title"] = os.environ["OPENROUTER_TITLE"]
        return ChatOpenAI(
            model=model or os.environ.get("OPENROUTER_MODEL", DEFAULTS["openrouter"]),
            base_url=os.environ.get("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
            max_tokens=max_tokens,
            timeout=timeout,
            **({"api_key": key} if key else {}),
            **({"default_headers": headers} if headers else {}),
            **kwargs,
        )

    raise ValueError(
        f"Unknown LLM provider '{provider}'. Supported: {', '.join(SUPPORTED)}."
    )
