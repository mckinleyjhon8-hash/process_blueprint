"""
embeddings.py — pluggable embedding-model factory (parallels brief/providers.py).

  * "openai" (default) — OpenAIEmbeddings, `text-embedding-3-small` → 1536 dims,
    which matches the knowledge_chunks.embedding vector(1536) column.
  * "fake"            — DeterministicFakeEmbedding, for tests (no network/keys).

If you switch the OpenAI embedding model, keep the output dimension at 1536 or
update the Supabase column + index accordingly.

Env vars:
    EMBEDDINGS_PROVIDER   openai | fake     (default openai)
    OPENAI_API_KEY / OPENAI_EMBED_MODEL
"""

from __future__ import annotations

import os
from typing import Any, Optional

EMBED_DIM = 1536
DEFAULT_OPENAI_MODEL = "text-embedding-3-small"
SUPPORTED = ("openai", "fake")


def get_embedder(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    size: int = EMBED_DIM,
    **kwargs: Any,
):
    """Return a LangChain Embeddings object for the chosen provider."""
    provider = (provider or os.environ.get("EMBEDDINGS_PROVIDER", "openai")).lower().strip()

    if provider == "fake":
        from langchain_core.embeddings import DeterministicFakeEmbedding

        return DeterministicFakeEmbedding(size=size)

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        key = api_key or os.environ.get("OPENAI_API_KEY")
        return OpenAIEmbeddings(
            model=model or os.environ.get("OPENAI_EMBED_MODEL", DEFAULT_OPENAI_MODEL),
            **({"api_key": key} if key else {}),
            **kwargs,
        )

    raise ValueError(
        f"Unknown embeddings provider '{provider}'. Supported: {', '.join(SUPPORTED)}."
    )
