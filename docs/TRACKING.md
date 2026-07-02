# Tracking — live status

> Update this as work lands. `[x]` done · `[~]` in progress · `[ ]` todo.
> Rule: nothing is `[x]` unless it has a passing test or a verified run.

_Last updated: 2026-06-29 (Phase 4 frontend foundation built & running)_

## Phase 1 — Mining engine → ProcessFacts  ✅
- [x] `facts.py` — ProcessFacts / ModelQuality / Bottleneck / Variant + JSON
- [x] `ingest.py` — CSV/XES, auto + explicit column mapping, cleaning
- [x] `discovery.py` — Inductive + Heuristics miners
- [x] `conformance.py` — real fitness/precision/generalization/simplicity
- [x] `performance.py` — KPIs, bottlenecks, variants, rework
- [x] `engine.py` — orchestration → ProcessFacts
- [x] Tests green: **11 passed** (`pytest -q`)
- [x] CLI verified: `run_phase1.py` emits ProcessFacts JSON
- [x] Verified on synthetic P2P log: fitness=1.0, precision=0.97, bottleneck=Approve PO

## Phase 1.5 — Supabase schema  ✅
- [x] Migration SQL `supabase/migrations/0001_init.sql` (clients, engagements, event_log_runs, process_facts, knowledge_chunks, recommendations)
- [x] `pgvector` enabled (hnsw cosine index on knowledge_chunks)
- [x] RLS enabled on all tables, no public policies (service-role-only; locked public API)
- [x] `persistence.py` — `run_row` / `facts_row` / `insert_process_facts`
- [x] Unit tests for row mapping (**13 passed** total)
- [x] Applied to live project `zrggqvgtthlhwbayckuc` and verified with a
      round-trip insert/read-back (jsonb path extraction OK), then cleaned up
- [ ] Wire `insert_process_facts` into the live flow (needs SUPABASE_SERVICE_KEY) — deferred to app integration

## Phase 2 — LLM brief  ✅ (built & tested; live gen pending key)
- [x] BABOK-shaped prompt skeleton in `brief/prompts.py` (from METHODOLOGY_MAP)
- [x] LangChain chain: facts → prompt → Claude → brief (`brief/chain.py`)
- [x] Internal template + client-safe template (two audiences)
- [x] Real Process Health Score from conformance metrics (`brief/scoring.py`) — sample = 95/A
- [x] Leak prevention by construction: client digest omits conformance (`brief/context.py`)
- [x] Client-safe output guard: `brief/redact.py` flags leaked internal terms
- [x] Default model wired: `claude-opus-4-8` (langchain-anthropic, no temperature)
- [x] **Pluggable provider** (`brief/providers.py`): anthropic | openai | openrouter, via `LLM_PROVIDER` env or `generate_brief(provider=, model=)` — 7 provider tests
- [x] Tests with fake chat model — **22 passed** total; CLI `run_phase2.py --demo`
- [ ] Live generation against real Claude — needs `ANTHROPIC_API_KEY` + data-handling decision
- [ ] `methodology_map.yaml` as a standalone asset (currently encoded in prompts.py)

## Phase 3 — Knowledge retrieval  ✅ (built & tested; live ingest needs keys)
- [x] `knowledge/` package: types, embeddings factory (openai|fake), benchmarks,
      store (InMemoryKB + SupabaseKB), retrieval
- [x] 8 process-type KPI benchmarks as retrievable chunks (`benchmarks.py`)
- [x] Migration `0002_knowledge_retrieval.sql` applied: `match_knowledge_chunks`
      pgvector RPC + `stakeholder_inputs` table — verified live (sim=1.0, then cleaned)
- [x] Evidence + stakeholder input wired into `build_context` / `generate_brief`
      (optional `kb=`, `evidence=`, `stakeholder=`, `engagement_id=`)
- [x] Prompts instruct using benchmark_evidence + stakeholder_input
- [x] Tests with fake embedder — **40 passed** total; `ingest_knowledge.py --dry-run`
- [ ] Live ingest into Supabase — needs OPENAI_API_KEY + SUPABASE_SERVICE_KEY
- [ ] Stakeholder-input UI form (Phase 4 Streamlit; data model + wiring done)
- [ ] Methodology subset chunks (benchmarks done; curated framework text next)

## Phase 4 — Portal + deliverable  🟡 (frontend foundation built & running)
- [x] **Next.js 16 + React 19 + Tailwind v4** app in `frontend/` (premium-dark
      enterprise design system from UI/UX Pro Max: indigo/violet, Plus Jakarta Sans + JetBrains Mono)
- [x] App shell (sidebar + topbar), flagship **Dashboard**: KPI ribbon, health-score
      ring, model-quality radar (SVG), bottlenecks, variants, phase tracker
- [x] Interactive **AI brief panel** with internal/client audience toggle + client-safe badge
- [x] **FastAPI backend** `backend/api.py`: /api/health, /api/analyze (upload→facts), /api/brief
- [x] `npm run build` green (TS + lint pass, 0 errors); runs, screenshot verified, no console errors
- [x] **Frontend wired LIVE** to backend: `lib/api.ts` + `DashboardClient` (upload → /api/analyze →
      renders live facts) + BriefPanel (→ /api/brief). `lib/health.ts` mirrors the score.
- [x] **Secure env**: `.env.example` + backend `load_dotenv`; real keys go in gitignored `.env` only
- [x] **Comprehensive enterprise test log** (`tests/enterprise_log.py`): tiered approvals, rejections,
      cancellations, returns, invoice exceptions, escalations, business-hours timing, named resources
- [x] **Production-scale proof**: live /api/analyze on 3,000 cases / 38,199 events in ~4s →
      17 activities, 42 variants, fitness 1.0 / precision 0.93. 45 Python tests pass.
