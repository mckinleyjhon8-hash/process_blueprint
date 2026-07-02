"use client";

import { ArrowRight, Search, X } from "lucide-react";
import type { ProcessFacts } from "@/lib/types";
import type { ProcessGraph } from "@/lib/graph";
import { fmtDuration, fmtInt } from "@/lib/format";
import { Badge } from "@/components/ui/Badge";

/** Right-rail inspector for the Map Studio: search, selected-node detail,
    run stats and a legend. Pure presentation — all state lives in the page. */
export function Inspector({
  facts,
  graph,
  selected,
  onSelect,
  query,
  onQuery,
}: {
  facts: ProcessFacts;
  graph: ProcessGraph;
  selected: string | null;
  onSelect: (id: string | null) => void;
  query: string;
  onQuery: (q: string) => void;
}) {
  const node = selected ? graph.nodes.find((n) => n.id === selected) : null;
  const incoming = node ? graph.edges.filter((e) => e.target === node.id && !e.selfLoop) : [];
  const outgoing = node ? graph.edges.filter((e) => e.source === node.id && !e.selfLoop) : [];

  return (
    <aside
      className="flex w-[300px] shrink-0 flex-col gap-4 overflow-y-auto border-l border-line bg-bg-elev/70 p-4 backdrop-blur-xl"
      aria-label="Map inspector"
    >
      {/* search */}
      <div className="relative">
        <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
        <input
          value={query}
          onChange={(e) => onQuery(e.target.value)}
          placeholder="Find activity…"
          aria-label="Find activity"
          className="w-full rounded-xl border border-line bg-panel/60 py-2 pl-9 pr-3 text-sm text-fg placeholder:text-muted focus:border-primary/60"
        />
      </div>

      {node ? (
        /* ---- selected activity detail ---- */
        <section className="rounded-xl border border-line bg-panel/70 p-4">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-bold leading-snug text-fg">{node.label}</h3>
            <button
              onClick={() => onSelect(null)}
              aria-label="Clear selection"
              className="grid h-6 w-6 shrink-0 place-items-center rounded-md text-muted hover:text-fg"
            >
              <X size={13} />
            </button>
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {node.isStart && <Badge tone="success">start</Badge>}
            {node.isEnd && <Badge tone="violet">end</Badge>}
            {node.rework > 0 && <Badge tone="warning">rework ×{node.rework}</Badge>}
          </div>
          <dl className="mt-3 space-y-1.5 text-xs">
            <div className="flex justify-between">
              <dt className="text-muted">Executions</dt>
              <dd className="font-mono font-semibold text-fg">{fmtInt(node.frequency)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">Share of cases</dt>
              <dd className="font-mono font-semibold text-fg">
                {facts.n_cases ? `${Math.round((node.frequency / facts.n_cases) * 100)}%` : "—"}
              </dd>
            </div>
          </dl>

          {[
            { label: "Incoming", list: incoming, dir: "in" as const },
            { label: "Outgoing", list: outgoing, dir: "out" as const },
          ].map(({ label, list, dir }) =>
            list.length ? (
              <div key={label} className="mt-3">
                <div className="mb-1 text-2xs font-bold uppercase tracking-[0.08em] text-muted/80">
                  {label}
                </div>
                <ul className="space-y-1">
                  {list.map((e) => (
                    <li key={e.id}>
                      <button
                        onClick={() => onSelect(dir === "in" ? e.source : e.target)}
                        className="flex w-full items-center gap-1.5 rounded-lg px-2 py-1.5 text-left text-xs text-fg-2 transition-colors hover:bg-panel-2/60 hover:text-fg"
                      >
                        <ArrowRight size={11} className={`shrink-0 ${e.isBottleneck ? "text-warning" : "text-muted"}`} />
                        <span className="truncate">{dir === "in" ? e.source : e.target}</span>
                        {e.waitSeconds != null && (
                          <span className="ml-auto shrink-0 font-mono font-semibold text-warning">
                            {fmtDuration(e.waitSeconds)}
                          </span>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null,
          )}
        </section>
      ) : (
        /* ---- run-level stats when nothing selected ---- */
        <section className="rounded-xl border border-line bg-panel/70 p-4">
          <h3 className="text-sm font-bold text-fg">{facts.process_type}</h3>
          <p className="mt-0.5 text-2xs text-muted">Select an activity for details</p>
          <dl className="mt-3 space-y-1.5 text-xs">
            {[
              ["Cases", fmtInt(facts.n_cases)],
              ["Events", fmtInt(facts.n_events)],
              ["Activities", fmtInt(facts.n_activities)],
              ["Variants", fmtInt(facts.n_variants)],
              ["Avg cycle", fmtDuration(facts.avg_cycle_time_seconds)],
              ["Median cycle", fmtDuration(facts.median_cycle_time_seconds)],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <dt className="text-muted">{k}</dt>
                <dd className="font-mono font-semibold text-fg">{v}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {/* hottest hand-offs — click focuses the source node */}
      {facts.bottlenecks.length > 0 && (
        <section>
          <div className="mb-1.5 text-2xs font-bold uppercase tracking-[0.08em] text-muted/80">
            Slowest hand-offs
          </div>
          <ul className="space-y-1">
            {facts.bottlenecks.slice(0, 5).map((b, i) => (
              <li key={i}>
                <button
                  onClick={() => onSelect(b.source)}
                  className="flex w-full items-center gap-1.5 rounded-lg px-2 py-1.5 text-left text-xs text-fg-2 transition-colors hover:bg-panel-2/60 hover:text-fg"
                >
                  <span className="truncate">{b.source}</span>
                  <ArrowRight size={11} className="shrink-0 text-muted" />
                  <span className="truncate">{b.target}</span>
                  <span className="ml-auto shrink-0 font-mono font-semibold text-warning">
                    {fmtDuration(b.mean_wait_seconds)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {graph.offPath.length > 0 && (
        <p className="text-2xs leading-relaxed text-muted">
          {graph.offPath.length} low-volume activit{graph.offPath.length === 1 ? "y is" : "ies are"} outside
          the top paths: {graph.offPath.slice(0, 4).join(", ")}
          {graph.offPath.length > 4 ? "…" : ""}
        </p>
      )}

      {/* legend */}
      <section className="mt-auto rounded-xl border border-line bg-panel/50 p-3 text-2xs text-muted">
        <div className="mb-1.5 font-bold uppercase tracking-[0.08em] text-muted/80">Legend</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-success-vivid" /> start activity</div>
          <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-violet" /> end activity</div>
          <div className="flex items-center gap-2"><span className="h-0.5 w-4 rounded bg-warning-vivid" /> measured bottleneck wait</div>
          <div className="flex items-center gap-2"><span className="h-0.5 w-4 rounded bg-[var(--map-edge)]" /> hand-off · width = traffic</div>
        </div>
      </section>
    </aside>
  );
}
