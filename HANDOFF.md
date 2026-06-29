# HANDOFF

_Session date: 2026-06-29_

## TL;DR
Phase 1 (the pm4py mining engine) is **built, tested, and verified end-to-end**.
The project is scaffolded with docs, tracking, and a clean git repo. Next concrete
step: **Phase 1.5 — the Supabase schema migration**.

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

## Next step (Phase 1.5)
Write a **reviewable SQL migration** (do not auto-apply) for the Supabase project
`zrggqvgtthlhwbayckuc` (eu-west-1, PG17, currently empty):
`clients`, `engagements`, `event_log_runs`, `process_facts (jsonb)`,
`knowledge_chunks (vector)`, `recommendations`. Enable `pgvector`. Then a thin
`persistence.py` to write a `ProcessFacts` row + a read-back test.

## Open decision (blocks Phase 2, not 1.5)
LLM provider + data handling — need a no-train DPA or a local model for client data.

## Gotchas
- pm4py is **AGPL**: keep it behind `engine.analyze()`; never expose to external users.
- Windows consoles are cp1252 — non-ASCII prints need `sys.stdout.reconfigure("utf-8")`.
- `pm4py.format_dataframe` re-groups by case, so the log isn't globally time-sorted
  (per-case order is what matters; downstream sorts explicitly).
- Don't commit `*.csv`/`*.xes`/`*.pdf` — `.gitignore` blocks them by design.
- Vendored repos (pm4py-release/, langchain-master/, etc.) are reference only, gitignored.
