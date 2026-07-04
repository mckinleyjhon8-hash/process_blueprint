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
from process_blueprint.ingest import ingest                    # noqa: E402
from process_blueprint.brief import generate_brief             # noqa: E402
from process_blueprint.report import build_report_html         # noqa: E402
from process_blueprint.visualize import render_petri_net, graphviz_available  # noqa: E402

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
_DFS: Dict[str, Any] = {}             # run_id -> event-log DataFrame (for process-map render)
_DISCOVERY: Dict[str, Dict[str, bool]] = {}  # run_id -> operator checklist answers
_AI_ANSWERS: Dict[str, Dict[str, Any]] = {}  # run_id -> AI decision-tree answers
_ROI_INPUTS: Dict[str, Dict[str, Any]] = {}  # run_id -> operator financial inputs

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
        df, _ = ingest(tmp.name)  # keep the df so we can render the process map
        facts = analyze_dataframe(df, process_type=process_type, algorithm=algorithm)
        facts.source_file = file.filename or "uploaded.csv"
    except Exception as exc:  # surface ingest/mining errors cleanly
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    # Persist first and adopt the Supabase run id as canonical, so the same id
    # works in-session AND after a restart (rebuilt from the process_facts jsonb).
    persisted = _persist(facts)
    run_id = (persisted or {}).get("run_id") or uuid.uuid4().hex
    _RUNS[run_id] = facts
    _DFS[run_id] = df
    payload = facts.to_dict()
    payload["run_id"] = run_id
    payload["persisted"] = persisted is not None
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

    persisted = _persist(facts)
    run_id = (persisted or {}).get("run_id") or uuid.uuid4().hex
    _RUNS[run_id] = facts
    _DFS[run_id] = df
    payload = facts.to_dict()
    payload["run_id"] = run_id
    payload["persisted"] = persisted is not None
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
    # In-session first, else rebuild from Supabase so archived runs work too.
    facts = _facts_for_run(req.run_id)
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


def _facts_for_run(run_id: str) -> Optional[ProcessFacts]:
    """In-session facts, else rebuild from the Supabase process_facts jsonb."""
    facts = _RUNS.get(run_id)
    if facts is not None:
        return facts
    client = _supabase()
    if client is None:
        return None
    try:
        rows = (client.table("process_facts").select("facts")
                .eq("run_id", run_id).limit(1).execute().data or [])
        if rows:
            return ProcessFacts.from_dict(rows[0]["facts"])
    except Exception:
        pass
    return None