- [x] **FULLY LIVE with real keys**: knowledge ingested to Supabase (8 benchmarks, OpenAI
      embeddings); live pgvector retrieval ranks correctly; /api/analyze **persists**
      client→engagement→run→facts to Supabase; /api/brief generates a **real claude-opus-4-8**
      brief grounded in benchmark evidence (47s, health 93/A, client-safe guard: 0 leaks)
- [x] **Branded report export** (`src/process_blueprint/report.py`): light, print-ready,
      self-contained HTML deliverable (cover, health ring, KPIs, dependency-free process-flow
      SVG, brief, bottlenecks, compliance) → `GET /api/report/{run_id}` (+ `download=1`).
      Audience-aware (client view strips mechanics). Browser "Save as PDF" = the PDF.
      Verified live: report HTTP 200, 27KB, real Claude brief embedded; 4 report tests.
- [x] **Consultant approve gate**: client report export is disabled until "Approve for client".
- [x] **Real Petri-net render** (`src/process_blueprint/visualize.py`): pm4py + Graphviz
      Petri net served at `GET /api/process-map/{run_id}`, embedded in the dashboard
      process-map card and the branded report. Auto-locates `dot` on Windows paths;
      degrades to the dependency-free SVG flow when Graphviz is absent
      (`/api/config` reports `render.graphviz`).
- [x] **Declarative compliance engine** (`src/process_blueprint/compliance.py`):
      existence / precedence / within_days rules (FREIGHT_SOP_RULES) + BPMN conformance
      against a documented model (`read_bpmn → Petri → token replay`). Freight check
      now runs through it; 3 new tests.
- [x] **Archived-run reports**: `ProcessFacts.from_dict` rebuilds facts from the
      Supabase jsonb, so /briefs "open" works for past runs, not just in-session ones.
- [x] Py3.11 compat fix in report.py (backslash-in-f-string SyntaxError).
- [x] **Routed portal**: sidebar uses next/link + active state; pages /engagements,
      /briefs, /knowledge, /settings, each fetching live backend data
      (/api/engagements, /api/runs, /api/knowledge — graceful Supabase/in-memory).
- [x] **Admin model panel** (/settings): pick generation provider + model
      (anthropic/openai/openrouter, suggested or custom), key-present badges,
      embeddings/Supabase status; saved per-browser, applied to /api/brief.
- [x] **Enterprise redesign (IA + design system)**: token-driven system in `globals.css`;
      `components/ui/` primitives (Button/Badge/Card/Field/Tabs/DataTable/EmptyState/
      Skeleton/Kbd/Page); Ctrl+K command palette; breadcrumb topbar + mobile drawer nav;
      per-run workspace `/runs/[id]` (Overview/Map/Compliance/Brief tabs); full-viewport
      **Map Studio** `/runs/[id]/map` (zoom/pan/fit/fullscreen/minimap, facts-derived
      dependency graph + Petri-net layer, inspector, search); sortable/searchable tables;
      dashboard = command center (attention items, recent runs, system status);
      GET /api/run/{id} powers deep links. WCAG focus rings + reduced-motion.
- [x] **Monday-class light re-skin**: UI/UX Pro Max `colors.csv` №21 basis —
      #6161FF primary on #F6F7FB canvas, white surfaces, rainbow status accents
      (#00C875/#FDAB3D/#E2445C/#579BFC/#A25DDC), Figtree typeface; map canvas +
      graph re-tokenised for light (`--map-*` vars). Verified live in preview.
- [x] **Report visuals get full pages**: discovered model on its own print page
      (Petri net rendered top-to-bottom via `rankdir=TB`, fixed px dims stripped so
      it scales to page width) + new **activity word map** page (all activities
      sized by frequency, bottleneck steps amber, top-8 frequency table). 60 tests.
- [ ] Optional: match a specific Figma frame (needs Dev/Full seat + frame URL)

## Elite program (docs/ELITE_ROADMAP.md) — Phase E1: Discovery
- [x] **pm4py activation** (`insights.py`): performance DFG (freq + mean/median/stdev
      wait per edge), case-duration percentiles P10/P50/P90 + heavy-tail ratio,
      top-variant/top-5 coverage + honest exception rate, FPY/rework-case-rate,
      resource analytics from org:resource (roles, hand-overs, SPOF), batch
      detection (best-effort). ProcessFacts **v1.1** (additive; jsonb-roundtrip safe).
- [x] **Benchmark engine** (`benchmarks.py`): seeded UK SME quartile tables
      (AP/O2C/onboarding/support/payroll/recruitment + generic VSM), direction-aware
      quartile positioning, ambition-ladder targets (Q1→median … Q4→hold),
      plausibility thresholds + zero-claims rule; every position cites source+grade.
- [x] **Discovery completeness** (`discovery_completeness.py`): six playbook domains
      point-scored with Must/Should/Complete gates; the event log auto-evidences
      items at E1 (freight: Process domain 95 from upload alone); operator confirms
      the rest via guided questions; overall formula + ROI gate (blocked/caveated/pass).
- [x] **API + UI**: GET/POST `/api/discovery/{run_id}`; run-workspace **Discovery tab**
      (score badge, gate banner, six domain cards with live checklist, follow-up
      questions) + **Benchmark position card** on Overview. Verified live: freight run
      14.3/blocked → 10 answers → 71.3/pass; UI toggle rescores instantly. 71 tests.
- [ ] E2 Redesign: H1–H12 heuristic engine → computed TO-BE deltas, ECRS gates
- [ ] E3 AI-Risk · E4 ROI · E5 Consultant-OS gates · E6 knowledge depth · E7 compliance breadth

## Phase 5 — Hardening
- [ ] Internal auth + engagement workspaces
- [ ] Deployment + audit trail
