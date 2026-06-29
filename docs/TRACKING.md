# Tracking — live status

> Update this as work lands. `[x]` done · `[~]` in progress · `[ ]` todo.
> Rule: nothing is `[x]` unless it has a passing test or a verified run.

_Last updated: 2026-06-29 (Phase 1.5 schema applied & verified)_

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

## Phase 2 — LLM brief
- [ ] `methodology_map.yaml` bound to the ProcessFacts schema
- [ ] LangChain chain: facts → brief
- [ ] Internal template + client-safe template
- [ ] Decision logged: LLM provider + data handling
- [ ] Tests: brief contains required sections; client-safe view strips tool names

## Phase 3 — Knowledge retrieval
- [ ] Curate framework subset into `knowledge/`
- [ ] Benchmarks loaded; pgvector retrieval wired
- [ ] Stakeholder-input form
- [ ] Tests: retrieval returns relevant chunks for a process type

## Phase 4 — Portal + deliverable
- [ ] Streamlit dashboard on ProcessFacts
- [ ] Branded PDF/HTML export (UI/UX Pro Max styling)
- [ ] Consultant approve gate

## Phase 5 — Hardening
- [ ] Internal auth + engagement workspaces
- [ ] Deployment + audit trail
