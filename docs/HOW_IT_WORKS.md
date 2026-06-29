# How it works — a plain-English guide

This explains the whole tool end to end: what process mining is, exactly which
parts of **pm4py** we use (and the much larger part we don't), how the data flows
from a raw event log all the way to the Claude-written report, how comprehensive
it is, what kinds of processes it works on, and what our sample log contains.

---

## 1. The one-paragraph idea

Most consulting "as-is" process maps are drawn from interviews — slow, subjective,
and based on what people *think* happens. **Process mining** flips that: it reads
the digital footprints a process already leaves behind (an *event log*) and
reconstructs what *actually* happened — objectively, completely, from real data.
Our tool does that mining with **pm4py**, turns the result into a clean fact
sheet, and then has **Claude** (via LangChain) write a consultant-quality brief
grounded in those facts plus industry benchmarks.

---

## 2. What an "event log" is

Everything starts from a table where **each row is one thing that happened**.
Three columns are mandatory (pm4py's standard names):

| Column | Meaning | Example |
|---|---|---|
| `case:concept:name` | which *case* (the thing flowing through the process) | `PO-100042` |
| `concept:name` | the *activity* that happened | `Approve Purchase Order` |
| `time:timestamp` | *when* it happened | `2026-01-08 14:05` |
| `org:resource` (optional) | *who/what* did it | `AP Clerk` |

A "case" is one run of the process (one purchase order, one support ticket, one
patient visit). A "variant" is a distinct *path* through the process — the exact
sequence of activities a case went through.

---

## 3. The pipeline, stage by stage

```
Event log (CSV/XES)
   │  ① INGEST          pm4py.format_dataframe / read_xes
   ▼
Clean, standard table
   │  ② DISCOVER        pm4py.discover_petri_net_inductive (+ heuristics)
   ▼
A process model (Petri net)
   │  ③ CONFORM         pm4py.fitness_token_based_replay / precision / alignments
   ▼
Quality scores (fitness, precision, …)
   │  ④ DIAGNOSE        our own pandas code (KPIs, bottlenecks, variants, rework)
   ▼
ProcessFacts  ← the single typed fact sheet (JSON)
   │  ⑤ PERSIST         saved to Supabase (clients→engagements→runs→facts)
   │  ⑥ GROUND          retrieve benchmarks from Supabase pgvector (OpenAI embeddings)
   ▼
   │  ⑦ WRITE           LangChain → Claude (claude-opus-4-8) → Markdown brief
   ▼
Executive report (internal + client-safe views) → shown in the Next.js portal
```

### ① Ingest — *make the data usable*
We read the CSV/XES and hand it to `pm4py.format_dataframe`, which standardises
the column names, parses timestamps, drops broken rows, and sorts events within
each case. (Code: `src/process_blueprint/ingest.py`.)

### ② Discover — *draw the real map*
`pm4py.discover_petri_net_inductive` reads every case and builds a **Petri net** —
a formal flowchart that captures the sequences, choices, parallels and loops the
data actually contains. We default to the **Inductive Miner** because it always
produces a sound, replayable model; **Heuristics Miner** is available for very
noisy logs. (Code: `discovery.py`.)

### ③ Conform — *how trustworthy is that map?*
A discovered model is only useful if we know how well it matches reality. pm4py
gives us four quality numbers (all 0–1):

- **Fitness** (`fitness_token_based_replay` / `fitness_alignments`) — how much of
  the real behaviour the model can reproduce. 1.0 = it explains everything.
- **Precision** (`precision_token_based_replay`) — does the model *only* allow
  what really happens, or is it too loose?
- **Generalization** & **Simplicity** — does it generalise sensibly, and is it
  clean rather than spaghetti?

These four feed our **Process Health Score** (a weighted 0–100). This is the
metric the old prototype always reported as "F" because it never actually
computed these numbers — now it does. (Code: `conformance.py`, `brief/scoring.py`.)

### ④ Diagnose — *the business numbers*
Here we use **plain pandas, not pm4py**, on purpose — the numbers are simple,
deterministic, and easy to explain to a client:

- **KPIs**: case count, event count, distinct activities, average & median cycle time.
- **Bottlenecks**: for every hand-off (activity → next activity) we measure the
  average wait, and flag the slow ones (above mean + 1σ).
- **Variants**: the distinct end-to-end paths and how common each is.
- **Rework**: activities that repeat inside a case (re-approvals, re-work loops).

(Code: `performance.py`.)

### The handoff object: `ProcessFacts`
Stages ②–④ are packed into one typed object — `ProcessFacts` — serialised to JSON.
**Nothing downstream ever touches the raw log or pm4py again**; every later layer
(database, LLM, dashboard) reads only this fact sheet. This keeps pm4py (which is
AGPL-licensed) isolated in the engine, and keeps the rest of the system clean.
(Code: `facts.py`.)

### ⑤ Persist
The FastAPI backend writes the facts to Supabase: a `clients → engagements →
event_log_runs → process_facts` chain, so every analysis is recorded.

### ⑥ Ground in benchmarks
Before writing the report, we fetch relevant **industry benchmarks** for the
process type from Supabase using **pgvector** semantic search (OpenAI embeddings).
That's how the brief can say "≈40 days vs a 5–7 day target" instead of just
reporting raw numbers. (Code: `knowledge/`.)

### ⑦ Write the report
LangChain assembles a prompt: the `ProcessFacts` digest + the retrieved benchmark
evidence + a **BABOK-shaped skeleton** (Current State → Performance → Root Causes →
Future State → Recommendations → Risks). **Claude (`claude-opus-4-8`)** writes the
brief. Two versions come out of the same facts:

- **Internal** — keeps the mechanics (fitness, precision, algorithm names).
- **Client-safe** — business language only; the engine/method words are *removed
  from the model's input* and a guard double-checks the output for leaks.

(Code: `brief/`.)

---

## 4. Are we using "all of pm4py"? — No, and that's deliberate

pm4py (v2.7.23) is **huge** — its public API spans ~20 discovery algorithms,
many conformance methods, object-centric mining, organisational/social-network
mining, machine-learning feature extraction, simulation, privacy, its own LLM
connectors, and database connectors (SAP, Camunda, Outlook…). We use a **small,
high-signal slice**:

| pm4py area | Functions we call | Use it? |
|---|---|---|
| Read / format | `read_xes`, `convert_to_dataframe`, `format_dataframe` | ✅ |
| Discovery | `discover_petri_net_inductive`, `discover_petri_net_heuristics` | ✅ |
| Conformance | `fitness_token_based_replay`, `fitness_alignments`, `precision_token_based_replay`, generalization, simplicity | ✅ |
| Stats / performance | *(we compute KPIs, variants, rework, bottlenecks in pandas instead)* | ➖ own code |
| Visual (`save_vis_petri_net`, dotted chart, performance spectrum) | — | ⬜ not yet (needs Graphviz) |
| Object-centric (OCEL) | — | ⬜ future |
| Organisational / social-network mining | — | ⬜ future |
| ML / prediction (`extract_features_dataframe`, next-activity, remaining-time) | — | ⬜ future |
| Simulation / playout | — | ⬜ (used only to generate test logs) |
| pm4py's own LLM module (`pm4py.llm.*`) | — | ➖ we use our own LangChain layer instead |

**Why we built our own LLM layer instead of `pm4py.llm`:** pm4py ships an LLM
module (`openai_query`, `anthropic_query`, `abstract_dfg`, `nlp_to_log_query`),
but it's OpenAI/Anthropic-call-it-yourself. Our LangChain layer adds what a
consulting product needs: **pluggable providers** (Claude/OpenAI/OpenRouter),
**benchmark grounding** via our own knowledge base, the **internal vs client-safe**
split, and a **redaction guard**. So pm4py does the *mining*; we own the *narrative*.

### What we could switch on next (all already in pm4py)
- **Real process-map image** in the portal's "Process map" panel → `save_vis_petri_net` (needs Graphviz).
- **Dotted chart / performance spectrum** → richer time visuals.
- **Organisational mining** (`discover_handover_of_work_network`, roles) → "who hands off to whom" — we already capture `org:resource`.
- **Predictive monitoring** (`extract_features_dataframe` + a model) → next-activity / remaining-time forecasts.
- **Object-centric (OCEL)** → processes with many interacting objects (orders + items + deliveries).

---

## 5. What kinds of process can it analyse?

**Any process that leaves a timestamped trail** with a case id, an activity, and a
time. No industry assumptions are baked in. Common examples:

- **Finance / operations:** Procure-to-Pay, Order-to-Cash, Invoice Processing, Accounts Payable.
- **Service / IT:** customer support tickets, IT incident & change management, SLA workflows.
- **HR:** employee onboarding, recruitment.
- **Healthcare:** patient pathways, diagnostics, claims.
- **Lending / insurance:** loan origination, underwriting, claims handling.
- **Manufacturing / logistics:** production routing, fulfilment, returns.

The data can come from a CSV/XES export, or (via pm4py's connectors) directly from
SAP, Camunda, or other systems. For multi-object processes, pm4py's object-centric
(OCEL) support is there when we need it.

---

## 6. What our sample consists of

Because real client logs are confidential, we ship a **synthetic but realistic
enterprise Procure-to-Pay generator** (`tests/enterprise_log.py`) so the whole
pipeline can be exercised and demonstrated. It is deliberately *messy*, like real
data, not a clean toy. It contains:

- **~17 activities** across the full P2P lifecycle: Create Purchase Requisition →
  Approve Requisition → Create PO → Approve PO → Send PO to Supplier → Receive
  Order Confirmation → Receive Goods → Inspect Goods → Receive Invoice → Match
  Invoice → Approve Payment → Pay Invoice.
- **Realistic complications**, each firing on a share of cases:
  - requisition **rejections** (~7%), some resubmitted,
  - **tiered PO approval** (high-value POs get a second, senior approval ~12%),
  - **PO cancellations** (~5%),
  - **supplier clarification** loops (~28%),
  - failed inspections → **goods returned and re-received** (~16%),
  - **invoice exceptions** → resolve → re-match, sometimes escalated (~24%).
- **Named resources** (Requester, Buyer, Manager, Senior Manager, Warehouse,
  Quality, AP Clerk, AP Manager) in `org:resource`.
- **Business-hours timing** — events only advance Mon–Fri 09:00–17:00, so cycle
  times look like real working days, not raw clock time.

This produces dozens of variants, genuine bottlenecks, and real rework — exactly
what stresses the engine. Verified runs:

| Run | Cases | Events | Activities | Variants | Health | Top bottleneck |
|---|---|---|---|---|---|---|
| Sample (one click) | 400 | ~5,200 | 17 | ~28 | 92 / A | Order confirmation → goods (~14 days) |
| Full enterprise | 3,000 | 38,199 | 17 | 42 | ~93 / A | Order confirmation → goods (~14 days) |

Generate your own size with `python scripts/generate_enterprise_log.py --cases 5000`.

---

## 7. In one sentence

**Raw event log → pm4py mines the real process and scores how trustworthy that
model is → we distil it into one fact sheet → Claude turns the facts (plus
benchmarks) into a board-ready, client-safe report** — objective, repeatable, and
fast, with the heavy process-mining maths done by a deliberately small, well-
understood slice of pm4py.
