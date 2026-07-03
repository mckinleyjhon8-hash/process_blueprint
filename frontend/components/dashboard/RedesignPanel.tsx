"use client";

import {
  ArrowDown,
  ArrowUp,
  Lock,
  Minus,
  Quote,
  Route,
  TriangleAlert,
  Wrench,
} from "lucide-react";
import type { ProcessFacts, RedesignRec } from "@/lib/types";
import { fmtDuration } from "@/lib/format";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";

const DISPO_TONE = {
  Eliminate: "danger",
  Simplify: "info",
  Standardise: "violet",
  Automate: "primary",
  Augment_AI: "warning",
} as const;

const PHASE_LABEL: Record<number, string> = {
  0: "Phase 0 · Foundation",
  1: "Phase 1 · Quick wins",
  2: "Phase 2 · Core automation",
  3: "Phase 3 · AI augmentation",
};

const QUAD_LABEL: Record<string, string> = {
  time: "Time",
  cost: "Cost",
  quality: "Quality",
  flexibility: "Flexibility",
};

function QuadEffect({ dim, effect }: { dim: string; effect: string }) {
  const icon =
    effect === "+" ? <ArrowUp size={11} className="text-success" />
    : effect === "-" ? <ArrowDown size={11} className="text-danger" />
    : <Minus size={11} className="text-muted" />;
  return (
    <span className="flex items-center gap-1 text-2xs text-muted" title={`${QUAD_LABEL[dim]}: ${effect}`}>
      {icon} {QUAD_LABEL[dim]}
    </span>
  );
}

function DeltaLine({ rec }: { rec: RedesignRec }) {
  const d = rec.delta;
  if (!d || !("metric" in d) || !d.baseline) return null;
  const [lo, hi] = d.reduction_pct_range;
  const isTime = d.unit === "seconds";
  const fmt = (v: number) => (isTime ? fmtDuration(v) : `${v}${d.unit === "pct_points" ? "pp" : d.unit}`);
  return (
    <p className="mt-2 rounded-lg bg-primary/8 px-3 py-2 text-xs text-fg-2">
      <span className="font-semibold text-fg">Computed effect</span> ({d.scope}):{" "}
      {fmt(d.baseline)} → <span className="font-mono font-semibold text-primary">
        {fmt(d.to_be_range[0])}–{fmt(d.to_be_range[1])}
      </span>{" "}
      <span className="text-muted">(−{lo}–{hi}%, cited heuristic range applied to the measured baseline)</span>
    </p>
  );
}

function RecCard({ rec }: { rec: RedesignRec }) {
  return (
    <div className="rounded-xl border border-line bg-panel-2/30 p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={DISPO_TONE[rec.disposition]}>{rec.disposition.replace("_", " ")}</Badge>
        <span className="text-sm font-bold text-fg">{rec.name}</span>
        <span className="font-mono text-2xs text-muted">{rec.heuristic}</span>
        <span className="ml-auto flex flex-wrap gap-1">
          {rec.targets.slice(0, 3).map((t) => (
            <Badge key={t} tone="neutral">{t}</Badge>
          ))}
          {rec.targets.length > 3 && <Badge tone="neutral">+{rec.targets.length - 3}</Badge>}
        </span>
      </div>

      <p className="mt-2 flex items-start gap-1.5 text-xs leading-relaxed text-fg-2">
        <Quote size={12} className="mt-0.5 shrink-0 text-primary" />
        <span><span className="font-semibold text-fg">Measured trigger:</span> {rec.trigger_evidence}</span>
      </p>

      <p className="mt-1.5 flex items-start gap-1.5 text-xs leading-relaxed text-fg-2">
        <Wrench size={12} className="mt-0.5 shrink-0 text-muted" />
        <span>{rec.move}</span>
      </p>

      <DeltaLine rec={rec} />

      <p className="mt-2 flex items-start gap-1.5 text-2xs leading-relaxed text-warning">
        <TriangleAlert size={11} className="mt-0.5 shrink-0" />
        <span>Verify first: {rec.precondition}</span>
      </p>

      {(rec.blockers?.length ?? 0) > 0 && (
        <ul className="mt-2 space-y-1">
          {rec.blockers!.map((b, i) => (
            <li key={i} className="flex items-center gap-1.5 rounded-lg bg-danger/10 px-2.5 py-1.5 text-2xs font-semibold text-danger">
              <Lock size={11} /> {b}
            </li>
          ))}
        </ul>
      )}

      {rec.gated_by.length > 0 && (
        <p className="mt-2 flex items-center gap-1.5 rounded-lg bg-warning/10 px-2.5 py-1.5 text-2xs font-semibold text-warning">
          <Lock size={11} /> ECRS gate: blocked until {rec.gated_by.length} Eliminate/Simplify/Standardise
          recommendation{rec.gated_by.length > 1 ? "s are" : " is"} resolved — never pave the cow-path.
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-line-soft pt-2">
        {Object.entries(rec.quadrangle ?? {}).map(([dim, eff]) => (
          <QuadEffect key={dim} dim={dim} effect={eff} />
        ))}
        <span className="ml-auto text-2xs text-muted/70">{rec.source}</span>
      </div>
    </div>
  );
}

/** Deterministic TO-BE recommendations: measured triggers → cited heuristics
    → computed deltas, sequenced Eliminate → … → Augment_AI. */
export function RedesignPanel({ facts }: { facts: ProcessFacts }) {
  const r = facts.redesign;
  if (!r || r.n_recommendations === 0) {
    return (
      <Card padded={false}>
        <EmptyState
          icon={<Route size={22} />}
          title="No redesign triggers fired"
          description="The mined facts show no batching, rework, queue tails, SPOF or triage signals — or this run predates the redesign engine (re-run the analysis)."
        />
      </Card>
    );
  }

  const [lo, hi] = r.aggregate.lead_time_reduction_seconds_range;
  const phases = [0, 1, 2, 3].filter((p) => r.recommendations.some((x) => x.phase === p));

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-center gap-5">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-primary/12 text-primary">
            <Route size={24} />
          </span>
          <div className="min-w-0">
            <h2 className="text-base font-bold text-fg">
              {r.n_recommendations} evidence-triggered recommendations
            </h2>
            <p className="text-xs text-muted">{r.principle}</p>
          </div>
          {hi > 0 && (
            <div className="ml-auto text-right">
              <div className="font-mono text-lg font-bold text-primary">
                {fmtDuration(lo)}–{fmtDuration(hi)}
              </div>
              <p className="text-2xs text-muted">
                potential lead-time reduction vs {fmtDuration(r.aggregate.baseline_lead_time_seconds)} baseline
                <br />realisation: Y1 {r.aggregate.realisation_phasing.Y1} · Y2 {r.aggregate.realisation_phasing.Y2} · Y3 {r.aggregate.realisation_phasing.Y3}
              </p>
            </div>
          )}
        </div>
        {r.aggregate.cap_note && (
          <p className="mt-3 flex items-start gap-1.5 rounded-lg bg-warning/10 px-3 py-2 text-2xs text-warning">
            <TriangleAlert size={12} className="mt-0.5 shrink-0" /> {r.aggregate.cap_note}
          </p>
        )}
      </Card>

      {phases.map((phase) => (
        <Card key={phase} title={PHASE_LABEL[phase]} padded={false}>
          <div className="space-y-3 p-4">
            {r.recommendations
              .filter((x) => x.phase === phase)
              .map((rec, i) => (
                <RecCard key={`${rec.heuristic}-${i}`} rec={rec} />
              ))}
          </div>
        </Card>
      ))}
    </div>
  );
}
