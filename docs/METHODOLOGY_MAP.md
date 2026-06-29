# Methodology Map (BABOK-aligned, copyright-safe)

This maps each engine output to the recognised business-analysis technique it
supports and the deliverable section it feeds. It is written **in our own words** —
it references BABOK *technique names and structure* (not copyrightable) and contains
**no text reproduced** from the BABOK guide. This is a prompt/template asset for the
Phase-2 LLM layer, never RAG content.

> BABOK technique numbers (v3, Ch.10) are cited for traceability only.

## Finding → technique → deliverable section

| `ProcessFacts` field | BA technique (BABOK ref) | Knowledge-area lens | Deliverable section |
|---|---|---|---|
| discovered model + `model.fitness/precision` | Process Modelling (10.35), Process Analysis (10.34) | Strategy Analysis → Analyze Current State | **Current State** |
| `n_variants`, `top_variants` | Process Analysis (10.34) | Strategy → Current State | **Current State / Variability** |
| `avg/median_cycle_time`, `activity_frequencies` | Metrics & KPIs; Benchmarking (10.4) | Solution Evaluation → Measure Performance | **Performance Analysis** |
| `bottlenecks` | Root Cause Analysis (10.40) | Solution Evaluation → Assess Limitations | **Root Causes** |
| `rework_activities` | Root Cause Analysis (10.40) | Solution Evaluation | **Root Causes / Waste** |
| benchmark gap (Phase 3) | Benchmarking & Market Analysis (10.4) | Strategy Analysis | **Benchmark Comparison** |
| LLM future-state synthesis | Business Cases (10.7); SWOT (10.46) | Strategy → Define Future State / Change Strategy | **Future State + Change Strategy** |
| prioritised actions | Prioritisation (10.33); Decision Analysis (10.18) | Req. Lifecycle → Prioritise | **Recommendations + Business Case** |
| risk flags | Risk Analysis & Management (10.38) | Strategy → Assess Risks | **Risk Indicators** |

## Deliverable skeleton (the LLM target)
1. **Executive Summary**
2. **Current State** — objective as-is from mining (model, variants, conformance)
3. **Performance Analysis** — KPIs vs. benchmarks
4. **Root Causes** — bottlenecks, rework, deviations
5. **Future State & Change Strategy**
6. **Recommendations + Business Case** — prioritised, with indicative ROI
7. **Risk Indicators**

## Two render targets
- **Internal view** — keeps mechanics: algorithm, fitness/precision, place/transition counts.
- **Client-safe view** — results only. Strips every reference to pm4py, conformance scores,
  and internal tooling. Findings stated in business language and impact (time/€), not method.

## Gaps the map cannot fill (need humans / Phase 3 form)
- **Elicitation & Collaboration** — the *why* behind a deviation (often a valid workaround).
- **BA Planning & Monitoring** — scoping which process and which data to analyse.
Capture these via the per-engagement stakeholder-input form and feed them into the prompt.
