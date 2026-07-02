import { Layers, Activity, GitBranch, Clock } from "lucide-react";
import type { ProcessFacts } from "@/lib/types";
import { fmtDuration } from "@/lib/format";

/** Four headline facts for a run — every value is measured, none invented. */
export function KpiRibbon({ facts }: { facts: ProcessFacts }) {
  const cards = [
    {
      icon: Layers,
      label: "Cases analysed",
      value: facts.n_cases.toLocaleString(),
      meta: "complete population, not a sample",
    },
    {
      icon: Activity,
      label: "Events processed",
      value: facts.n_events.toLocaleString(),
      meta: `${facts.n_activities} distinct activities`,
    },
    {
      icon: GitBranch,
      label: "Process variants",
      value: String(facts.n_variants),
      meta: `top path covers ${
        facts.n_cases && facts.top_variants[0]
          ? Math.round((facts.top_variants[0].frequency / facts.n_cases) * 100)
          : 0
      }% of cases`,
    },
    {
      icon: Clock,
      label: "Avg cycle time",
      value: fmtDuration(facts.avg_cycle_time_seconds),
      meta: `median ${fmtDuration(facts.median_cycle_time_seconds)}`,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
      {cards.map(({ icon: Icon, label, value, meta }) => (
        <div key={label} className="rise rounded-2xl border border-line bg-panel p-4 shadow-[var(--elev-1)]">
          <div className="flex items-center justify-between">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/12 text-primary">
              <Icon size={17} />
            </span>
          </div>
          <div className="mt-3 font-mono text-2xl font-bold leading-none text-fg">{value}</div>
          <div className="mt-1.5 text-xs font-medium text-muted">{label}</div>
          <div className="mt-0.5 truncate text-2xs text-muted/70">{meta}</div>
        </div>
      ))}
    </div>
  );
}
