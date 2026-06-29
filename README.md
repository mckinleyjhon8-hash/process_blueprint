# Process Blueprint

**Internal** process-mining & consulting-intelligence tool. We ingest an SME client's
event log, automatically mine the as-is process, quantify performance and conformance,
and (later phases) generate a client-ready improvement brief.

> Internal use only. Clients receive **outputs** (reports, recommendations) — never access
> to this tool. See [`CLAUDE.md`](CLAUDE.md) for the full goal, architecture, and plan.

## Status
- **Phase 1 — mining engine → `ProcessFacts`: ✅ done & tested** (11 passing tests).
- Next: Supabase persistence (Phase 1.5), then the LangChain brief layer (Phase 2).
- Live progress: [`docs/TRACKING.md`](docs/TRACKING.md).

## Quick start
```bash
pip install -r requirements.txt
pytest -q                      # all tests should pass
python scripts/run_phase1.py   # demo on a generated sample Procure-to-Pay log
```

Run on your own event log:
```bash
python scripts/run_phase1.py path/to/log.csv --process-type "Order-to-Cash" --json facts.json
```

## What Phase 1 produces
A typed, JSON-serialisable `ProcessFacts`: case/event/variant counts, cycle times,
start/end activities, a discovered model with **real conformance metrics**
(fitness, precision, generalization, simplicity), ranked bottlenecks, and rework.
This is the contract every later layer consumes.

## Architecture & docs
- [`CLAUDE.md`](CLAUDE.md) — goal, architecture, knowledge, phases, conventions.
- [`docs/PHASES.md`](docs/PHASES.md) — detailed phase plan.
- [`docs/METHODOLOGY_MAP.md`](docs/METHODOLOGY_MAP.md) — BABOK-aligned deliverable mapping.
- [`HANDOFF.md`](HANDOFF.md) — current session handoff.

## Licensing note
Uses pm4py (AGPL-3.0) strictly as an **internal batch engine**; report outputs are not
derivative works. Do not expose the engine to external users. The BABOK PDF is IIBA
copyrighted and is **not** committed or redistributed.
