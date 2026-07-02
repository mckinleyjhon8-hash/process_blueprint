"use client";

import { use, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Expand,
  FileText,
  Gauge,
  Loader2,
  Map,
  ShieldAlert,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import type { ProcessFacts } from "@/lib/types";
import { getRun } from "@/lib/api";
import { SEED_FACTS, SEED_BRIEF_CLIENT } from "@/lib/seed";
import { computeHealth } from "@/lib/health";
import { buildProcessGraph } from "@/lib/graph";
import { fmtDate } from "@/lib/format";
import { Page, PageHeader } from "@/components/ui/Page";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Tabs } from "@/components/ui/Tabs";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { KpiRibbon } from "@/components/dashboard/KpiRibbon";
import { HealthScore } from "@/components/dashboard/HealthScore";
import { ModelRadar } from "@/components/dashboard/ModelRadar";
import { Bottlenecks } from "@/components/dashboard/Bottlenecks";
import { Variants } from "@/components/dashboard/Variants";
import { Compliance } from "@/components/dashboard/Compliance";
import { BriefPanel } from "@/components/dashboard/BriefPanel";
import { ProcessCanvas } from "@/components/map/ProcessCanvas";
import { DependencyGraph } from "@/components/map/DependencyGraph";

/** Run workspace — one analysis, four focused views. */
export default function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const isSeed = id === "seed";

  const [facts, setFacts] = useState<(ProcessFacts & { has_map?: boolean }) | null>(
    isSeed ? SEED_FACTS : null,
  );
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState("overview");
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    if (isSeed) return;
    getRun(id)
      .then(setFacts)
      .catch((e) => setError(e instanceof Error ? e.message : "Run not found"));
  }, [id, isSeed]);

  const graph = useMemo(() => (facts ? buildProcessGraph(facts) : null), [facts]);
  const health = facts ? computeHealth(facts.model) : null;
  const breaches = facts?.compliance
    ? Object.values(facts.compliance.rules).reduce((s, r) => s + r.violations, 0)
    : 0;

  if (error) {
    return (
      <Page>
        <EmptyState
          icon={<TriangleAlert size={22} />}
          title="Run unavailable"
          description={`${error}. In-memory runs expire when the engine restarts; archived runs need Supabase.`}
          action={
            <Link href="/runs" className="text-sm font-semibold text-primary hover:underline">
              ← Back to runs
            </Link>
          }
        />
      </Page>
    );
  }

  if (!facts || !graph || !health) {
    return (
      <Page>
        <div className="space-y-4">
          <Skeleton className="h-9 w-72" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
      </Page>
    );
  }

  const mapHref = `/runs/${id}/map`;

  return (
    <Page width="wide">
      <PageHeader
        eyebrow={
          <div className="mb-1 flex flex-wrap items-center gap-1.5">
            <Badge tone="primary">{facts.model.algorithm} miner</Badge>
            <Badge tone={health.score != null && health.score >= 70 ? "success" : "warning"}>
              <Gauge size={11} /> health {health.score ?? "—"} · {health.grade}
            </Badge>
            {isSeed && <Badge tone="violet">sample preview</Badge>}
            {breaches > 0 && <Badge tone="danger"><ShieldAlert size={11} /> {breaches} SOP breaches</Badge>}
          </div>
        }
        title={`${facts.process_type} analysis`}
        description={`Mined from ${facts.n_events.toLocaleString()} events · ${fmtDate(facts.generated_at)} · evidence-based, not interview-based`}
        actions={
          <Link
            href={mapHref}
            className="flex items-center gap-1.5 rounded-xl bg-primary-strong px-3.5 py-2 text-xs font-semibold text-white shadow-[var(--elev-glow)] transition-colors hover:bg-primary"
          >
            <Expand size={14} /> Open Map Studio
          </Link>
        }
      />

      <Tabs
        tabs={[
          { id: "overview", label: "Overview", icon: <Gauge size={14} /> },
          { id: "map", label: "Process map", icon: <Map size={14} /> },
          {
            id: "compliance",
            label: "Compliance",
            icon: <ShieldAlert size={14} />,
            badge: breaches > 0 ? <Badge tone="danger">{breaches}</Badge> : undefined,
          },
          { id: "brief", label: "Brief & report", icon: <Sparkles size={14} /> },
        ]}
        active={tab}
        onChange={setTab}
      />

      {tab === "overview" && (
        <div className="space-y-6">
          <KpiRibbon facts={facts} />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <Card title="Process health" subtitle="Conformance-weighted" className="lg:col-span-3">
              <HealthScore score={health.score ?? 0} grade={health.grade} label={health.label} />
            </Card>
            <Card
              title="Model quality"
              subtitle="Discovered process vs. reality"
              className="lg:col-span-4"
              action={<Badge tone="neutral" className="font-mono">{facts.model.algorithm}</Badge>}
            >
              <ModelRadar model={facts.model} />
            </Card>
            <Card title="Top bottlenecks" subtitle="Slowest hand-offs by waiting time" className="lg:col-span-5">
              {facts.bottlenecks.length ? (
                <Bottlenecks items={facts.bottlenecks} />
              ) : (
                <p className="py-8 text-center text-sm text-muted">No significant bottlenecks detected.</p>
              )}
            </Card>
          </div>
          <Card title="Workflow variants" subtitle="How cases actually flow through the process">
            <Variants items={facts.top_variants} total={facts.n_cases} />
          </Card>
        </div>
      )}

      {tab === "map" && (
        <Card padded={false} className="overflow-hidden">
          <div className="flex items-center justify-between border-b border-line px-5 py-3">
            <p className="text-xs text-muted">
              Interactive preview — drag to pan, scroll to zoom, click an activity to focus it.
            </p>
            <Link href={mapHref} className="flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline">
              <Expand size={13} /> Full studio
            </Link>
          </div>
          <ProcessCanvas contentWidth={graph.width} contentHeight={graph.height} className="h-[480px]">
            <DependencyGraph graph={graph} selected={selected} onSelect={setSelected} highlight="" />
          </ProcessCanvas>
        </Card>
      )}

      {tab === "compliance" && (
        facts.compliance ? (
          <Card>
            <Compliance report={facts.compliance} />
          </Card>
        ) : (
          <Card padded={false}>
            <EmptyState
              icon={<ShieldAlert size={22} />}
              title="No SOP rule set for this run"
              description="Declarative compliance runs when a documented SOP rule set exists for the process — the UK Freight Brokerage sample ships with one."
            />
          </Card>
        )
      )}

      {tab === "brief" && (
        <Card>
          <BriefPanel
            facts={facts}
            runId={isSeed ? undefined : id}
            seedBrief={isSeed ? SEED_BRIEF_CLIENT : ""}
          />
        </Card>
      )}

      <footer className="flex items-center gap-2 pb-4 text-2xs text-muted">
        <FileText size={12} />
        run {isSeed ? "sample preview" : id} · pm4py engine isolated · clients receive reports only
      </footer>
    </Page>
  );
}
