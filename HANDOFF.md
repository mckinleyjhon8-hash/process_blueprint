# HANDOFF

_Session date: 2026-06-29_

## TL;DR
Phases **1–3 done & tested** (40 passing tests); **Phase 4 frontend foundation is
built and running**. pm4py engine → `ProcessFacts`; Supabase live (7 tables + pgvector
RPC); pluggable LLM brief; RAG evidence + stakeholder input. Phase 4 adds a
**Next.js 16 enterprise frontend** (premium-dark, UI/UX Pro Max) on a **FastAPI**
backend — builds clean, runs, screenshot-verified.

## Phase 4 — frontend foundation DONE this session
- `frontend/` — Next.js 16 + React 19 + Tailwind v4. Design system in `app/globals.css`
  (premium-dark tokens: bg/panel/line/fg/muted/primary/violet/success…; Plus Jakarta
  Sans + JetBrains Mono). NOTE: Next 16 has breaking changes — see `frontend/AGENTS.md`
  and `node_modules/next/dist/docs/`.
- App shell: `components/shell/{Sidebar,Topbar}.tsx`. Flagship dashboard `app/page.tsx`
  with `components/dashboard/*` (KpiRibbon, HealthScore ring, ModelRadar SVG, Bottlenecks,
  Variants, PhaseTracker) + interactive `BriefPanel` (internal/client toggle, client-safe badge).
- Seed data `lib/seed.ts` (real Phase-1 numbers) + `lib/types.ts` (ProcessFacts TS mirror)
  so the UI renders standalone. `npm run build` is green; runs with no console errors.
- Backend `backend/api.py` (FastAPI): /api/health, /api/analyze (upload→facts+run_id),
  /api/brief (run_id+audience→markdown). pm4py stays isolated here. Run:
  `uvicorn backend.api:app --reload --port 8000`.
- Preview: `.claude/launch.json` defines the `frontend` dev server (port 3000).
- Charts are hand-rolled SVG (no chart dep); only extra npm dep is `lucide-react`.
- node_modules/.next are gitignored (frontend/.gitignore + root safety net).

## Phase 3 — DONE this session
- `src/process_blueprint/knowledge/`: `embeddings.py` (factory: openai default /
  fake for tests, 1536 dims), `benchmarks.py` (8 process-type KPI chunks),
  `store.py` (InMemoryKB + SupabaseKB via pgvector RPC), `retrieval.py`, `types.py`.
- Migration `0002_knowledge_retrieval.sql` applied + verified live:
  `match_knowledge_chunks(query_embedding, match_count, filter_source, filter_engagement)`
  (cosine; returned sim=1.0 on a round-trip, then cleaned) and `stakeholder_inputs` table.
- `generate_brief(..., kb=, evidence=, stakeholder=, engagement_id=)` — retrieves
  evidence and feeds benchmark comparison + the qualitative WHY into the prompt.
- `scripts/ingest_knowledge.py [--dry-run]` loads benchmarks (live needs keys).
- Tests use the deterministic fake embedder (identical text → identical vector),
  so retrieval is validated without network. 40 passing.

## Phase 2 — DONE this session
- `src/process_blueprint/brief/`: `scoring.py` (real health score — sample = 95/A),
  `context.py` (audience-aware digest; client view omits conformance = leak-proof by
  construction), `prompts.py` (BABOK skeleton, internal + client systems),
  `redact.py` (client-safe output guard), `chain.py` (`generate_brief(facts, audience, llm=None)`).
- Default model `claude-opus-4-8` via langchain-anthropic (no temperature/budget_tokens).
- `llm=` is injectable → fully unit-tested with `FakeListChatModel`, no API key.
- CLI `scripts/run_phase2.py [--demo] [--audience client]`. Tests: **22 passed**.
- Replaces the legacy static `research_agent.py`.

## Phase 1.5 — DONE this session
- `supabase/migrations/0001_init.sql`: clients, engagements, event_log_runs,
  process_facts (jsonb), knowledge_chunks (pgvector + hnsw), recommendations.
- RLS enabled on every table, **no public policies** → public API exposes nothing;
  the app uses the service-role key server-side (bypasses RLS). The 6
  `rls_enabled_no_policy` advisor notices are INFO-level and **intentional**.
- `src/process_blueprint/persistence.py`: `run_row`/`facts_row` (pure, tested) +
  `insert_process_facts` (lazy supabase client; needs SUPABASE_URL + SUPABASE_SERVICE_KEY).
- Applied to live project `zrggqvgtthlhwbayckuc` and verified by inserting a full
  client→engagement→run→facts chain, reading it back (jsonb extraction worked),
  then deleting it (cascade left the DB clean). Tests: **13 passed**.

## What was done this session
- Decided the architecture: pm4py engine → Supabase(+pgvector) → LangChain → Streamlit;
  dropped `autoresearch`; RAGFlow optional. AGPL resolved (internal-only). See `CLAUDE.md §2`.
- Built `src/process_blueprint/`: `facts.py` (the `ProcessFacts` contract), `ingest.py`,
  `discovery.py`, `conformance.py`, `performance.py`, `engine.py`.
