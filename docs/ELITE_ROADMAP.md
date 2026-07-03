# Elite Roadmap — One-Stop Process-Intelligence Consultancy Tool

> Goal: an **internal-only** tool (never multi-tenant, clients never access it) that lets
> anyone with basic training run a complete, partner-grade process-consulting engagement
> end to end: Discover → Analyze → (Re)Design → Recommend → Deliver — with the playbook
> methodology enforced by the tool, not remembered by the consultant.
>
> Sources: the playbooks + knowledge base + Consultant OS, now consolidated in
> `C:\Users\musta\Desktop\pure_research` (2026-07-02 additions: **apqc_scor_framework_reference**
> — verified PCF v8.0 + SCOR v14.0; **roi_investment_research_reference** — empirically
> calibrated ROI defaults; **compliance_privacy_regulatory_landscape** — current-status ADM
> law per jurisdiction; **concepts/** — the 10-screen "Meridian" product design),
> pm4py 2.7.23 full API, our existing engine/portal.

## 0. Research-driven corrections (2026-07-03 review)

1. **ROI calibration (feeds E4):** use the research reference's conservative defaults, not
   the playbook's — realisation RPA 40/70/90% (Y1/Y2/Y3), AI 25/55/80%; TCO contingency
   15% RPA / 25–30% AI; STP ceilings AP 75% · onboarding 60% · RPA 80% · LLM 75% (never
   100%); UK loaded-FTE ×1.30 (2025/26 NI); failure haircut ~30% under-delivery; manual AP
   error baseline 1.5% → post-automation 0.3–0.5% (never zero).
2. **Framework tagging (quick win):** tag each process with verified PCF v8.0 + SCOR v14.0
   codes (AP→9.5, AR→9.2.3, Payroll→7.5.4 under HR now, PO→4.2.4/S1, Fulfilment→4.4.3/F1…);
   fix our benchmark labels citing "SCOR DS 2.0" → SCOR v14.0, APQC v7 → v8.0.
3. **Compliance freshness discipline (E3/E7):** ADM provisions are jurisdiction-specific and
   fast-moving (EU AI Act high-risk obligations ~Aug 2026; UK DUAA 2025 recasts Art 22).
   Compliance gates must carry `[verify against regulator]` notes + research-date stamps;
   re-verify quarterly. Landscape reference = the gate seed data.
4. **Meridian concept adoption (shapes E5+):** engagement-centric IA (Company Profile →
   Engagement → in-scope Processes with stage badges) over run-centric; Evidence Hub +
   Interview Notes = the elicitation-capture layer feeding discovery completeness; Process
   Workspace = AS-IS/TO-BE VSM strip + per-step dispositions. Keep OUR design system
   (Monday-class light) — adopt Meridian's structures, not its skin.
   ⚠️ Concepts grade evidence E1–E5 **inverted** vs the playbooks (E5=benchmarked best);
   our implementation keeps playbook semantics (E1 = measured = best). Do not copy the UI scale.

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
