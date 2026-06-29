# Process Blueprint — CLAUDE.md

> Internal process-mining & consulting-intelligence tool.
> This file is the single source of truth for goal, architecture, knowledge, phases,
> and how we track progress. Read it first every session.

---

## 1. Goal

Build an **internal-only** tool that lets our consulting firm deliver fact-based
process improvement to **SME** clients fast. We ingest a client's event log
(and optionally their documents), automatically mine the *as-is* process, quantify
performance and conformance, and generate a **client-ready brief** with findings,
recommendations and a business case — framed in BABOK-recognisable methodology.

**Clients never see or access this tool.** They receive only the outputs:
reports, recommendations, solutions — the *what*, never the *how/where*.

### Why this wins
Classic BA builds the as-is from interviews (subjective, slow, sampled).
We replace that with **objective, complete, evidence-based** discovery from real
event data, then spend consultant time on the *why* and the change strategy.

---

## 2. Architecture (target)

```
Event logs (CSV/XES) ─► pm4py mining engine ─┐
                                             ├─► LangChain orchestration ─► Streamlit portal ─► Deliverable
Client docs (PDF/SOPs) ─► Supabase pgvector ─┘        (facts + evidence + LLM)   (internal)      (internal + client-safe views)
```

- **Mining engine (pm4py)** — discovery, conformance, performance. Emits `ProcessFacts`.
- **Knowledge (Supabase Postgres + pgvector)** — benchmarks, methodology, per-client docs.
  Replaces RAGFlow for SME scale; RAGFlow only if heavy scanned-PDF parsing is needed.
- **Orchestration (LangChain)** — composes facts + retrieved evidence → brief. **Pluggable provider**
  via `LLM_PROVIDER`: `anthropic` (default, `claude-opus-4-8`), `openai`, or `openrouter`
  (OpenAI-compatible). Swap with `generate_brief(..., provider=..., model=...)` or env vars.
- **Portal (Streamlit)** — internal UI; styled using UI/UX Pro Max design data.
- **Persistence/auth (Supabase)** — internal team only; per-engagement data.

### Components & licenses (resolved)
| Component | Role | License | Note |
|---|---|---|---|
| pm4py | core engine | **AGPL-3.0** | Internal-only ⇒ copyleft never triggers. Reports are not derivative works. Embed freely; keep it isolated in the batch engine. |
| LangChain | LLM orchestration | MIT | — |
| Supabase | data + pgvector + auth | — | Project `zrggqvgtthlhwbayckuc`, eu-west-1, PG17. |
| UI/UX Pro Max | design *data* (CSVs) | MIT | Not a runtime import; reference data. |
| RAGFlow | heavy RAG | Apache-2.0 | Optional / later. |
| autoresearch | — | — | **DROPPED** (Karpathy's GPT-training harness; irrelevant). |

### The only open decision
LLM data handling: need a **no-train DPA** or a **local model** for the LangChain
step (client-data confidentiality from NDA, not AGPL). eu-west-1 Supabase helps.

---

## 3. Knowledge assets

- **`enterprise_process_analysis_knowledge_framework.md`** — 13.5k-line, 17-discipline
  framework. **Use only the SME slice:** §2 Business Analysis, §3 Process Analysis,
  §4 Operational Excellence, §5 Root Cause, §12 Decision + the Agent Capability Matrix.
  Ignore enterprise-scale §1/§6/§7/§10/§11/§13–17. Ingestible (it's our own content).
- **`BABOK_Guide_v3_Member.pdf`** — IIBA copyrighted, *"Not for Distribution or Resale."*
  **RULE: methodology scaffold in our own words, NOT RAG content.** Never ingest the PDF
  into the deliverable pipeline. Distilled into `docs/METHODOLOGY_MAP.md`.

### BABOK coverage of our tool
- **Enhanced** (beyond manual BA): Strategy Analysis → *Analyze Current State*; Solution Evaluation.
- **Augmented** (tool + human): Requirements Analysis & Design; Requirements Lifecycle Mgmt.
- **Gaps** (human-led): Elicitation & Collaboration (mining = *what*, not *why*); BA Planning & Monitoring.
- **Closing the gaps cheaply:** per-engagement stakeholder-input form + a human-in-the-loop
  "consultant approve" step before any brief is client-final.

---

## 4. Phases & tracking

Full detail in `docs/PHASES.md`. **Live status in `docs/TRACKING.md`** (update it as work lands).

| Phase | Outcome | Status |
|---|---|---|
| **1** | Hardened engine → `ProcessFacts` (inductive+heuristics, real conformance, KPIs, bottlenecks, rework) | ✅ **DONE & tested** |
| 1.5 | Supabase schema (engagements/runs/facts/knowledge+pgvector/recommendations) | ✅ **DONE & verified** |
| 2 | LangChain + Claude brief from facts; internal + client-safe templates | ✅ **built & tested** (live needs API key) |
| 3 | Knowledge retrieval (benchmarks + curated framework + client docs) | ✅ **built & tested** (live ingest needs keys) |
| 4 | Streamlit portal + branded PDF export (UI/UX Pro Max) | ⬜ |
| 5 | Internal auth, engagement workspaces, deployment | ⬜ |

### Tracking method
1. `docs/TRACKING.md` holds a checklist per phase — tick items as merged.
2. Every code change ships with a test; `pytest` must stay green.
3. `HANDOFF.md` is rewritten at the end of each working session.
4. Durable decisions live here (CLAUDE.md §2) so they're not relitigated.

---

## 5. Repo structure
```
src/process_blueprint/   # the engine (Phase 1)
  facts.py               # ProcessFacts contract  <-- the cross-layer payload
  ingest.py  discovery.py  conformance.py  performance.py  engine.py
tests/                   # pytest suite + deterministic synthetic log
scripts/run_phase1.py    # CLI: log -> ProcessFacts JSON
docs/                    # PHASES, TRACKING, METHODOLOGY_MAP
CLAUDE.md  HANDOFF.md  README.md  requirements.txt
# Legacy prototype (kept for reference, superseded by src/): app.py, mining_engine.py,
# research_agent.py, platform_generator.html
```

## 6. Commands
```bash
pip install -r requirements.txt
pytest -q                              # run the test suite (must be green)
python scripts/run_phase1.py           # demo on a generated sample log
python scripts/run_phase1.py log.csv --process-type "Order-to-Cash" --json out.json
```

## 7. Conventions
- pm4py stays **behind `engine.analyze()`** — no pm4py imports leak into UI/LLM layers.
- Canonical event-log columns: `case:concept:name`, `concept:name`, `time:timestamp`.
- Downstream code consumes **`ProcessFacts` only**, never the raw log.
- New behaviour ⇒ new test. Times are seconds in facts; format at the edge.
- Never commit client event logs or the BABOK PDF (see `.gitignore`).
