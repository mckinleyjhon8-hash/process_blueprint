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

export interface ProcessFacts {
  process_type: string;
  source_file: string;
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
