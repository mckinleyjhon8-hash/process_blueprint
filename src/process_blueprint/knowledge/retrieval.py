"""
retrieval.py — turn a process + findings into ranked evidence for the brief.

Searches the firm-wide knowledge (benchmarks + methodology) and, when an
engagement is given, that client's own documents, then returns a compact list
of evidence dicts ready to drop into the brief context.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def retrieve_evidence(
    kb: Any,
    process_type: str,
    findings_text: str = "",
    k: int = 4,
    engagement_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return ranked evidence chunks as dicts: {source, title, content, score}."""
    query = (
        f"{process_type} benchmarks, KPI targets, common bottlenecks and best "
        f"practices. {findings_text}".strip()
    )

    hits = list(kb.search(query, k=k))
    if engagement_id is not None:
        hits += list(
            kb.search(query, k=k, source="client_doc", engagement_id=engagement_id)
        )

    # De-duplicate by (source, title), keep best score, then rank.
    best: Dict[tuple, Dict[str, Any]] = {}
    for c in hits:
        key = (c.source, c.title)
        item = {
            "source": c.source,
            "title": c.title,
            "content": c.content,
            "score": c.score,
        }
        if key not in best or (c.score or 0) > (best[key]["score"] or 0):
            best[key] = item

    ranked = sorted(best.values(), key=lambda d: d["score"] or 0.0, reverse=True)
    return ranked[:k]
