"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  Cpu,
  Database,
  FileText,
  KeyRound,
  Play,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  Upload,
  Workflow,
} from "lucide-react";
import type { ProcessFacts } from "@/lib/types";
import {
  analyzeLog,
  analyzeSample,
  apiHealth,
  getConfig,
  getRuns,
  type AppConfig,
  type RunSummary,
} from "@/lib/api";
import { fmtDate, fmtInt, fmtRatio } from "@/lib/format";
import { Page, PageHeader } from "@/components/ui/Page";
import { Card } from "@/components/ui/Card";
import { Badge, StatusDot } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { LabeledSelect } from "@/components/ui/Field";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

const PROCESS_TYPES = [
  "Procure-to-Pay",
  "UK Freight Brokerage",
  "Order-to-Cash",
  "Issue Resolution",
  "Invoice Processing",
  "Customer Service",
];

export default function DashboardPage() {
  const router = useRouter();
  const [online, setOnline] = useState<boolean | null>(null);
  const [runs, setRuns] = useState<RunSummary[] | null>(null);
  const [cfg, setCfg] = useState<AppConfig | null>(null);

  const [processType, setProcessType] = useState("Procure-to-Pay");
  const [analyzing, setAnalyzing] = useState<"sample" | "upload" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const newCardRef = useRef<HTMLElement>(null);

  useEffect(() => {
    apiHealth().then(setOnline);
    getRuns().then((d) => setRuns(d.runs ?? [])).catch(() => setRuns([]));
    getConfig().then(setCfg).catch(() => setCfg(null));
    // /?focus=new (topbar + palette) scrolls the analysis card into view
    if (window.location.search.includes("focus=new")) {
      setTimeout(() => newCardRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 80);
    }
  }, []);

  async function run(kind: "sample" | "upload", fn: () => Promise<ProcessFacts>) {
    setAnalyzing(kind);
    setError(null);
    try {
      const facts = await fn();
      if (facts.run_id) router.push(`/runs/${facts.run_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
      setAnalyzing(null);
    }
  }

  const latest = runs?.find((r) => r.run_id) ?? null;
  const provider = cfg?.llm.providers[cfg.llm.default_provider];
  const anyLlmKey = cfg ? Object.values(cfg.llm.providers).some((p) => p.key_present) : null;

  /* ---- attention items: only things that genuinely need a decision ---- */
  const attention: { tone: "danger" | "warning"; text: string; href: string; cta: string }[] = [];
  if (online === false)
    attention.push({ tone: "danger", text: "Engine offline — analyses and briefs are unavailable.", href: "/settings", cta: "Setup" });
  if (anyLlmKey === false)
    attention.push({ tone: "danger", text: "No LLM API key configured — brief generation will fail.", href: "/settings", cta: "Fix" });
  if (latest?.model_precision != null && latest.model_precision < 0.7)
    attention.push({
      tone: "warning",
      text: `Latest ${latest.process_type} run has precision ${fmtRatio(latest.model_precision)} — high variability, review the map.`,
      href: `/runs/${latest.run_id}/map`,
      cta: "Open map",
    });

  return (
    <Page width="wide">
      <PageHeader
        title="Dashboard"
        description="Mine an event log, review the run workspace, deliver the brief."
        actions={
          online == null ? (
            <StatusDot tone="neutral" label="checking engine…" />
          ) : online ? (
            <StatusDot tone="success" label="engine online" />
          ) : (
            <StatusDot tone="danger" label="engine offline" pulse />
          )
        }
      />

      {/* ---- needs attention ---- */}
      {attention.length > 0 && (
        <div className="space-y-2" role="alert" aria-label="Needs attention">
          {attention.map((a, i) => (
            <div
              key={i}
              className={`flex items-center gap-2.5 rounded-xl px-4 py-3 text-sm ring-1 ring-inset ${
                a.tone === "danger" ? "bg-danger/10 text-danger ring-danger/25" : "bg-warning/10 text-warning ring-warning/25"
              }`}
            >
              <TriangleAlert size={15} className="shrink-0" />
              <span className="min-w-0 flex-1">{a.text}</span>
              <Link href={a.href} className="shrink-0 text-xs font-bold underline-offset-2 hover:underline">
                {a.cta} →
              </Link>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* ================= left 2/3 ================= */}
        <div className="space-y-6 xl:col-span-2">
          {/* ---- new analysis ---- */}
          <Card
            title="New analysis"
            subtitle="Upload a client event log or mine a bundled sample — you'll land in the run workspace."
          >
            <span ref={newCardRef} />
            <div className="flex flex-wrap items-end gap-3">
              <LabeledSelect
                label="Process type"
                value={processType}
                onChange={(e) => setProcessType(e.target.value)}
                className="w-full sm:w-[240px]"
              >
                {PROCESS_TYPES.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </LabeledSelect>

              <input
                ref={fileRef}
                type="file"
                accept=".csv,.xes"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) run("upload", () => analyzeLog(f, processType));
                  e.target.value = "";
                }}
              />
              <Button
                icon={<Upload size={14} />}
                loading={analyzing === "upload"}
                disabled={!!analyzing || online === false}
                onClick={() => fileRef.current?.click()}
              >
                Upload log (CSV / XES)
              </Button>
              <Button
                variant="primary"
                data-testid="run-sample"
                icon={<Play size={14} />}
                loading={analyzing === "sample"}
                disabled={!!analyzing || online === false}
                onClick={() =>
                  run("sample", () => analyzeSample(processType.includes("Freight") ? 600 : 400, processType))
                }
              >
                {analyzing === "sample" ? "Mining live…" : "Run sample analysis"}
              </Button>
            </div>

            {error && (
              <p className="mt-3 flex items-center gap-1.5 rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger ring-1 ring-inset ring-danger/25" role="alert">
                <TriangleAlert size={13} /> {error}
              </p>
            )}
            {online === false && (
              <p className="mt-3 text-xs text-muted">
                Engine offline — start it with{" "}
                <code className="font-mono text-fg-2">uvicorn backend.api:app --port 8000</code>, or{" "}
                <Link href="/runs/seed" className="font-semibold text-primary hover:underline">
                  preview the sample workspace
                </Link>{" "}
                without it.
              </p>
            )}
          </Card>

          {/* ---- recent runs ---- */}
          <Card
            title="Recent runs"
            subtitle="Pick up where you left off"
            action={
              <Link href="/runs" className="flex items-center gap-1 text-xs font-semibold text-primary hover:underline">
                View all <ArrowRight size={12} />
              </Link>
            }
            padded={false}
          >
            <div className="px-2 pb-2">
              {runs == null ? (
                <div className="space-y-2 p-3">
                  {[0, 1, 2].map((i) => <Skeleton key={i} className="h-12 w-full" />)}
                </div>
              ) : runs.length === 0 ? (
                <EmptyState
                  icon={<Workflow size={22} />}
                  title="No analyses yet"
                  description="Run your first analysis above — the complete as-is process, bottlenecks and compliance findings land here."
                />
              ) : (
                <ul className="divide-y divide-line-soft">
                  {runs.slice(0, 5).map((r, i) => (
                    <li key={r.run_id ?? i}>
                      {r.run_id ? (
                        <Link
                          href={`/runs/${r.run_id}`}
                          className="flex items-center gap-3 rounded-xl px-3 py-3 transition-colors hover:bg-panel-2/50"
                        >
                          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary/12 text-primary">
                            <FileText size={15} />
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block truncate text-sm font-semibold text-fg">{r.process_type}</span>
                            <span className="block text-2xs text-muted">
                              {fmtInt(r.n_cases)} cases · {fmtInt(r.n_variants)} variants · {fmtDate(r.created_at)}
                            </span>
                          </span>
                          <span className="hidden shrink-0 items-center gap-3 font-mono text-xs text-fg-2 sm:flex">
                            <span title="fitness">fit {fmtRatio(r.model_fitness)}</span>
                            <span title="precision">prec {fmtRatio(r.model_precision)}</span>
                          </span>
                          <ArrowRight size={14} className="shrink-0 text-muted" />
                        </Link>
                      ) : (
                        <div className="flex items-center gap-3 px-3 py-3 opacity-60">
                          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-panel-2 text-muted">
                            <FileText size={15} />
                          </span>
                          <span className="min-w-0 flex-1">
                            <span className="block truncate text-sm font-semibold text-fg-2">{r.process_type}</span>
                            <span className="block text-2xs text-muted">archived without id</span>
                          </span>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Card>
        </div>

        {/* ================= right rail ================= */}
        <div className="space-y-6">
          <Card title="Pipeline" subtitle="How a deliverable is produced">
            <ol className="space-y-3">
              {[
                { icon: Upload, t: "Ingest", d: "Event log lands; columns normalised to the canonical schema." },
                { icon: Workflow, t: "Mine", d: "pm4py discovers the as-is model, conformance, bottlenecks, rework." },
                { icon: Sparkles, t: "Ground & write", d: "LLM drafts the BABOK-shaped brief on facts + pgvector benchmarks." },
                { icon: ShieldCheck, t: "Approve & export", d: "Consultant approves; client receives the branded report only." },
              ].map(({ icon: Icon, t, d }, i) => (
                <li key={t} className="flex gap-3">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/12 text-primary">
                    <Icon size={14} />
                  </span>
                  <span>
                    <span className="block text-sm font-semibold text-fg">{i + 1}. {t}</span>
                    <span className="block text-2xs leading-relaxed text-muted">{d}</span>
                  </span>
                </li>
              ))}
            </ol>
          </Card>

          <Card title="System status" subtitle="Configured server-side via .env">
            {cfg === null && online !== false ? (
              <div className="space-y-2">
                {[0, 1, 2].map((i) => <Skeleton key={i} className="h-9 w-full" />)}
              </div>
            ) : (
              <ul className="space-y-2 text-sm">
                <li className="flex items-center justify-between rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
                  <span className="flex items-center gap-2 text-fg-2"><Cpu size={14} className="text-muted" /> Generation</span>
                  <span className="flex items-center gap-2">
                    <span className="font-mono text-xs text-fg-2">{cfg?.llm.default_provider ?? "—"}</span>
                    {provider?.key_present ? <CheckCircle2 size={14} className="text-success" /> : <TriangleAlert size={14} className="text-danger" />}
                  </span>
                </li>
                <li className="flex items-center justify-between rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
                  <span className="flex items-center gap-2 text-fg-2"><KeyRound size={14} className="text-muted" /> Embeddings</span>
                  <span className="flex items-center gap-2">
                    <span className="font-mono text-xs text-fg-2">{cfg?.embeddings.provider ?? "—"}</span>
                    {cfg?.embeddings.key_present ? <CheckCircle2 size={14} className="text-success" /> : <TriangleAlert size={14} className="text-danger" />}
                  </span>
                </li>
                <li className="flex items-center justify-between rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
                  <span className="flex items-center gap-2 text-fg-2"><Database size={14} className="text-muted" /> Supabase</span>
                  {cfg?.supabase.configured ? (
                    <Badge tone="success">connected</Badge>
                  ) : (
                    <Badge tone="neutral">not configured</Badge>
                  )}
                </li>
                <li className="flex items-center justify-between rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
                  <span className="flex items-center gap-2 text-fg-2"><Workflow size={14} className="text-muted" /> Petri-net render</span>
                  {cfg?.render?.graphviz ? (
                    <Badge tone="success">graphviz ready</Badge>
                  ) : (
                    <Badge tone="neutral">graph fallback</Badge>
                  )}
                </li>
              </ul>
            )}
            <Link href="/settings" className="mt-3 flex items-center gap-1 text-xs font-semibold text-primary hover:underline">
              Model & provider settings <ArrowRight size={12} />
            </Link>
          </Card>
        </div>
      </div>
    </Page>
  );
}
