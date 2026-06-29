"""
knowledge — Phase 3: retrieval-augmented evidence for the brief.

Three tiers of knowledge (per the architecture):
  * benchmarks   — KPI targets per process type (firm-wide)
  * methodology  — curated framework guidance (firm-wide)
  * client_doc   — the client's own SOPs/policies (per engagement)

Everything is embedding-provider-pluggable and works against either an
in-memory store (tests / local) or Supabase pgvector (production).

    from process_blueprint.knowledge import get_embedder, InMemoryKB, SupabaseKB
    from process_blueprint.knowledge import benchmark_chunks, retrieve_evidence
"""

from .types import Chunk
from .embeddings import get_embedder, SUPPORTED as SUPPORTED_EMBEDDERS
from .benchmarks import BENCHMARKS, benchmark_chunks
from .store import InMemoryKB, SupabaseKB, cosine_similarity
from .retrieval import retrieve_evidence

__all__ = [
    "Chunk",
    "get_embedder",
    "SUPPORTED_EMBEDDERS",
    "BENCHMARKS",
    "benchmark_chunks",
    "InMemoryKB",
    "SupabaseKB",
    "cosine_similarity",
    "retrieve_evidence",
]
