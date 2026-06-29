"use client";

import { useState } from "react";
import { ShieldCheck, Lock, Sparkles, Download, Loader2, AlertTriangle } from "lucide-react";
import type { ProcessFacts } from "@/lib/types";
import { getBrief } from "@/lib/api";

type Audience = "internal" | "client";

function renderMarkdown(md: string) {
  return md.split("\n").map((line, i) => {
    if (line.startsWith("# "))
      return <h3 key={i} className="mb-2 text-[16px] font-bold text-fg">{line.slice(2)}</h3>;
    if (line.startsWith("## "))
      return (
        <h4 key={i} className="mt-4 mb-1 text-[13px] font-bold uppercase tracking-wide text-primary">
          {line.slice(3)}
        </h4>
      );
    if (line.startsWith("- "))
      return <li key={i} className="ml-4 list-disc text-[13px] leading-relaxed text-fg-2">{line.slice(2)}</li>;
    if (line.trim() === "") return <div key={i} className="h-1" />;
    return <p key={i} className="text-[13px] leading-relaxed text-fg-2">{line}</p>;
  });
}

export function BriefPanel({
  facts,
  runId,
  seedBrief,
  provider,
}: {
  facts: ProcessFacts;
  runId?: string;
  seedBrief: string;
  provider?: string;
}) {
  const [audience, setAudience] = useState<Audience>("client");
  const [briefs, setBriefs] = useState<Partial<Record<Audience, string>>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modelName, setModelName] = useState<string | null>(null);

  const live = briefs[audience];

  async function generate() {
    if (!runId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getBrief(runId, audience, provider);
      setBriefs((b) => ({ ...b, [audience]: res.markdown }));
      setModelName(res.model_name);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Brief generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-violet/15 text-violet">
            <Sparkles size={16} />
          </span>
          <div>
            <h2 className="text-[14px] font-bold text-fg">AI executive brief</h2>
            <p className="text-[11.5px] text-muted">{modelName || "claude-opus-4-8"} · BABOK-shaped</p>
          </div>
        </div>
        <div className="flex items-center gap-1 rounded-xl border border-line bg-bg-elev/60 p-1">
          {(["internal", "client"] as const).map((a) => (
            <button
              key={a}
              onClick={() => { setAudience(a); setError(null); }}
              className={
                "rounded-lg px-3 py-1.5 text-[12px] font-semibold capitalize transition-colors " +
                (audience === a ? "bg-primary-strong text-white" : "text-fg-2 hover:text-fg")
              }
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      {audience === "client" ? (
        <span className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-success/12 px-2.5 py-1 text-[11px] font-semibold text-success ring-1 ring-inset ring-success/25">
          <ShieldCheck size={12} /> Client-safe — engine details stripped
        </span>
      ) : (
        <span className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-warning/12 px-2.5 py-1 text-[11px] font-semibold text-warning ring-1 ring-inset ring-warning/25">
          <Lock size={12} /> Internal — includes mining mechanics
        </span>
      )}

      <div className="max-h-[440px] min-h-[200px] overflow-y-auto rounded-xl border border-line bg-bg-elev/40 p-5">
        {error && (
          <div className="flex items-start gap-2 rounded-lg bg-danger/10 p-3 text-[12.5px] text-danger ring-1 ring-inset ring-danger/25">
            <AlertTriangle size={15} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {loading && (
          <div className="flex items-center gap-2 text-[13px] text-muted">
            <Loader2 size={16} className="animate-spin text-primary" /> Generating with the LLM…
          </div>
        )}
        {!loading && live && renderMarkdown(live)}
        {!loading && !live && audience === "client" && (runId ? (
          <p className="text-[13px] text-muted">
            Click <span className="font-semibold text-fg">Generate</span> to produce the client-safe
            brief from this run (requires an LLM API key in <code className="font-mono">.env</code>).
          </p>
        ) : (
          renderMarkdown(seedBrief)
        ))}
        {!loading && !live && audience === "internal" && (
          <div className="space-y-2 text-[13px] leading-relaxed text-fg-2">
            <p className="text-fg"><span className="font-semibold">Internal view</span> — full mechanics the client never sees:</p>
            <ul className="ml-4 list-disc space-y-1 font-mono text-[12.5px]">
              <li>algorithm: {facts.model.algorithm}</li>
              <li>fitness {facts.model.fitness?.toFixed(3)} · precision {facts.model.precision?.toFixed(3)}</li>
              <li>generalization {facts.model.generalization?.toFixed(3)} · simplicity {facts.model.simplicity?.toFixed(3)}</li>
              <li>{facts.n_variants} variants / {facts.n_cases} cases · {facts.n_activities} activities</li>
              {facts.bottlenecks[0] && (
                <li>bottleneck {facts.bottlenecks[0].source} → {facts.bottlenecks[0].target} {(facts.bottlenecks[0].mean_wait_seconds/3600).toFixed(0)}h</li>
              )}
            </ul>
            <p className="pt-2 text-muted">
              {runId ? "Click Generate for the full LLM brief." : "Switch to Client to see the same findings in business language."}
            </p>
          </div>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        <button
          onClick={generate}
          disabled={!runId || loading}
          className="flex items-center gap-1.5 rounded-xl bg-primary-strong px-3.5 py-2 text-[12.5px] font-semibold text-white transition-colors hover:bg-primary disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
          {runId ? "Generate" : "Generate (upload a log)"}
        </button>
        <button className="flex items-center gap-1.5 rounded-xl border border-line bg-panel/60 px-3.5 py-2 text-[12.5px] font-semibold text-fg-2 hover:text-fg">
          <Download size={14} /> Export PDF
        </button>
      </div>
    </div>
  );
}
