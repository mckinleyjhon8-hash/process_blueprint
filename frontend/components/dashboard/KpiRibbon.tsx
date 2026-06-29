import { Layers, Activity, GitBranch, Clock, ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { ProcessFacts } from "@/lib/types";

function fmtHours(seconds: number): string {
  const h = seconds / 3600;
  if (h >= 24) return `${(h / 24).toFixed(1)}d`;
  return `${h.toFixed(1)}h`;
}

export function KpiRibbon({ facts }: { facts: ProcessFacts }) {
  const cards = [
    { icon: Layers, label: "Cases analysed", value: facts.n_cases.toLocaleString(), delta: "+100% coverage", up: true },
    { icon: Activity, label: "Events processed", value: facts.n_events.toLocaleString(), delta: "objective data", up: true },
    { icon: GitBranch, label: "Process variants", value: String(facts.n_variants), delta: "low complexity", up: true },
    { icon: Clock, label: "Avg cycle time", value: fmtHours(facts.avg_cycle_time_seconds), delta: "vs 5–7d target", up: false },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
      {cards.map(({ icon: Icon, label, value, delta, up }) => (
        <div
          key={label}
          className="rise rounded-2xl border border-line bg-panel/70 p-4"
        >
          <div className="flex items-center justify-between">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/12 text-primary">
              <Icon size={17} />
            </span>
            <span
              className={
                "flex items-center gap-1 text-[11px] font-semibold " +
                (up ? "text-success" : "text-info")
              }
            >
              {up ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
              {delta}
            </span>
          </div>
          <div className="mt-3 font-mono text-[26px] font-bold leading-none text-fg">
            {value}
          </div>
          <div className="mt-1.5 text-[12px] font-medium text-muted">{label}</div>
        </div>
      ))}
    </div>
  );
}
