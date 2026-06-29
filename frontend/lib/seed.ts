import type { ProcessFacts } from "./types";

// Real output from the Phase-1 engine on the synthetic Procure-to-Pay log,
// so the dashboard renders fully populated without the backend running.
export const SEED_FACTS: ProcessFacts = {
  process_type: "Procure-to-Pay",
  source_file: "sample_p2p.csv",
  n_events: 356,
  n_cases: 60,
  n_activities: 6,
  n_variants: 3,
  avg_cycle_time_seconds: 215340,
  median_cycle_time_seconds: 201600,
  start_activities: { "Create PO": 60 },
  end_activities: { "Pay Invoice": 60 },
  activity_frequencies: {
    "Create PO": 60,
    "Approve PO": 67,
    "Receive Goods": 51,
    "Receive Invoice": 60,
    "Match Invoice": 60,
    "Pay Invoice": 58,
  },
  model: {
    algorithm: "inductive",
    fitness: 1.0,
    fitness_alignments: 1.0,
    precision: 0.9714,
    generalization: 0.8233,
    simplicity: 0.8947,
  },
  bottlenecks: [
    { source: "Approve PO", target: "Receive Invoice", mean_wait_seconds: 190472, occurrences: 11 },
    { source: "Approve PO", target: "Receive Goods", mean_wait_seconds: 167040, occurrences: 49 },
    { source: "Approve PO", target: "Approve PO", mean_wait_seconds: 158400, occurrences: 7 },
  ],
  top_variants: [
    { sequence: ["Create PO", "Approve PO", "Receive Goods", "Receive Invoice", "Match Invoice", "Pay Invoice"], frequency: 45 },
    { sequence: ["Create PO", "Approve PO", "Receive Invoice", "Match Invoice", "Pay Invoice"], frequency: 8 },
    { sequence: ["Create PO", "Approve PO", "Approve PO", "Receive Goods", "Receive Invoice", "Match Invoice", "Pay Invoice"], frequency: 7 },
  ],
  rework_activities: { "Approve PO": 7 },
  schema_version: "1.0",
  generated_at: "2026-06-29T00:00:00Z",
  notifications: [],
};

// Health score = 95 / A (computed from the conformance metrics above).
export const SEED_HEALTH = { score: 95, grade: "A", label: "Excellent" };

export const SEED_BRIEF_CLIENT = `# Executive Brief — Procure-to-Pay

## 1. Executive summary
We reviewed 60 purchase-order cases end to end. The process is well-structured and follows a consistent path, but a single stage — invoice and goods handling immediately after PO approval — adds roughly two days of delay per case and is the clear priority for improvement.

## 2. Current state
Orders follow three distinct paths. The large majority (75%) run the standard route; a smaller share skip goods receipt or loop back for a second approval.

## 3. Performance analysis
Average end-to-end time is ~2.5 days against an industry target of 5–7 days — strong overall — but the wait straight after approval averages ~53 hours, far above the rest of the flow.

## 4. Root causes
A second approval is triggered on ~12% of orders, and goods/invoice receipt frequently stalls right after approval, pointing to a hand-off and ownership gap at that step.

## 5. Future state & change strategy
Introduce tiered approval thresholds so low-value POs are auto-approved, and assign clear ownership for post-approval receipt.

## 6. Recommendations & business case
Targeting the post-approval delay could remove ~1 day per case; at current volume that is a material throughput and working-capital gain.

## 7. Risk indicators
Re-approval loops and skipped goods-receipt steps are control risks worth monitoring.`;
