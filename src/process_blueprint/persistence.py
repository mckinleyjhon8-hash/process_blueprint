"""
persistence.py — map ProcessFacts onto Supabase rows and (optionally) write them.

Row-building functions are pure and unit-tested (no network). The actual write
helper imports the Supabase client lazily, so the package has no hard dependency
on it and tests run without credentials.

The app connects with the **service-role key** (server-side) — RLS is enabled on
all tables with no public policies, so the public API exposes nothing.

Env vars used by `insert_process_facts`:
    SUPABASE_URL, SUPABASE_SERVICE_KEY
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .facts import ProcessFacts


def run_row(facts: ProcessFacts, engagement_id: str) -> Dict[str, Any]:
    """Build an `event_log_runs` row from facts."""
    return {
        "engagement_id": engagement_id,
        "source_file": facts.source_file,
        "algorithm": facts.model.algorithm,
        "n_events": facts.n_events,
        "n_cases": facts.n_cases,
        "status": "completed",
    }


def facts_row(facts: ProcessFacts, run_id: str) -> Dict[str, Any]:
    """Build a `process_facts` row (queryable columns + full jsonb) from facts."""
    return {
        "run_id": run_id,
        "schema_version": facts.schema_version,
        "process_type": facts.process_type,
        "n_cases": facts.n_cases,
        "n_variants": facts.n_variants,
        "avg_cycle_time_seconds": facts.avg_cycle_time_seconds,
        "model_fitness": facts.model.fitness,
        "model_precision": facts.model.precision,
        "facts": facts.to_dict(),
    }


def get_client(url: Optional[str] = None, key: Optional[str] = None):
    """Return a Supabase client (lazy import). Raises if creds/lib are missing."""
    url = url or os.environ.get("SUPABASE_URL")
    key = key or os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_KEY (service-role) to write."
        )
    try:
        from supabase import create_client
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("`pip install supabase` to enable writes.") from exc
    return create_client(url, key)


def insert_process_facts(
    facts: ProcessFacts,
    engagement_id: str,
    client=None,
) -> Dict[str, str]:
    """Insert a run then its facts; return the new ids. Requires a live client."""
    client = client or get_client()

    run = client.table("event_log_runs").insert(run_row(facts, engagement_id)).execute()
    run_id = run.data[0]["id"]

    fr = client.table("process_facts").insert(facts_row(facts, run_id)).execute()
    facts_id = fr.data[0]["id"]

    return {"run_id": run_id, "facts_id": facts_id}
