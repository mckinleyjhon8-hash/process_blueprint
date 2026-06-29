"""Phase-3 tests: embeddings, knowledge store, retrieval, brief wiring (no network)."""

from __future__ import annotations

import pytest

from process_blueprint.knowledge import (
    Chunk,
    get_embedder,
    benchmark_chunks,
    InMemoryKB,
    cosine_similarity,
    retrieve_evidence,
)
from process_blueprint.knowledge.embeddings import SUPPORTED


def _kb():
    kb = InMemoryKB(get_embedder("fake", size=64))
    kb.add(benchmark_chunks())
    return kb


# --- embeddings factory ----------------------------------------------------
def test_fake_embedder_is_deterministic():
    e = get_embedder("fake", size=16)
    assert e.embed_query("Procure-to-Pay") == e.embed_query("Procure-to-Pay")


def test_openai_embedder_selected():
    e = get_embedder("openai", api_key="sk-test")
    assert type(e).__name__ == "OpenAIEmbeddings"
    assert e.model == "text-embedding-3-small"


def test_unknown_embedder_raises():
    with pytest.raises(ValueError):
        get_embedder("cohere")


def test_supported_embedders():
    assert set(SUPPORTED) == {"openai", "fake"}


# --- benchmarks ------------------------------------------------------------
def test_benchmark_chunks_cover_process_types():
    chunks = benchmark_chunks()
    titles = {c.title for c in chunks}
    assert "Procure-to-Pay benchmarks" in titles
    assert "Order-to-Cash benchmarks" in titles
    assert len(chunks) >= 8
    assert all(c.source == "benchmark" for c in chunks)


def test_chunk_rejects_bad_source():
    with pytest.raises(ValueError):
        Chunk(source="nope", title="t", content="c")


# --- store + retrieval (deterministic) -------------------------------------
def test_cosine_basics():
    assert cosine_similarity([1, 0], [1, 0]) == 1.0
    assert cosine_similarity([1, 0], [0, 1]) == 0.0
    assert cosine_similarity([], [1]) == 0.0


def test_exact_query_ranks_its_own_chunk_first():
    # With a deterministic embedder, identical text -> identical vector -> sim 1.0.
    kb = _kb()
    target = benchmark_chunks()[0]  # Procure-to-Pay
    hits = kb.search(target.content, k=3)
    assert hits[0].title == target.title
    assert hits[0].score == pytest.approx(1.0, abs=1e-6)


def test_search_respects_source_filter():
    kb = _kb()
    assert kb.search("anything", k=5, source="client_doc") == []  # no client docs loaded
    assert len(kb.search("anything", k=5, source="benchmark")) > 0


def test_retrieve_evidence_shape():
    kb = _kb()
    ev = retrieve_evidence(kb, "Procure-to-Pay", findings_text="Approve PO delay", k=3)
    assert 1 <= len(ev) <= 3
    assert {"source", "title", "content", "score"} <= set(ev[0].keys())


# --- brief wiring ----------------------------------------------------------
def test_generate_brief_retrieves_and_includes_evidence(sample_facts):
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    from process_blueprint.brief import generate_brief, build_context

    kb = _kb()
    # evidence flows into the digest the model sees
    ev = retrieve_evidence(kb, sample_facts.process_type, k=2)
    digest = build_context(sample_facts, "client", evidence=ev,
                           stakeholder={"pain_points": ["slow approvals"]})
    assert "benchmark_evidence" in digest
    assert "stakeholder_input" in digest

    result = generate_brief(sample_facts, audience="internal",
                            llm=FakeListChatModel(responses=["ok"]), kb=kb)
    assert result.markdown == "ok"  # retrieval path runs without error
