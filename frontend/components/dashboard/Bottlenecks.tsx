import { ArrowRight, AlertTriangle } from "lucide-react";
import type { Bottleneck } from "@/lib/types";

export function Bottlenecks({ items }: { items: Bottleneck[] }) {
  const max = Math.max(...items.map((b) => b.mean_wait_seconds), 1);
  return (
    <div className="space-y-3">
      {items.map((b, i) => {
        const hours = b.mean_wait_seconds / 3600;
        const w = Math.round((b.mean_wait_seconds / max) * 100);
        return (
          <div key={i} className="rounded-xl border border-line bg-panel-2/50 p-3">
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-2 text-[13px] font-semibold text-fg">
                {i === 0 && <AlertTriangle size={14} className="shrink-0 text-warning" />}
                <span className="truncate">{b.source}</span>
                <ArrowRight size={13} className="shrink-0 text-muted" />
                <span className="truncate">{b.target}</span>
              </div>
              <div className="shrink-0 font-mono text-[13px] font-bold text-warning">
                {hours.toFixed(0)}h
              </div>
            </div>
            <div className="mt-2 flex items-center gap-3">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-line">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-warning-vivid to-danger"
                  style={{ width: `${w}%` }}
                />
              </div>
              <span className="shrink-0 text-[11px] text-muted">{b.occurrences}×</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
