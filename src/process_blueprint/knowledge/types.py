"""types.py — the knowledge Chunk: one retrievable unit, maps to a row of
public.knowledge_chunks in Supabase."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

SOURCES = ("benchmark", "methodology", "client_doc")


@dataclass
class Chunk:
    source: str                              # one of SOURCES
    title: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    engagement_id: Optional[str] = None      # None = firm-wide
    embedding: Optional[List[float]] = None
    score: Optional[float] = None            # similarity, set on retrieval

    def __post_init__(self) -> None:
        if self.source not in SOURCES:
            raise ValueError(f"source must be one of {SOURCES}, got '{self.source}'")
