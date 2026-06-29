"use client";

import { useRef, useState } from "react";
import { RefreshCw, Workflow, Upload, Loader2, AlertTriangle, Play } from "lucide-react";
import type { ProcessFacts } from "@/lib/types";
import { analyzeLog, analyzeSample } from "@/lib/api";
import { computeHealth } from "@/lib/health";
import { Card } from "@/components/ui/Card";
import { KpiRibbon } from "./KpiRibbon";
import { HealthScore } from "./HealthScore";
import { ModelRadar } from "./ModelRadar";
import { Bottlenecks } from "./Bottlenecks";
import { Variants } from "./Variants";
import { BriefPanel } from "./BriefPanel";
import { PhaseTracker } from "./PhaseTracker";
import { Compliance } from "./Compliance";

const PROCESS_TYPES = [
  "Procure-to-Pay",
  "UK Freight Brokerage",
  "Order-to-Cash",
  "Issue Resolution",
  "Invoice Processing",
  "Customer Service",
];

export function DashboardClient({
  initialFacts,
  seedBrief,
}: {
  initialFacts: ProcessFacts;
  seedBrief: string;
}) {
  const [facts, setFacts] = useState<ProcessFacts>(initialFacts);
  const [processType, setProcessType] = useState("Procure-to-Pay");
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLive, setIsLive] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const health = computeHealth(facts.model);

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    await run(() => analyzeLog(file, processType));
    if (fileRef.current) fileRef.current.value = "";
  }

  async function run(fn: () => Promise<ProcessFacts>) {
    setAnalyzing(true);
    setError(null);
    try {
      const result = await fn();
      setFacts(result);
      setIsLive(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1280px] space-y-6">
      {/* Hero */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[12px] font-semibold text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" /> Engagement · Acme SME
            {isLive && (
              <span className="ml-1 rounded-full bg-success/12 px-2 py-0.5 text-[10.5px] text-success ring-1 ring-inset ring-success/25">
                live
              </span>
            )}
          </div>
          <h1 className="mt-1 text-[24px] font-extrabold tracking-tight text-fg">
            {facts.process_type} analysis
          </h1>
          <p className="mt-1 text-[13px] text-muted">
            Objective as-is process, mined from {facts.n_events.toLocaleString()} events ·{" "}
            <span className="text-fg-2">evidence-based, not interview-based</span>
          </p>
        </div>
        <PhaseTracker />
      </div>

      {/* Upload / analyze bar */}
      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-line bg-panel/60 p-3">
        <select
          value={processType}
          onChange={(e) => setProcessType(e.target.value)}
          className="rounded-xl border border-line bg-bg-elev/60 px-3 py-2 text-[13px] font-medium text-fg-2 focus:outline-none"
        >
          {PROCESS_TYPES.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
        <input
          ref={fileRef}
          type="file"
          accept=".csv,.xes"
          onChange={onFile}
          className="hidden"
        />
        <button
          onClick={() => fileRef.current?.click()}
          disabled={analyzing}
          className="flex items-center gap-1.5 rounded-xl border border-line bg-panel-2/60 px-3.5 py-2 text-[12.5px] font-semibold text-fg-2 transition-colors hover:text-fg disabled:opacity-50"
        >
          <Upload size={14} /> Upload log (CSV / XES)
        </button>
        <button
          data-testid="run-sample"
          onClick={() => run(() => analyzeSample(processType.includes("Freight") ? 600 : 400, processType))}
          disabled={analyzing}
          className="flex items-center gap-1.5 rounded-xl bg-primary-strong px-3.5 py-2 text-[12.5px] font-semibold text-white transition-colors hover:bg-primary disabled:opacity-50"
        >
          {analyzing ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          {analyzing ? "Mining live…" : "Run sample analysis (live)"}
        </button>
        <span className="text-[12px] text-muted">
          {isLive ? "Live data from the engine." : "Showing seed data — run a live analysis →"}
        </span>
        {error && (
          <span className="flex items-center gap-1.5 rounded-lg bg-danger/10 px-2.5 py-1 text-[12px] text-danger ring-1 ring-inset ring-danger/25">
            <AlertTriangle size={13} /> {error}
          </span>
        )}
      </div>

      <KpiRibbon facts={facts} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Card title="Process health score" subtitle="Conformance-weighted" className="lg:col-span-3">
          <HealthScore score={health.score ?? 0} grade={health.grade} label={health.label} />
        </Card>

        <Card
          title="Model quality"
          subtitle="Discovered process vs. reality"
          className="lg:col-span-4"
          action={
            <span className="rounded-lg bg-panel-2/60 px-2 py-1 font-mono text-[11px] text-muted">
              {facts.model.algorithm}
            </span>
          }
        >
          <ModelRadar model={facts.model} />
        </Card>

        <Card title="Top bottlenecks" subtitle="Slowest hand-offs by waiting time" className="lg:col-span-5">
          {facts.bottlenecks.length ? (
            <Bottlenecks items={facts.bottlenecks} />
          ) : (
            <p className="py-8 text-center text-[13px] text-muted">No significant bottlenecks detected.</p>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Card
          title="Process map"
          subtitle="Discovered Petri net"
          className="lg:col-span-7"
          action={
            <button className="flex items-center gap-1.5 rounded-lg border border-line bg-panel-2/60 px-2.5 py-1.5 text-[11.5px] font-semibold text-fg-2 hover:text-fg">
              <RefreshCw size={13} /> Re-discover
            </button>
          }
        >
          <div className="grid h-[220px] place-items-center rounded-xl border border-dashed border-line bg-bg-elev/40">
            <div className="flex flex-col items-center gap-2 text-center">
              <span className="grid h-12 w-12 place-items-center rounded-2xl bg-primary/12 text-primary">
                <Workflow size={22} />
              </span>
              <p className="text-[13px] font-semibold text-fg-2">Petri-net render</p>
              <p className="max-w-[260px] text-[11.5px] text-muted">
                {facts.n_activities} activities · {facts.n_variants} variants · served from the engine.
              </p>
            </div>
          </div>
        </Card>

        <Card title="Workflow variants" subtitle="Path distribution" className="lg:col-span-5">
          <Variants items={facts.top_variants} total={facts.n_cases} />
        </Card>
      </div>

      {facts.compliance && (
        <Card className="p-5">
          <Compliance report={facts.compliance} />
        </Card>
      )}

      <Card className="p-5">
        <BriefPanel facts={facts} runId={facts.run_id} seedBrief={seedBrief} />
      </Card>

      <footer className="pb-4 pt-2 text-center text-[11px] text-muted">
        Process Blueprint · internal tool · pm4py engine isolated · clients receive reports only
      </footer>
    </div>
  );
}
