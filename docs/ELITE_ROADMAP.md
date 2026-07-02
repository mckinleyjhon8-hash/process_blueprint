# Elite Roadmap — One-Stop Process-Intelligence Consultancy Tool

> Goal: an **internal-only** tool (never multi-tenant, clients never access it) that lets
> anyone with basic training run a complete, partner-grade process-consulting engagement
> end to end: Discover → Analyze → (Re)Design → Recommend → Deliver — with the playbook
> methodology enforced by the tool, not remembered by the consultant.
>
> Sources: the five playbooks + knowledge base + Consultant OS (`drive-download-20260702…`),
> pm4py 2.7.23 full API, our existing engine/portal.

---

## 1. Gap analysis — where we are vs where we need to be

| Capability | Today | Target (playbook) | Gap |
|---|---|---|---|
| Evidence ingest | CSV/XES → pm4py → ProcessFacts (E1) | Same + provenance tags on every metric, plausibility-checked | E1 labelling + plausibility engine |
| Process map | Petri net + variants + bottlenecks | + performance DFG (freq+wait per edge), PCE, percentiles, heavy tail | pm4py activation (dormant) |
| People dimension | **none** (org:resource ignored) | roles, hand-overs, SPOF, four-eyes/SoD | pm4py activation (dormant) |
| Discovery method | upload → auto-facts | triage score, 6-domain completeness w/ Must gates, question banks, ROI gate | Discovery engine + guided UI |
| Benchmarks | 8 text chunks in pgvector | quartile tables (p25/p50/p75/top) × process, positioning, gap sizing, targets | structured benchmark engine |
| Redesign | LLM prose recommendations | H1–H12 heuristic engine: triggers from facts → computed TO-BE deltas, ECRS gates | deterministic redesign engine |
| AI/automation advice | none | rules>ML>LLM>human decision tree, data-readiness gates, HITL patterns | AI-suitability module |
| ROI | LLM-invented numbers | deterministic TCO/NPV/payback, 3 scenarios, double-count register, realisation phasing | ROI engine |
| Compliance | SOP rule engine + BPMN conformance (strong) | + four-eyes/SoD rules, Art-22/HITL flags on recommendations | extend rule kinds |
| Brief quality | LLM + approve gate | Consultant-OS §10 rules (C1–C7), evidence-honest precision, so-what test, Minto | prompt + validation layer |
| Operator UX | run workspace + map studio | guided stage flow with gates; playbook logic as checklists/wizards (per the static HTML) | stage-gated engagement UI |

**Explicit non-goals (avoid at all costs):** multi-tenancy, client portal/auth, regional
Supabase projects, jurisdiction RLS. Internal single-team tool. pm4py stays isolated in
the engine (AGPL posture unchanged).

## 2. Phased program (each phase ships tested + usable)

| Phase | Content | Playbook source |
|---|---|---|
| **E1 Discovery** (now) | pm4py activation (perf DFG, percentiles, resources, batches) → ProcessFacts v1.1 · benchmark quartile engine + plausibility + zero-claims · 6-domain completeness w/ auto-scoring from log + manual checklists · triage score · Discovery tab | Discovery playbook + Benchmark Ref §1–4 |
| **E2 Redesign** | H1–H12 heuristic engine: trigger detection from facts, disposition sequencing (Eliminate→…→Augment_AI hard gate), computed TO-BE deltas w/ cited ranges, happy-path/exception design fields | Redesign playbook + KB §3 |
| **E3 AI & Risk** | AI-vs-rules-vs-human decision tree per opportunity, data-readiness scoring, HITL pattern selection, AI risk EVs (R1–R5) into risk register | AI Decision & Risk playbook |
| **E4 ROI** | Deterministic ROI: cost/benefit taxonomy, TCO, NPV/payback, conservative/base/optimistic, double-count register, realisation phasing, benefit checkpoints | ROI refs in KB §6 + ROI impl spec |
| **E5 Consultant OS layer** | Stage gates (Diagnose→Analyze→Design→Recommend) on engagements, anti-pattern detectors (AP1–AP10), §10 rules C1–C7 into brief prompts + validation, partner-grade finding linter, Minto/SCQA report structure | Consultant OS |
| **E6 Knowledge depth** | Ingest KB + playbooks as structured nodes into pgvector (node_type, cross-refs), pm4py.llm abstractions (abstract_dfg/variants/log_skeleton) as brief grounding, auto-hypotheses | KB + pm4py.llm |
| **E7 Compliance breadth** | Four-eyes/SoD rule kind, Art-22/DPIA trigger flags on AI recommendations, declarative-rule discovery (log skeleton) as SOP rule candidates | Compliance UK + pm4py |

## 3. Definition of "elite" (the 9.9/10 bar)

1. Every number in a deliverable is **measured (E1), benchmarked (E2), or labelled estimated** — never silently invented.
2. Every recommendation is **traceable**: root cause → heuristic → computed delta → ROI scenario → risk EV.
3. Every gate the playbooks define is **enforced by the tool** (can't reach Recommend with a failing gate).
4. A trained-but-junior operator can run an engagement end to end following the tool's guidance alone.
5. The engine runs fully offline of the LLM: mining, benchmarks, redesign math, ROI are deterministic; the LLM writes *around* computed numbers.

## 4. Live status

Tracked per-phase in `docs/TRACKING.md` (Phase E1 section).
