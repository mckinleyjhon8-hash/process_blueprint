"use client";

import { use, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowLeft, GitBranch, Loader2, Network, TriangleAlert } from "lucide-react";
import type { ProcessFacts } from "@/lib/types";
import { getRun, processMapUrl } from "@/lib/api";
import { SEED_FACTS } from "@/lib/seed";
import { buildProcessGraph } from "@/lib/graph";
import { ProcessCanvas } from "@/components/map/ProcessCanvas";
import { DependencyGraph } from "@/components/map/DependencyGraph";
import { Inspector } from "@/components/map/Inspector";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

type Layer = "graph" | "petri";

/** Map Studio — full-viewport process-map workspace (Miro/Lucidchart class):
    zoom, pan, fit, fullscreen, minimap, inspector, activity search. */
export default function MapStudioPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const isSeed = id === "seed";

  const [facts, setFacts] = useState<(ProcessFacts & { has_map?: boolean }) | null>(
    isSeed ? SEED_FACTS : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [layer, setLayer] = useState<Layer>("graph");
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [petri, setPetri] = useState<{ w: number; h: number } | null>(null);
  const [petriFailed, setPetriFailed] = useState(false);

  useEffect(() => {
    if (isSeed) return;
    getRun(id)
      .then(setFacts)
      .catch((e) => setError(e instanceof Error ? e.message : "Run not found"));
  }, [id, isSeed]);

  const graph = useMemo(() => (facts ? buildProcessGraph(facts) : null), [facts]);
  const petriAvailable = Boolean(facts?.has_map) && !petriFailed;

  if (error) {
    return (
      <EmptyState
        icon={<TriangleAlert size={22} />}
        title="Run unavailable"
        description={`${error}. In-memory runs expire when the engine restarts; archived runs need Supabase.`}
        action={
          <Link href="/runs" className="text-sm font-semibold text-primary hover:underline">
            ← Back to runs
          </Link>
        }
        className="h-full"
      />
    );
  }

  if (!facts || !graph) {
    return (
      <div className="grid h-full place-items-center text-sm text-muted">
        <span className="flex items-center gap-2">
          <Loader2 size={16} className="animate-spin text-primary" /> Loading run…
        </span>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* ---- studio toolbar ---- */}
      <div className="flex shrink-0 flex-wrap items-center gap-3 border-b border-line bg-bg-elev/60 px-4 py-2.5 backdrop-blur-xl">
        <Link
          href={isSeed ? "/" : `/runs/${id}`}
          className="flex items-center gap-1.5 text-xs font-semibold text-muted transition-colors hover:text-fg"
        >
          <ArrowLeft size={14} /> {isSeed ? "Dashboard" : "Run workspace"}
        </Link>
        <span className="h-4 w-px bg-line" aria-hidden />
        <h1 className="truncate text-sm font-bold text-fg">{facts.process_type} — process map</h1>
        <Badge tone="neutral" className="hidden sm:inline-flex">
          {facts.n_activities} activities · {facts.n_variants} variants
        </Badge>

        <div className="ml-auto flex items-center gap-1 rounded-xl border border-line bg-panel/60 p-1" role="group" aria-label="Map layer">
          <button
            onClick={() => setLayer("graph")}
            aria-pressed={layer === "graph"}
            className={
              "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors " +
              (layer === "graph" ? "bg-primary-strong text-white" : "text-fg-2 hover:text-fg")
            }
          >
            <GitBranch size={13} /> Dependency graph
          </button>
          <button
            onClick={() => setLayer("petri")}
            disabled={!petriAvailable}
            aria-pressed={layer === "petri"}
            title={petriAvailable ? "Formal Petri net (Graphviz)" : "Petri net needs the in-session log + Graphviz"}
            className={
              "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40 " +
              (layer === "petri" ? "bg-primary-strong text-white" : "text-fg-2 hover:text-fg")
            }
          >
            <Network size={13} /> Petri net
          </button>
        </div>
      </div>

      {/* ---- canvas + inspector ---- */}
      <div className="flex min-h-0 flex-1">
        {layer === "graph" ? (
          <ProcessCanvas contentWidth={graph.width} contentHeight={graph.height} className="flex-1">
            <DependencyGraph graph={graph} selected={selected} onSelect={setSelected} highlight={query} />
          </ProcessCanvas>
        ) : (
          <ProcessCanvas
            contentWidth={petri?.w ?? 1200}
            contentHeight={petri?.h ?? 600}
            className="flex-1"
          >
            <div className="rounded-xl bg-white p-4" style={petri ? { width: petri.w, height: petri.h } : undefined}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={processMapUrl(id)}
                alt={`Discovered Petri net for ${facts.process_type}`}
                draggable={false}
                onLoad={(e) => {
                  const img = e.currentTarget;
                  setPetri({ w: img.naturalWidth + 32, h: img.naturalHeight + 32 });
                }}
                onError={() => {
                  setPetriFailed(true);
                  setLayer("graph");
                }}
              />
            </div>
          </ProcessCanvas>
        )}

        <div className="hidden md:flex">
          <Inspector
            facts={facts}
            graph={graph}
            selected={selected}
            onSelect={setSelected}
            query={query}
            onQuery={setQuery}
          />
        </div>
      </div>
    </div>
  );
}
