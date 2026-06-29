# HANDOFF

_Session date: 2026-06-29_

## TL;DR
Phases **1, 1.5, 2, and 3 are done and tested** (40 passing tests). pm4py engine
→ `ProcessFacts`; Supabase schema live (now 7 tables + a pgvector RPC); LangChain
brief layer with pluggable provider (anthropic/openai/openrouter); Phase 3 adds
RAG evidence (benchmarks) + stakeholder input wired into the brief. Pending live
bits need keys only. Next concrete step: **Phase 4 — Streamlit portal + branded
report export**.

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

## Next step (Phase 4 — portal + deliverable)
Build the internal Streamlit portal on `ProcessFacts`: upload log → run engine →
show KPIs/process map/health score → generate brief (internal + client views) →
branded PDF/HTML export styled with the UI/UX Pro Max data. Add the
stakeholder-input form (data model + brief wiring already done in Phase 3) and the
consultant "approve" gate before a brief goes client-final. Also wire live
persistence (`insert_process_facts`, knowledge ingest) once keys are available.

Remaining Phase 3 polish (optional): add curated methodology-framework chunks
(benchmarks already loaded) and run the live ingest into Supabase.

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
