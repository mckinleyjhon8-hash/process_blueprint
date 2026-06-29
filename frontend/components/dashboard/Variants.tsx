import type { Variant } from "@/lib/types";

const COLORS = ["bg-primary", "bg-violet", "bg-info"];

export function Variants({ items, total }: { items: Variant[]; total: number }) {
  return (
    <div className="space-y-3.5">
      {items.map((v, i) => {
        const pct = Math.round((v.frequency / total) * 100);
        return (
          <div key={i}>
            <div className="mb-1.5 flex items-center justify-between">
              <span className="flex items-center gap-2 text-[12px] text-fg-2">
                <span className={`h-2 w-2 rounded-full ${COLORS[i % COLORS.length]}`} />
                Variant {i + 1} · {v.sequence.length} steps
              </span>
              <span className="font-mono text-[12px] font-semibold text-fg">
                {pct}% <span className="text-muted">({v.frequency})</span>
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-line">
              <div className={`h-full rounded-full ${COLORS[i % COLORS.length]}`} style={{ width: `${pct}%` }} />
            </div>
            <p className="mt-1.5 truncate text-[11px] text-muted">{v.sequence.join("  →  ")}</p>
          </div>
        );
      })}
    </div>
  );
}
