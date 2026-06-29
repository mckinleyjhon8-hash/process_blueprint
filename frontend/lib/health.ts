import type { ModelQuality } from "./types";

// Mirrors brief/scoring.py — weights renormalised over available metrics.
const W = { fitness: 0.4, precision: 0.25, generalization: 0.15, simplicity: 0.2 } as const;

export function computeHealth(m: ModelQuality): {
  score: number | null;
  grade: string;
  label: string;
} {
  let num = 0;
  let den = 0;
  (Object.keys(W) as (keyof typeof W)[]).forEach((k) => {
    const v = m[k];
    if (typeof v === "number") {
      num += Math.min(Math.max(v, 0), 1) * W[k];
      den += W[k];
    }
  });
  if (den === 0) return { score: null, grade: "N/A", label: "insufficient data" };
  const score = Math.round((num / den) * 100);
  const grade = score >= 85 ? "A" : score >= 70 ? "B" : score >= 55 ? "C" : score >= 40 ? "D" : "F";
  const label =
    score >= 85 ? "Excellent" : score >= 70 ? "Good" : score >= 55 ? "Moderate" : score >= 40 ? "Poor" : "Critical";
  return { score, grade, label };
}
