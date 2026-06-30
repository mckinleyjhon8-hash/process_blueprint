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
from fastapi.responses import HTMLResponse, Response
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
from process_blueprint.report import build_report_html         # noqa: E402

app = FastAPI(title="Process Blueprint API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory caches (internal-only tool, single worker).
_RUNS: Dict[str, ProcessFacts] = {}
_BRIEFS: Dict[tuple, Any] = {}        # (run_id, audience) -> BriefResult
_COMPLIANCE: Dict[str, Any] = {}      # run_id -> SOP compliance report

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
def analyze_sample(cases: int = 400, process: str = "Procure-to-Pay") -> Dict[str, Any]:
    """Generate a comprehensive sample log server-side and analyse it.

    One-click live demo of the whole pipeline — no file upload needed.
    `process` selects the scenario: Procure-to-Pay (default) or a UK freight
    brokerage SOP log (which also runs a rule-based SOP compliance check).
    """
    n = max(50, min(cases, 5000))
    compliance = None
    try:
        if "freight" in process.lower() or "broker" in process.lower():
            from tests.freight_log import build_freight_log, check_sop_compliance

            df = build_freight_log(n_cases=n, seed=11)
            facts = analyze_dataframe(df, process_type="UK Freight Brokerage")
            facts.source_file = f"sample_freight_{n}cases.csv"
            compliance = check_sop_compliance(df)
        else:
            from tests.enterprise_log import build_enterprise_log

            df = build_enterprise_log(n_cases=n, seed=7)
            facts = analyze_dataframe(df, process_type="Procure-to-Pay")
            facts.source_file = f"sample_enterprise_{n}cases.csv"
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"sample generation failed: {exc}")

    run_id = uuid.uuid4().hex
    _RUNS[run_id] = facts
    payload = facts.to_dict()
    payload["run_id"] = run_id
    payload["persisted"] = _persist(facts) is not None
    if compliance is not None:
        payload["compliance"] = compliance
        _COMPLIANCE[run_id] = compliance
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
    _BRIEFS[(req.run_id, result.audience)] = result  # reused by the report endpoint
    return {
        "audience": result.audience,
        "markdown": result.markdown,
        "health_score": result.health_score,
        "grade": result.grade,
        "model_name": result.model_name,
        "redaction_warnings": result.redaction_warnings,
    }


@app.get("/api/report/{run_id}")
def report(run_id: str, audience: str = "client", download: int = 0):
    """Render the branded HTML deliverable for a run (client or internal)."""
    facts = _RUNS.get(run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id; analyze first.")

    brief = _BRIEFS.get((run_id, audience))
    brief_md = brief.markdown if brief is not None else None
    compliance = _COMPLIANCE.get(run_id)

    html = build_report_html(facts, brief_md, audience=audience, compliance=compliance)

    if download:
        fname = f"{facts.process_type.replace(' ', '_')}_{audience}_report.html"
        return Response(
            content=html,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )
    return HTMLResponse(content=html)


# --------------------------------------------------------------------------- #
# Admin / config + listing endpoints (route the whole frontend to the backend)
# --------------------------------------------------------------------------- #
_MODELS = {
    "anthropic": ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4.1"],
    "openrouter": [
        "anthropic/claude-opus-4",
        "openai/gpt-4o",
        "google/gemini-2.0-flash-exp",
        "meta-llama/llama-3.3-70b-instruct",
    ],
}


@app.get("/api/config")
def config() -> Dict[str, Any]:
    """Admin panel data: which providers/models are usable, key presence, infra."""
    from process_blueprint.brief.providers import DEFAULTS

    providers = {
        p: {
            "key_present": bool(os.environ.get(_PROVIDER_KEY[p])),
            "default_model": DEFAULTS[p],
            "models": _MODELS.get(p, []),
        }
        for p in ("anthropic", "openai", "openrouter")
    }
    return {
        "llm": {
            "default_provider": os.environ.get("LLM_PROVIDER", "anthropic"),
            "providers": providers,
        },
        "embeddings": {
            "provider": os.environ.get("EMBEDDINGS_PROVIDER", "openai"),
            "key_present": bool(os.environ.get("OPENAI_API_KEY")),
        },
        "supabase": {"configured": _supabase() is not None},
    }


@app.get("/api/engagements")
def engagements() -> Dict[str, Any]:
    client = _supabase()
    if client is None:
        return {
            "source": "memory",
            "engagements": [
                {"id": "local", "name": "Local session", "client_name": "—",
                 "process_type": "—", "status": "active", "runs": len(_RUNS)}
            ],
        }
    try:
        from collections import Counter

        engs = (client.table("engagements")
                .select("id,name,process_type,status,created_at,client_id")
                .order("created_at", desc=True).execute().data or [])
        runs = client.table("event_log_runs").select("engagement_id").execute().data or []
        cnt = Counter(r.get("engagement_id") for r in runs)
        names = {c["id"]: c["name"] for c in
                 (client.table("clients").select("id,name").execute().data or [])}
        for e in engs:
            e["runs"] = cnt.get(e["id"], 0)
            e["client_name"] = names.get(e.get("client_id"), "—")
        return {"source": "supabase", "engagements": engs}
    except Exception as exc:  # pragma: no cover
        return {"source": "error", "error": str(exc), "engagements": []}


@app.get("/api/runs")
def runs() -> Dict[str, Any]:
    client = _supabase()
    if client is None:
        return {"source": "memory", "runs": [
            {"run_id": rid, "process_type": f.process_type, "n_cases": f.n_cases,
             "n_variants": f.n_variants, "model_fitness": f.model.fitness,
             "model_precision": f.model.precision, "created_at": f.generated_at}
            for rid, f in list(_RUNS.items())[::-1]
        ]}
    try:
        rows = (client.table("process_facts")
                .select("run_id,process_type,n_cases,n_variants,model_fitness,model_precision,created_at")
                .order("created_at", desc=True).limit(50).execute().data or [])
        return {"source": "supabase", "runs": rows}
    except Exception as exc:  # pragma: no cover
        return {"source": "error", "error": str(exc), "runs": []}


@app.get("/api/knowledge")
def knowledge() -> Dict[str, Any]:
    client = _supabase()
    if client is None:
        return {"configured": False, "total": 0, "by_source": {}, "chunks": []}
    try:
        from collections import Counter

        rows = client.table("knowledge_chunks").select("source,title").execute().data or []
        by_source = dict(Counter(r.get("source") for r in rows))
        return {
            "configured": True,
            "total": len(rows),
            "by_source": by_source,
            "chunks": [{"source": r.get("source"), "title": r.get("title")} for r in rows[:60]],
        }
    except Exception as exc:  # pragma: no cover
        return {"configured": True, "total": 0, "by_source": {}, "chunks": [], "error": str(exc)}
