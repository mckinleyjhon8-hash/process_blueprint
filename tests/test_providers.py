"""Tests for the pluggable LLM provider factory (no network calls)."""

from __future__ import annotations

import pytest

from process_blueprint.brief.providers import build_llm, SUPPORTED


def test_default_provider_is_anthropic(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    llm = build_llm(api_key="sk-test")
    assert type(llm).__name__ == "ChatAnthropic"
    assert llm.model == "claude-opus-4-8"


def test_openai_provider(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    llm = build_llm("openai", model="gpt-4o", api_key="sk-test")
    assert type(llm).__name__ == "ChatOpenAI"
    assert llm.model_name == "gpt-4o"


def test_openrouter_provider(monkeypatch):
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)
    llm = build_llm("openrouter", model="anthropic/claude-opus-4", api_key="sk-test")
    assert type(llm).__name__ == "ChatOpenAI"
    assert llm.model_name == "anthropic/claude-opus-4"
    assert "openrouter.ai" in str(llm.openai_api_base)


def test_provider_from_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    llm = build_llm(model="openai/gpt-4o")
    assert type(llm).__name__ == "ChatOpenAI"
    assert "openrouter.ai" in str(llm.openai_api_base)


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        build_llm("bedrock")


def test_supported_set():
    assert set(SUPPORTED) == {"anthropic", "openai", "openrouter"}


def test_generate_brief_still_works_with_injected_llm(sample_facts):
    """Injected llm must bypass the factory entirely (provider-agnostic path)."""
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    from process_blueprint.brief import generate_brief

    result = generate_brief(
        sample_facts, audience="internal", llm=FakeListChatModel(responses=["ok"])
    )
    assert result.markdown == "ok"
