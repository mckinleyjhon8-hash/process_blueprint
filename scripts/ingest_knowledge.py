#!/usr/bin/env python
"""
ingest_knowledge.py — embed the firm-wide benchmark knowledge into Supabase.

Loads the KPI benchmarks (one chunk per process type), embeds them, and writes
them to public.knowledge_chunks via the SupabaseKB store.

Requires:
    OPENAI_API_KEY            (for embeddings; or EMBEDDINGS_PROVIDER=fake to dry-run)
    SUPABASE_URL, SUPABASE_SERVICE_KEY

Usage:
    python scripts/ingest_knowledge.py
    python scripts/ingest_knowledge.py --dry-run    # build chunks, no DB write
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(_ROOT, ".env"))
except ImportError:
    pass

from process_blueprint.knowledge import (  # noqa: E402
    benchmark_chunks,
    get_embedder,
    InMemoryKB,
    SupabaseKB,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest benchmark knowledge into Supabase")
    ap.add_argument("--dry-run", action="store_true", help="Build + embed only; no DB write")
    args = ap.parse_args()

    chunks = benchmark_chunks()
    print(f"[i] Built {len(chunks)} benchmark chunks "
          f"({', '.join(c.metadata.get('process_type', '') for c in chunks)})")

    if args.dry_run:
        kb = InMemoryKB(get_embedder("fake", size=64))
        kb.add(chunks)
        print("[OK] Dry run: embedded into in-memory store. No DB write.")
        return 0

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("[!] Set SUPABASE_URL and SUPABASE_SERVICE_KEY (or use --dry-run).")
        return 1

    from supabase import create_client

    client = create_client(url, key)
    kb = SupabaseKB(get_embedder(), client)   # OpenAI embeddings by default
    kb.add(chunks)
    print(f"[OK] Wrote {len(chunks)} benchmark chunks to knowledge_chunks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
