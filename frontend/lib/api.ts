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
): Promise<BriefResult> {
  const r = await fetch(`${BASE}/api/brief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: runId, audience, provider }),
  });
  if (!r.ok) throw new Error(await detail(r));
  return r.json();
}

export async function apiHealth(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/api/health`, { cache: "no-store" });
    return r.ok;
  } catch {
    return false;
  }
}
