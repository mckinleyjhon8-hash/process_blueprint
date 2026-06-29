"""
prompts.py — BABOK-shaped prompt templates for the two audiences.

The skeleton mirrors docs/METHODOLOGY_MAP.md (Strategy Analysis → Solution
Evaluation). Templates contain only the {process_type} and {digest_json}
placeholders — no other literal braces, so ChatPromptTemplate parses cleanly.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

_SECTIONS = (
    "1. Executive Summary\n"
    "2. Current State\n"
    "3. Performance Analysis\n"
    "4. Root Causes\n"
    "5. Future State and Change Strategy\n"
    "6. Recommendations and Business Case\n"
    "7. Risk Indicators"
)

INTERNAL_SYSTEM = (
    "You are a senior process-mining consultant writing an INTERNAL evaluation "
    "brief for your own consulting team. Be precise and technical. You may cite "
    "the discovery algorithm and conformance metrics (fitness, precision, "
    "simplicity) where useful. Ground every claim in the supplied analysis data; "
    "never invent numbers. Use the following Markdown section skeleton exactly, "
    "in order:\n\n" + _SECTIONS + "\n\n"
    "Quantify impact in hours and, where you can reason it, indicative cost. Keep "
    "it tight and decision-useful."
)

CLIENT_SYSTEM = (
    "You are a senior management consultant writing a CLIENT-FACING brief for an "
    "SME executive. Write in plain business language about findings, impact, and "
    "recommendations. State impact in time (hours/days) and indicative euro cost. "
    "Use the following Markdown section skeleton exactly, in order:\n\n"
    + _SECTIONS + "\n\n"
    "ABSOLUTE RULES: Never mention software, tools, algorithms, or process-mining "
    "mechanics. Do not use the words conformance, fitness, precision, petri net, "
    "or any tool name. Do not describe HOW the analysis was produced — only WHAT "
    "was found and what to do about it. Ground every claim in the supplied data; "
    "never invent numbers."
)

HUMAN_TEMPLATE = (
    "Process under review: {process_type}\n\n"
    "Analysis data (JSON):\n{digest_json}\n\n"
    "Write the brief now, following the section skeleton exactly."
)


def build_prompt(audience: str) -> ChatPromptTemplate:
    system = CLIENT_SYSTEM if audience.lower() == "client" else INTERNAL_SYSTEM
    return ChatPromptTemplate.from_messages(
        [("system", system), ("human", HUMAN_TEMPLATE)]
    )
