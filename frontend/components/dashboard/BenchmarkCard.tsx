import { TriangleAlert } from "lucide-react";
import type { BenchmarkPosition, ProcessFacts } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

const Q_TONE = { Q1: "danger", Q2: "warning", Q3: "info", Q4: "success" } as const;
const METRIC_LABEL: Record<string, string> = {
  lead_time_days: "Lead time",
  fpy_pct: "First-pass yield",
  rework_rate_pct: "Rework rate",
  exception_rate_pct: "Exception rate (outside top-5 paths)",
  heavy_tail_ratio: "Heavy-tail ratio (P90 ÷ P50)",
};

function fmtVal(p: BenchmarkPosition) {
  return `${p.value}${p.unit === "%" ? "%" : p.unit ? ` ${p.unit}` : "×"}`;
}

/** Quartile positioning vs the peer group — benchmark as evidence, not truth. */
export function BenchmarkCard({ facts }: { facts: ProcessFacts }) {
  const b = facts.benchmarks;
  if (!b?.positions?.length) return null;

  return (
    <Card
      title="Benchmark position"
      subtitle={`${b.family_label} · ${b.baseline} · measured (E1) vs peer quartiles`}
      action={
        (b.framework?.apqc_pcf_v8 || b.framework?.scor_v14) ? (
          <span className="flex flex-wrap justify-end gap-1">
            {b.framework.apqc_pcf_v8 && (
              <Badge tone="violet" className="font-mono">APQC v8 · {b.framework.apqc_pcf_v8.split(" ")[0]}</Badge>
            )}
            {b.framework.scor_v14 && (
              <Badge tone="info" className="font-mono">SCOR v14 · {b.framework.scor_v14.split(" ")[0]}</Badge>
            )}
          </span>
        ) : undefined
      }
    >
      <ul className="divide-y divide-line-soft">
        {b.positions.map((p) => (
          <li key={p.metric} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2.5">
            <span className="min-w-[180px] text-sm font-medium text-fg">
              {METRIC_LABEL[p.metric] ?? p.metric}
            </span>
            <span className="font-mono text-sm font-bold text-fg">{fmtVal(p)}</span>
            {p.quartile ? (
              <Badge tone={Q_TONE[p.quartile]}>{p.quartile}</Badge>
            ) : (
              <Badge tone="neutral">no peer range</Badge>
            )}
            {p.plausibility !== "pass" && (
              <span
                className={`flex items-center gap-1 text-2xs font-semibold ${p.plausibility === "fail" ? "text-danger" : "text-warning"}`}
                title={p.plausibility_note ?? undefined}
              >
                <TriangleAlert size={11} /> {p.plausibility_note}
              </span>
            )}
            <span className="ml-auto text-right">
              {p.quartile && p.target_value != null && (
                <span className="block text-2xs text-fg-2">
                  next target <span className="font-mono font-semibold">{p.target_value}{p.unit === "%" ? "%" : ""}</span>
                  {p.gap_pct != null && <span className="text-muted"> ({p.gap_pct}% gap)</span>}
                </span>
              )}
              {p.quartile === "Q4" && (
                <span className="block text-2xs text-success">top quartile — hold</span>
              )}
              {p.source && (
                <span className="block text-2xs text-muted/70">
                  {p.median != null && `peer median ${p.median}${p.unit === "%" ? "%" : ""} · `}
                  {p.source} · grade {p.grade}
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-2xs italic text-muted">{b.principle}.</p>
    </Card>
  );
}
