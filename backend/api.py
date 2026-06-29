"""
api.py — thin FastAPI backend exposing the Process Blueprint engine to the frontend.

Endpoints:
    GET  /api/health
    POST /api/analyze   (multipart: file, process_type)  -> ProcessFacts + run_id
    POST /api/brief     (json: run_id, audience, provider) -> brief markdown

The pm4py engine stays isolated here (AGPL-clean internal batch step). Facts are
cached in-memory per run so the brief endpoint can reuse them without re-mining.
Run with:  uvicorn backend.api:app --reload --port 8000
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, _ROOT)  # so the sample-log generator (tests/) is importable

# Load .env (gitignored) so provider keys are available. Never hardcode keys.
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(_ROOT, ".env"))
except ImportError:
    pass

from process_blueprint import analyze, ProcessFacts            # noqa: E402
from process_blueprint.engine import analyze_dataframe         # noqa: E402
from process_blueprint.brief import generate_brief             # noqa: E402

app = FastAPI(title="Process Blueprint API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory run cache: run_id -> ProcessFacts (internal-only tool, single worker).
_RUNS: Dict[str, ProcessFacts] = {}

_PROVIDER_KEY = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def _supabase():
    """Return a Supabase client if creds are present, else None (best-effort)."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client

        return create_client(url, key)
    except Exception:
        return None


def _knowledge_base():
    """Supabase-backed knowledge store for benchmark evidence (needs OpenAI key)."""
    client = _supabase()
    if client is None or not os.environ.get("OPENAI_API_KEY"):
        return None
    try:
        from process_blueprint.knowledge import get_embedder, SupabaseKB

        return SupabaseKB(get_embedder("openai"), client)
    except Exception:
        return None


def _default_engagement_id(client) -> Optional[str]:
    """Get-or-create a singleton 'API Demo' engagement to attach runs to."""
    try:
        found = (
            client.table("engagements").select("id").eq("name", "API Demo").limit(1).execute()
        )
        if found.data:
            return found.data[0]["id"]
        cl = client.table("clients").insert({"name": "API Demo", "industry": "Demo"}).execute()
        eng = (
            client.table("engagements")
            .insert({"client_id": cl.data[0]["id"], "name": "API Demo", "process_type": "Procure-to-Pay"})
            .execute()
        )
        return eng.data[0]["id"]
    except Exception:
        return None


def _persist(facts: ProcessFacts) -> Optional[Dict[str, str]]:
    """Best-effort persistence of a run + facts to Supabase. Never raises."""
    client = _supabase()
    if client is None:
        return None
    try:
        from process_blueprint.persistence import insert_process_facts

        eng_id = _default_engagement_id(client)
        if not eng_id:
            return None
        return insert_process_facts(facts, eng_id, client=client)
    except Exception:
        return None


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "process-blueprint"}


@app.post("/api/analyze")
async def analyze_log(
    file: UploadFile = File(...),
    process_type: str = Form("Procure-to-Pay"),
    algorithm: str = Form("inductive"),
) -> Dict[str, Any]:
    suffix = os.path.splitext(file.filename or "log.csv")[1] or ".csv"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(await file.read())
        tmp.close()
        facts = analyze(tmp.name, process_type=process_type, algorithm=algorithm)
    except Exception as exc:  # surface ingest/mining errors cleanly
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    run_id = uuid.uuid4().hex
    _RUNS[run_id] = facts
    payload = facts.to_dict()
    payload["run_id"] = run_id
    payload["persisted"] = _persist(facts) is not None
    return payload


@app.post("/api/analyze-sample")
def analyze_sample(cases: int = 400) -> Dict[str, Any]:
    """Generate a comprehensive enterprise P2P log server-side and analyse it.

    One-click live demo of the whole pipeline — no file upload needed.
    """
    try:
        from tests.enterprise_log import build_enterprise_log
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"sample generator unavailable: {exc}")

    df = build_enterprise_log(n_cases=max(50, min(cases, 5000)), seed=7)
    facts = analyze_dataframe(df, process_type="Procure-to-Pay")
    facts.source_file = f"sample_enterprise_{len(df['case:concept:name'].unique())}cases.csv"

    run_id = uuid.uuid4().hex
    _RUNS[run_id] = facts
    payload = facts.to_dict()
    payload["run_id"] = run_id
    payload["persisted"] = _persist(facts) is not None
    return payload


class BriefRequest(BaseModel):
    run_id: str
    audience: str = "internal"
    provider: Optional[str] = None
    model: Optional[str] = None


@app.post("/api/brief")
def brief(req: BriefRequest) -> Dict[str, Any]:
    facts = _RUNS.get(req.run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id; analyze first.")

    provider = req.provider or os.environ.get("LLM_PROVIDER", "anthropic")
    if not os.environ.get(_PROVIDER_KEY.get(provider, "ANTHROPIC_API_KEY")):
        raise HTTPException(
            status_code=503,
            detail=f"No API key for provider '{provider}'. Set {_PROVIDER_KEY.get(provider)}.",
        )

    result = generate_brief(
        facts,
        audience=req.audience,
        provider=req.provider,
        model=req.model,
        kb=_knowledge_base(),  # grounds the brief in live benchmark evidence
    )
    return {
        "audience": result.audience,
        "markdown": result.markdown,
        "health_score": result.health_score,
        "grade": result.grade,
        "model_name": result.model_name,
        "redaction_warnings": result.redaction_warnings,
    }