@app.get("/api/run/{run_id}")
def run_detail(run_id: str) -> Dict[str, Any]:
    """Full facts for one run (in-session or rebuilt from Supabase) — powers /runs/[id]."""
    facts = _facts_for_run(run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id.")
    payload = facts.to_dict()
    payload["run_id"] = run_id
    compliance = _COMPLIANCE.get(run_id)
    if compliance is not None:
        payload["compliance"] = compliance
    # The Petri net can only render while the log is cached this session.
    payload["has_map"] = run_id in _DFS and graphviz_available()
    return payload


class DiscoveryAnswers(BaseModel):
    answers: Dict[str, bool]


@app.get("/api/discovery/{run_id}")
def discovery_get(run_id: str) -> Dict[str, Any]:
    """Current discovery-completeness scoring (auto + operator answers)."""
    facts = _facts_for_run(run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id.")
    from process_blueprint.discovery_completeness import compute

    report = compute(
        facts,
        manual_answers=_DISCOVERY.get(run_id, {}),
        has_sop_rules=run_id in _COMPLIANCE,
    )
    report["answers"] = _DISCOVERY.get(run_id, {})
    return report


@app.post("/api/discovery/{run_id}")
def discovery_post(run_id: str, req: DiscoveryAnswers) -> Dict[str, Any]:
    """Merge operator checklist answers and rescore the six domains."""
    facts = _facts_for_run(run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id.")
    merged = {**_DISCOVERY.get(run_id, {}), **req.answers}
    _DISCOVERY[run_id] = {k: v for k, v in merged.items() if v}  # keep only asserted
    from process_blueprint.discovery_completeness import compute

    report = compute(
        facts,
        manual_answers=_DISCOVERY[run_id],
        has_sop_rules=run_id in _COMPLIANCE,
    )
    report["answers"] = _DISCOVERY[run_id]
    # keep the in-session facts in sync so reports/briefs see the latest score
    if run_id in _RUNS:
        _RUNS[run_id].discovery = {k: v for k, v in report.items() if k != "answers"}
    return report


class AiAnswers(BaseModel):
    answers: Dict[str, Any]


@app.get("/api/ai-assessment/{run_id}")
def ai_assessment_get(run_id: str) -> Dict[str, Any]:
    """Current AI decision-tree assessment (conservative until answered)."""
    facts = _facts_for_run(run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id.")
    from process_blueprint.ai_risk import assess

    report = assess(facts, _AI_ANSWERS.get(run_id))
    report["answers"] = _AI_ANSWERS.get(run_id, {})
    return report


@app.post("/api/ai-assessment/{run_id}")
def ai_assessment_post(run_id: str, req: AiAnswers) -> Dict[str, Any]:
    """Merge operator answers (incl. readiness overrides) and re-walk the tree."""
    facts = _facts_for_run(run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id.")
    current = _AI_ANSWERS.get(run_id, {})
    readiness = {**current.get("readiness", {}), **(req.answers.get("readiness") or {})}
    merged = {**current, **req.answers}
    if readiness:
        merged["readiness"] = readiness
    # None values clear an answer (lets the operator undo a choice)
    _AI_ANSWERS[run_id] = {k: v for k, v in merged.items() if v is not None}
    from process_blueprint.ai_risk import assess

    report = assess(facts, _AI_ANSWERS[run_id])
    report["answers"] = _AI_ANSWERS[run_id]
    if run_id in _RUNS:
        _RUNS[run_id].ai_assessment = {k: v for k, v in report.items() if k != "answers"}
    return report


class RoiInputs(BaseModel):
    inputs: Dict[str, Any]


@app.get("/api/roi/{run_id}")
def roi_get(run_id: str) -> Dict[str, Any]:
    """Current investment appraisal (uncomputed shell until inputs stated)."""
    facts = _facts_for_run(run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id.")
    from process_blueprint.roi import compute as roi_compute

    return roi_compute(facts, _ROI_INPUTS.get(run_id, {}))


@app.post("/api/roi/{run_id}")
def roi_post(run_id: str, req: RoiInputs) -> Dict[str, Any]:
    """Merge operator financial inputs and recompute the 3-year appraisal."""
    facts = _facts_for_run(run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id.")
    merged = {**_ROI_INPUTS.get(run_id, {}), **req.inputs}
    _ROI_INPUTS[run_id] = {k: v for k, v in merged.items() if v is not None}
    from process_blueprint.roi import compute as roi_compute

    report = roi_compute(facts, _ROI_INPUTS[run_id])
    if run_id in _RUNS:
        _RUNS[run_id].roi = report
    return report


@app.get("/api/process-map/{run_id}")
def process_map(run_id: str, algorithm: str = "inductive"):
    """Render the discovered Petri net for an in-session run as an SVG image."""
    df = _DFS.get(run_id)
    if df is None:
        raise HTTPException(status_code=404, detail="No cached log for this run.")
    svg = render_petri_net(df, algorithm=algorithm, fmt="svg")
    if svg is None:
        raise HTTPException(status_code=503, detail="Graphviz unavailable to render the Petri net.")
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/api/report/{run_id}")
def report(run_id: str, audience: str = "client", download: int = 0):
    """Render the branded HTML deliverable for a run (client or internal)."""
    facts = _facts_for_run(run_id)
    if facts is None:
        raise HTTPException(status_code=404, detail="Unknown run_id.")

    brief = _BRIEFS.get((run_id, audience))
    brief_md = brief.markdown if brief is not None else None
    compliance = _COMPLIANCE.get(run_id)

    # Real Petri net for in-session runs (we have the log cached); else the flow SVG.
    # Top-to-bottom orientation fills the report's portrait page instead of
    # shrinking a very wide left-to-right net.
    map_svg = None
    df = _DFS.get(run_id)
    if df is not None:
        raw = render_petri_net(df, fmt="svg", rankdir="TB")
        if raw:
            map_svg = raw.decode("utf-8", "replace")

    html = build_report_html(
        facts, brief_md, audience=audience, compliance=compliance, process_map_svg=map_svg
    )

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
        "render": {"graphviz": graphviz_available()},
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
