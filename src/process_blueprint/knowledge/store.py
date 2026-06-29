"""
store.py — knowledge-base backends with a common interface.

  * InMemoryKB  — cosine similarity in Python; tests and local use.
  * SupabaseKB  — pgvector via the `match_knowledge_chunks` RPC (production).

Both expose:
    add(chunks)                        # embed + store
    search(query, k, source, engagement_id) -> list[Chunk]   # scored, ranked
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any, List, Optional

from .types import Chunk


def cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class InMemoryKB:
    """Embeds chunks on add and ranks by cosine similarity on search."""

    def __init__(self, embedder: Any):
        self.embedder = embedder
        self._chunks: List[Chunk] = []

    def add(self, chunks: List[Chunk]) -> None:
        vectors = self.embedder.embed_documents([c.content for c in chunks])
        for c, v in zip(chunks, vectors):
            self._chunks.append(replace(c, embedding=list(v)))

    def search(
        self,
        query: str,
        k: int = 5,
        source: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ) -> List[Chunk]:
        qv = self.embedder.embed_query(query)
        candidates = [
            c
            for c in self._chunks
            if (source is None or c.source == source)
            and (engagement_id is None or c.engagement_id in (None, engagement_id))
        ]
        scored = [
            replace(c, score=round(cosine_similarity(qv, c.embedding or []), 4))
            for c in candidates
        ]
        scored.sort(key=lambda c: c.score or 0.0, reverse=True)
        return scored[:k]


class SupabaseKB:
    """pgvector-backed store. Requires a supabase client and `match_knowledge_chunks`."""

    def __init__(self, embedder: Any, client: Any):
        self.embedder = embedder
        self.client = client

    @staticmethod
    def _vec_literal(v: List[float]) -> str:
        # pgvector expects a "[a,b,c]" string literal via PostgREST.
        return "[" + ",".join(repr(float(x)) for x in v) + "]"

    def add(self, chunks: List[Chunk]) -> None:
        vectors = self.embedder.embed_documents([c.content for c in chunks])
        rows = [
            {
                "source": c.source,
                "title": c.title,
                "content": c.content,
                "embedding": self._vec_literal(list(v)),
                "metadata": c.metadata,
                "engagement_id": c.engagement_id,
            }
            for c, v in zip(chunks, vectors)
        ]
        self.client.table("knowledge_chunks").insert(rows).execute()

    def search(
        self,
        query: str,
        k: int = 5,
        source: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ) -> List[Chunk]:
        qv = self.embedder.embed_query(query)
        res = self.client.rpc(
            "match_knowledge_chunks",
            {
                "query_embedding": self._vec_literal(qv),
                "match_count": k,
                "filter_source": source,
                "filter_engagement": engagement_id,
            },
        ).execute()
        return [
            Chunk(
                source=row.get("source", "benchmark"),
                title=row.get("title", ""),
                content=row.get("content", ""),
                score=round(float(row.get("similarity", 0.0)), 4),
            )
            for row in (res.data or [])
        ]
