// Mirrors src/process_blueprint/facts.py ProcessFacts (schema_version 1.0).

export interface ModelQuality {
  algorithm: string;
  fitness: number | null;
  fitness_alignments: number | null;
  precision: number | null;
  generalization: number | null;
  simplicity: number | null;
}

export interface Bottleneck {
  source: string;
  target: string;
  mean_wait_seconds: number;
  occurrences: number;
}

export interface Variant {
  sequence: string[];
  frequency: number;
}

export interface ComplianceRule {
  violations: number;
  pct_of_cases: number;
  example_cases: string[];
}

export interface ComplianceReport {
  n_cases: number;
  rules: Record<string, ComplianceRule>;
}

// --- v1.1 insight layers -------------------------------------------------
export interface FlowEdge {
  source: string;
  target: string;
  frequency: number;
  mean_wait_seconds: number;
  median_wait_seconds: number;
  stdev_wait_seconds: number;
}

export interface TimeProfile {
  p10_seconds: number;
  p50_seconds: number;
  p90_seconds: number;
  heavy_tail_ratio: number | null;
  top_variant_coverage_pct: number;
  top5_coverage_pct: number;
  exception_rate_pct: number;
  rework_case_rate_pct: number;
  fpy_pct: number;
}

export interface BenchmarkPosition {
  metric: string;
  value: number;
  provenance: string;
  plausibility: "pass" | "warning" | "fail";
  plausibility_note: string | null;
  unit?: string;
  direction?: "lower" | "higher";
  p25?: number;
  median?: number;
  p75?: number;
  top_quartile?: number;
  quartile?: "Q1" | "Q2" | "Q3" | "Q4";
  target_value?: number | null;
  gap_pct?: number | null;
  source?: string;
  grade?: string;
}

export interface DiscoveryItem {
  id: string;
  label: string;
  points: number;
  critical: boolean;
  question: string;
  granted: boolean;
  status: "auto" | "manual" | "missing";
}

export interface DiscoveryDomain {
  label: string;
  score: number;
  level: "below_must" | "must" | "should" | "complete";
  must: number;
  should: number;
  complete: number;
  items: DiscoveryItem[];
}

export interface DiscoveryReport {
  domains: Record<string, DiscoveryDomain>;
  overall: number;
  all_musts_met: boolean;
  roi_gate: "pass" | "caveated" | "blocked";
  roi_gate_note: string;
  top_gaps: { domain: string; item: string; question: string }[];
  answers?: Record<string, boolean>;
}

export interface ProcessFacts {
  process_type: string;
  source_file: string;
  compliance?: ComplianceReport;
  flow?: { n_edges: number; edges: FlowEdge[] };
  time_profile?: Partial<TimeProfile>;
  resources?: {
    n_resources: number;
    roles: { resource: string; n_events: number; top_activities: string[] }[];
    handovers: { source: string; target: string; count: number }[];
    single_points_of_failure: string[];
  };
  batching?: { activity: string; resource: string; batch_type: string; n_batches: number }[];
  benchmarks?: {
    family: string;
    family_label: string;
    baseline: string;
    principle: string;
    positions: BenchmarkPosition[];
  };
  provenance?: Record<string, string>;
  discovery?: DiscoveryReport;
  n_events: number;
  n_cases: number;
  n_activities: number;
  n_variants: number;
  avg_cycle_time_seconds: number;
  median_cycle_time_seconds: number;
  start_activities: Record<string, number>;
  end_activities: Record<string, number>;
  activity_frequencies: Record<string, number>;
  model: ModelQuality;
  bottlenecks: Bottleneck[];
  top_variants: Variant[];
  rework_activities: Record<string, number>;
  schema_version: string;
  generated_at: string;
  notifications: string[];
  run_id?: string;
}

export interface BriefResult {
  audience: "internal" | "client";
  markdown: string;
  health_score: number | null;
  grade: string;
  model_name: string;
  redaction_warnings: string[];
}
