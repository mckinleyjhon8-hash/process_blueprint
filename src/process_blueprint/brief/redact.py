"""
redact.py — client-safe output guard.

The client view must never expose the internal engine or its mechanics. The
primary protection is that the client digest (context.build_context) omits the
conformance numbers entirely, so the model can't cite what it never saw. This
module is the second line of defence: it scans the generated text for internal
terms that should never reach a client, and can strip them if needed.
"""

from __future__ import annotations

import re
from typing import List

# Terms that must never appear in a client-facing deliverable.
INTERNAL_TERMS: List[str] = [
    "pm4py",
    "petri net",
    "petri-net",
    "token replay",
    "token-based replay",
    "heuristics miner",
    "inductive miner",
    "conformance",
    "directly-follows",
    "dfg",
    "event log",
    "xes",
]


def _pattern(term: str) -> str:
    # Word boundaries prevent false positives like "xes" inside "indexes"/"taxes".
    return r"\b" + re.escape(term) + r"\b"


def scan(text: str) -> List[str]:
    """Return the sorted, de-duplicated internal terms found in *text*."""
    low = text.lower()
    return sorted({t for t in INTERNAL_TERMS if re.search(_pattern(t), low)})


def clean(text: str, replacement: str = "[internal detail removed]") -> str:
    """Replace any internal terms with a neutral placeholder (last-resort)."""
    out = text
    for term in INTERNAL_TERMS:
        out = re.sub(_pattern(term), replacement, out, flags=re.IGNORECASE)
    return out
