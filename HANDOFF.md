# HANDOFF

_Session date: 2026-06-29_

## TL;DR
Phases **1 and 1.5 are done, tested, and verified**. The pm4py engine emits
`ProcessFacts`; the Supabase schema is live and round-trip-verified. Next concrete
step: **Phase 2 — the LangChain + Claude brief layer** (blocked only on the LLM
data-handling decision).

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

## Next step (Phase 2 — LLM brief)
Build the LangChain + Claude layer: `ProcessFacts` → executive brief, using
`docs/METHODOLOGY_MAP.md` for the BABOK-shaped skeleton. Two render targets:
internal (full mechanics) and client-safe (results only, strips tool/method refs).
Replaces the legacy static `research_agent.py`. Wire `insert_process_facts` into
the flow once `SUPABASE_SERVICE_KEY` is available.

## Open decision (blocks Phase 2)
LLM provider + data handling — need a no-train DPA or a local model for client data.
eu-west-1 Supabase already helps with residency.

## Gotchas
- pm4py is **AGPL**: keep it behind `engine.analyze()`; never expose to external users.
- Windows consoles are cp1252 — non-ASCII prints need `sys.stdout.reconfigure("utf-8")`.
- `pm4py.format_dataframe` re-groups by case, so the log isn't globally time-sorted
  (per-case order is what matters; downstream sorts explicitly).
- Don't commit `*.csv`/`*.xes`/`*.pdf` — `.gitignore` blocks them by design.
- Vendored repos (pm4py-release/, langchain-master/, etc.) are reference only, gitignored.
