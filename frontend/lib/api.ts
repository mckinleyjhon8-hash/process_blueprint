import type { ProcessFacts, BriefResult } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function detail(r: Response): Promise<string> {
  try {
    const j = await r.json();
    return j.detail || r.statusText;
  } catch {
    return r.statusText;
  }
}

export async function analyzeLog(
  file: File,
  processType: string,
  algorithm = "inductive",
): Promise<ProcessFacts> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("process_type", processType);
  fd.append("algorithm", algorithm);
  const r = await fetch(`${BASE}/api/analyze`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(await detail(r));
  return r.json();
}

export async function analyzeSample(cases = 400, process = "Procure-to-Pay"): Promise<ProcessFacts> {
  const q = `cases=${cases}&process=${encodeURIComponent(process)}`;
  const r = await fetch(`${BASE}/api/analyze-sample?${q}`, { method: "POST" });
  if (!r.ok) throw new Error(await detail(r));
  return r.json();
}

export async function getBrief(
  runId: string,
  audience: "internal" | "client",
  provider?: string,
  model?: string,
): Promise<BriefResult> {
  const r = await fetch(`${BASE}/api/brief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      run_id: runId,
      audience,
      provider: provider || undefined,
      model: model || undefined,
    }),
  });
  if (!r.ok) throw new Error(await detail(r));
  return r.json();
}

// --- admin / listing endpoints ---
export interface ProviderInfo {
  key_present: boolean;
  default_model: string;
  models: string[];
}
export interface AppConfig {
  llm: { default_provider: string; providers: Record<string, ProviderInfo> };
  embeddings: { provider: string; key_present: boolean };
  supabase: { configured: boolean };
  render?: { graphviz: boolean };
}

export interface RunSummary {
  run_id: string | null;
  process_type: string | null;
  n_cases: number | null;
  n_variants: number | null;
  model_fitness: number | null;
  model_precision: number | null;
  created_at: string | null;
}

export interface Engagement {
  id?: string;
  name: string;
  client_name?: string | null;
  process_type?: string | null;
  status?: string | null;
  runs?: number;
}

export interface KnowledgeChunk {
  title: string;
  source: string;
}

async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(await detail(r));
  return r.json();
}

export const getConfig = () => getJSON<AppConfig>("/api/config");
export const getEngagements = () =>
  getJSON<{ source: string; engagements: Engagement[] }>("/api/engagements");
export const getRuns = () => getJSON<{ source: string; runs: RunSummary[] }>("/api/runs");
export const getRun = (runId: string) =>
  getJSON<ProcessFacts & { has_map?: boolean }>(`/api/run/${runId}`);
export const getKnowledge = () =>
  getJSON<{
    configured: boolean;
    total: number;
    by_source: Record<string, number>;
    chunks: KnowledgeChunk[];
  }>("/api/knowledge");

export function reportUrl(runId: string, audience: "internal" | "client", download = false): string {
  const q = `audience=${audience}${download ? "&download=1" : ""}`;
  return `${BASE}/api/report/${runId}?${q}`;
}

export function processMapUrl(runId: string): string {
  return `${BASE}/api/process-map/${runId}`;
}

export async function apiHealth(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/api/health`, { cache: "no-store" });
    return r.ok;
  } catch {
    return false;
  }
}