- Wrote tests (`tests/`) with a deterministic synthetic P2P log. **11 passing.**
- CLI `scripts/run_phase1.py` verified: emits `ProcessFacts` JSON.
- Docs: `CLAUDE.md`, `README.md`, `docs/PHASES.md`, `docs/TRACKING.md`, `docs/METHODOLOGY_MAP.md`.
- `.gitignore` excludes vendored repos, the BABOK PDF, and all client data.

## How to run / verify
```bash
pip install -r requirements.txt
pytest -q                      # expect: 11 passed
python scripts/run_phase1.py   # prints facts; --json to save
```
Verified result on the sample log: 60 cases, 3 variants, fitness=1.0, precision=0.97,
top bottleneck `Approve PO -> Receive Invoice` (~52.9 h), rework `Approve PO x7`.

## The contract to build against
`ProcessFacts` (see `src/process_blueprint/facts.py`) — every later layer consumes
this object, never the raw event log. `engine.analyze(file_path, process_type=...)`
returns it; `.to_json()` serialises it.

## Live wiring + production test — DONE this session
- Frontend ↔ backend wired: `frontend/lib/api.ts` (analyzeLog/getBrief), `lib/health.ts`,
  `components/dashboard/DashboardClient.tsx` (upload bar → /api/analyze → live render),
  BriefPanel → /api/brief. Verified live: 3,000-case enterprise CSV through /api/analyze
  in ~4s; /api/brief returns clean 503 until a key is set.
- Env: `.env.example` (all keys) + backend `load_dotenv`. **Add real keys to `.env`** (gitignored):
  `cp .env.example .env` then fill `ANTHROPIC_API_KEY` (or OPENAI/OPENROUTER) + `SUPABASE_SERVICE_KEY`.
- Comprehensive log: `tests/enterprise_log.py` + `scripts/generate_enterprise_log.py`
  (`--cases N`, writes to gitignored `data/`). 5 enterprise tests; 45 total.

## TO GO LIVE WITH BRIEFS
1. `cp .env.example .env`; paste your `ANTHROPIC_API_KEY` (do NOT commit / do NOT paste in chat).
2. Restart `uvicorn backend.api:app --port 8000`; upload a log in the UI; click Generate.

## Next step (Phase 4 — finish the portal)
Render the real Petri-net into the map panel (engine PNG/SVG endpoint), branded PDF
export, consultant "approve" gate, engagements/knowledge pages. Optionally match a
Figma frame (needs Dev/Full seat + URL). Then Phase 5 (auth/deploy).

## Run the full stack
```
pip install -r requirements.txt
cp .env.example .env            # then add your real keys (gitignored)
uvicorn backend.api:app --reload --port 8000      # backend
npm --prefix frontend install                      # once
npm --prefix frontend run dev                      # frontend → http://localhost:3000
python scripts/generate_enterprise_log.py          # 3000-case test log → data/
```
Frontend renders on seed data even without the backend; live analysis needs the API.

## Open decision (now blocks only LIVE Phase 2 generation, not the build)
LLM provider + data handling — need a no-train DPA or a local model before sending
real client data to Claude. eu-west-1 Supabase already helps with residency. The
code is provider-pluggable via `generate_brief(..., llm=...)`, so swapping to a
local model is a one-line change.

## LLM providers (pluggable)
`brief/providers.py` → `build_llm(provider, model, api_key=...)`. Select via:
- `LLM_PROVIDER` env: `anthropic` (default), `openai`, `openrouter`
- or per call: `generate_brief(facts, audience, provider="openrouter", model="anthropic/claude-opus-4")`
- keys: `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `OPENROUTER_API_KEY`; model overrides:
  `ANTHROPIC_MODEL` / `OPENAI_MODEL` / `OPENROUTER_MODEL`. OpenRouter base url + optional
  `OPENROUTER_REFERRER`/`OPENROUTER_TITLE` attribution headers. openai+openrouter share langchain-openai.
- CLI: `run_phase2.py --provider openrouter --model openai/gpt-4o` (or `--demo`).

## Phase 2 gotchas
- Opus 4.8 rejects `temperature`/`budget_tokens` (400). `ChatAnthropic` defaults temperature
  to None (not sent) — safe. OpenAI/OpenRouter accept temperature normally.
- The client-safe guarantee is two-layer: (1) client digest never contains the
  conformance numbers; (2) `redact.scan()` flags any leaked internal term in output.
- Tests never hit the network — they inject `FakeListChatModel`.

## Gotchas
- pm4py is **AGPL**: keep it behind `engine.analyze()`; never expose to external users.
- Windows consoles are cp1252 — non-ASCII prints need `sys.stdout.reconfigure("utf-8")`.
- `pm4py.format_dataframe` re-groups by case, so the log isn't globally time-sorted
  (per-case order is what matters; downstream sorts explicitly).
- Don't commit `*.csv`/`*.xes`/`*.pdf` — `.gitignore` blocks them by design.
- Vendored repos (pm4py-release/, langchain-master/, etc.) are reference only, gitignored.
