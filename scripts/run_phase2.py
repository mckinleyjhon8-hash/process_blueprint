#!/usr/bin/env python
"""
run_phase2.py — run the engine, then generate executive briefs from the facts.

Usage:
    python scripts/run_phase2.py                 # sample log; real Claude (needs ANTHROPIC_API_KEY)
    python scripts/run_phase2.py log.csv --audience client
    python scripts/run_phase2.py --demo          # no API key: uses a canned fake model

Set ANTHROPIC_API_KEY (and optionally CLAUDE_MODEL) for live generation.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, _ROOT)

from process_blueprint import analyze            # noqa: E402
from process_blueprint.brief import generate_brief  # noqa: E402


def _sample_log() -> str:
    from tests.sample_log import write_sample_csv

    path = os.path.join(tempfile.gettempdir(), "pb_sample_p2p.csv")
    return write_sample_csv(path)


def _demo_llm():
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    return FakeListChatModel(responses=[
        "# Executive Brief (DEMO)\n\n"
        "## 1. Executive Summary\nThis is a canned demo response — set "
        "ANTHROPIC_API_KEY to generate a real brief with Claude.\n"
    ])


def main() -> int:
    ap = argparse.ArgumentParser(description="Process Blueprint — Phase 2 (brief)")
    ap.add_argument("log", nargs="?", help="CSV/XES event log (omit for sample)")
    ap.add_argument("--process-type", default="Procure-to-Pay")
    ap.add_argument("--audience", default="internal", choices=["internal", "client"])
    ap.add_argument("--demo", action="store_true", help="Use a fake model (no API key)")
    args = ap.parse_args()

    log_path = args.log or _sample_log()
    facts = analyze(log_path, process_type=args.process_type)

    llm = _demo_llm() if args.demo else None
    if llm is None and not os.environ.get("ANTHROPIC_API_KEY"):
        print("[!] ANTHROPIC_API_KEY not set. Re-run with --demo to see the wiring, "
              "or set the key for a real brief.")
        return 1

    result = generate_brief(facts, audience=args.audience, llm=llm)

    print(f"\n{'=' * 64}")
    print(f"{args.audience.upper()} BRIEF  |  model={result.model_name}  "
          f"|  health={result.health_score} {result.grade}")
    if result.redaction_warnings:
        print(f"[!] client-safe guard flagged: {result.redaction_warnings}")
    print("=" * 64 + "\n")
    print(result.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
