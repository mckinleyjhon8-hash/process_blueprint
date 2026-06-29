import { Card } from "@/components/ui/Card";
import { KpiRibbon } from "@/components/dashboard/KpiRibbon";
import { HealthScore } from "@/components/dashboard/HealthScore";
import { ModelRadar } from "@/components/dashboard/ModelRadar";
import { Bottlenecks } from "@/components/dashboard/Bottlenecks";
import { Variants } from "@/components/dashboard/Variants";
import { BriefPanel } from "@/components/dashboard/BriefPanel";
import { PhaseTracker } from "@/components/dashboard/PhaseTracker";
import { SEED_FACTS, SEED_HEALTH, SEED_BRIEF_CLIENT } from "@/lib/seed";
import { RefreshCw, Workflow } from "lucide-react";

export default function DashboardPage() {
  const facts = SEED_FACTS;

  return (
    <div className="mx-auto max-w-[1280px] space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-[12px] font-semibold text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" /> Engagement · Acme SME
          </div>
          <h1 className="mt-1 text-[24px] font-extrabold tracking-tight text-fg">
            Procure-to-Pay analysis
          </h1>
          <p className="mt-1 text-[13px] text-muted">
            Objective as-is process, mined from {facts.n_events.toLocaleString()} events ·{" "}
            <span className="text-fg-2">evidence-based, not interview-based</span>
          </p>
        </div>
        <PhaseTracker />
      </div>

      <KpiRibbon facts={facts} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <Card title="Process health score" subtitle="Conformance-weighted" className="lg:col-span-3">
          <HealthScore score={SEED_HEALTH.score} grade={SEED_HEALTH.grade} label={SEED_HEALTH.label} />
        </Card>

        <Card
          title="Model quality"
          subtitle="Discovered process vs. reality"
          className="lg:col-span-4"
          action={
            <span className="rounded-lg bg-panel-2/60 px-2 py-1 font-mono text-[11px] text-muted">
              inductive
            </span>
          }
        >
          <ModelRadar model={facts.model} />
        </Card>

        <Card
          title="Top bottlenecks"
          subtitle="Slowest hand-offs by waiting time"
          className="lg:col-span-5"
        >
          <Bottlenecks items={facts.bottlenecks} />
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
                Served from the engine as PNG/SVG. {facts.n_activities} activities ·{" "}
                {facts.n_variants} variants.
              </p>
            </div>
          </div>
        </Card>

        <Card title="Workflow variants" subtitle="Path distribution" className="lg:col-span-5">
          <Variants items={facts.top_variants} total={facts.n_cases} />
        </Card>
      </div>

      <Card className="p-5">
        <BriefPanel clientBrief={SEED_BRIEF_CLIENT} />
      </Card>

      <footer className="pb-4 pt-2 text-center text-[11px] text-muted">
        Process Blueprint · internal tool · pm4py engine isolated · clients receive reports only
      </footer>
    </div>
  );
}
