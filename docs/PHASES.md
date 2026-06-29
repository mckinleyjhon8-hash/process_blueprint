# Phases — detailed plan

Each phase ships standalone value and ends green (`pytest`) with `HANDOFF.md` + `TRACKING.md` updated.

---

## Phase 1 — Mining engine → `ProcessFacts`  ✅ DONE
**Outcome:** a deterministic engine that turns a CSV/XES event log into a typed,
serialisable `ProcessFacts` object — the contract every later layer consumes.

Delivered:
- `ingest` — CSV/XES load, column auto-mapping + explicit mapping, cleaning, pm4py format.
- `discovery` — Inductive Miner (default) + Heuristics Miner; no Graphviz dependency.
- `conformance` — **real** token-replay fitness + precision, best-effort alignment fitness,
  generalization, simplicity. (Fixes the original always-"F" health-score bug.)
- `performance` — KPIs (cycle times), bottlenecks (mean+1σ on DF waits), variants, rework.
- `engine.analyze()` / `analyze_dataframe()` — orchestration → `ProcessFacts`.
- Tests: 11 passing (ingest + e2e). CLI: `scripts/run_phase1.py`.

## Phase 1.5 — Supabase schema (internal)
**Outcome:** facts and runs persist; foundation for knowledge + recommendations.
Tables (no client auth — internal team only):
- `clients`, `engagements`, `event_log_runs`, `process_facts` (jsonb),
  `knowledge_chunks` (vector via pgvector), `recommendations` (status/priority/owner).
Deliver as a **reviewable SQL migration** (not auto-applied). Add a thin
`persistence.py` that writes a `ProcessFacts` row.

## Phase 2 — LLM brief (LangChain + Claude)
**Outcome:** `ProcessFacts` → executive brief + recommendations.
- Prompt templates driven by `docs/METHODOLOGY_MAP.md` (BABOK-shaped skeleton).
- **Two render targets:** internal view (full pm4py mechanics) and **client-safe view**
  (results only — strips all tool/method references).
- Replaces the legacy static `research_agent.py`.
- Needs the LLM data-handling decision (no-train DPA or local).

## Phase 3 — Knowledge retrieval
**Outcome:** briefs grounded in evidence, with citations.
- Ingest: domain KPI benchmarks + curated framework subset + per-client docs.
- Supabase pgvector retrieval wired into the LangChain chain.
- Per-engagement stakeholder-input form (closes the Elicitation gap).

## Phase 4 — Portal + deliverable
**Outcome:** internal Streamlit portal; branded PDF/HTML export.
- Dashboard (KPIs, process map, conformance) + brief panel.
- Styling from UI/UX Pro Max design data (palette/typography/UX rules).
- Human-in-the-loop "consultant approve" gate before client-final.

## Phase 5 — Hardening
**Outcome:** internal auth, engagement workspaces, deployment, audit trail.
