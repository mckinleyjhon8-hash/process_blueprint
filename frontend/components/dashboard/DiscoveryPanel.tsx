"use client";

import { useMemo, useState } from "react";
import {
  CheckCircle2,
  CircleDashed,
  HelpCircle,
  Loader2,
  ShieldAlert,
  Sparkles,
  TriangleAlert,
  Zap,
} from "lucide-react";
import type { DiscoveryDomain, DiscoveryItem, DiscoveryReport } from "@/lib/types";
import { postDiscovery } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

const GATE_TONE = { pass: "success", caveated: "warning", blocked: "danger" } as const;
const GATE_LABEL = {
  pass: "ROI gate: pass",
  caveated: "ROI gate: caveated only",
  blocked: "ROI gate: blocked",
} as const;

function DomainBar({ domain }: { domain: DiscoveryDomain }) {
  const tone =
    domain.level === "below_must" ? "bg-danger" : domain.level === "must" ? "bg-warning-vivid" : "bg-success-vivid";
  return (
    <div className="relative h-2 overflow-hidden rounded-full bg-panel-2">
      <div className={`h-full rounded-full ${tone}`} style={{ width: `${domain.score}%` }} />
      {/* Must-threshold marker */}
      <span
        className="absolute top-0 h-full w-0.5 bg-fg/40"
        style={{ left: `${domain.must}%` }}
        title={`Must threshold: ${domain.must}`}
      />
    </div>
  );
}

function ItemRow({
  item,
  busy,
  onToggle,
}: {
  item: DiscoveryItem;
  busy: boolean;
  onToggle: (id: string, value: boolean) => void;
}) {
  const canToggle = item.status !== "auto";
  return (
    <li className="flex items-start gap-2.5 py-1.5">
      {item.status === "auto" ? (
        <span title="Evidenced by the event log (E1 · measured)">
          <Zap size={14} className="mt-0.5 shrink-0 text-primary" />
        </span>
      ) : (
        <button
          disabled={busy}
          onClick={() => onToggle(item.id, !item.granted)}
          aria-label={`${item.granted ? "Unconfirm" : "Confirm"} ${item.label}`}
          className="mt-0.5 shrink-0 text-muted transition-colors hover:text-primary disabled:opacity-50"
        >
          {item.granted ? (
            <CheckCircle2 size={14} className="text-success" />
          ) : (
            <CircleDashed size={14} className={item.critical ? "text-danger" : ""} />
          )}
        </button>
      )}
      <div className="min-w-0 flex-1">
        <span className={`text-xs ${item.granted ? "text-fg-2" : "font-medium text-fg"}`}>
          {item.label}
          <span className="ml-1.5 font-mono text-2xs text-muted">+{item.points}</span>
          {item.critical && !item.granted && (
            <Badge tone="danger" className="ml-1.5">must</Badge>
          )}
          {item.status === "auto" && (
            <Badge tone="primary" className="ml-1.5">log-evidenced</Badge>
          )}
        </span>
        {!item.granted && canToggle && (
          <p className="mt-0.5 flex items-start gap-1 text-2xs leading-relaxed text-muted">
            <HelpCircle size={11} className="mt-0.5 shrink-0" /> Ask: “{item.question}”
          </p>
        )}
      </div>
    </li>
  );
}

/** Guided discovery-completeness workspace: the log auto-evidences what it can,
    the operator confirms the rest, the ROI gate reacts live. */
export function DiscoveryPanel({
  runId,
  initial,
}: {
  runId?: string;
  initial: DiscoveryReport;
}) {
  const [report, setReport] = useState<DiscoveryReport>(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const autoCount = useMemo(
    () =>
      Object.values(report.domains).reduce(
        (n, d) => n + d.items.filter((i) => i.status === "auto").length,
        0,
      ),
    [report],
  );

  async function toggle(id: string, value: boolean) {
    if (!runId) return;
    setBusy(true);
    setError(null);
    try {
      setReport(await postDiscovery(runId, { [id]: value }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* ---- header: overall + ROI gate ---- */}
      <Card>
        <div className="flex flex-wrap items-center gap-5">
          <div className="flex items-center gap-3">
            <span className="grid h-14 w-14 place-items-center rounded-2xl bg-primary/12 font-mono text-xl font-bold text-primary">
              {Math.round(report.overall)}
            </span>
            <div>
              <h2 className="text-base font-bold text-fg">Discovery completeness</h2>
              <p className="text-xs text-muted">
                {autoCount} items evidenced by the event log automatically · confirm the rest below
              </p>
            </div>
          </div>
          <div className="ml-auto flex flex-col items-end gap-1">
            <Badge tone={GATE_TONE[report.roi_gate]}>
              <ShieldAlert size={11} /> {GATE_LABEL[report.roi_gate]}
            </Badge>
            <p className="max-w-[360px] text-right text-2xs text-muted">{report.roi_gate_note}</p>
          </div>
        </div>
        {error && (
          <p className="mt-3 flex items-center gap-1.5 rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger ring-1 ring-inset ring-danger/25" role="alert">
            <TriangleAlert size={13} /> {error}
          </p>
        )}
        {!runId && (
          <p className="mt-3 text-2xs text-muted">
            Sample preview — run a live analysis to record checklist answers.
          </p>
        )}
      </Card>

      {/* ---- what to go and ask next ---- */}
      {report.top_gaps.length > 0 && (
        <Card
          title="Close these gaps next"
          subtitle="Missing critical evidence — the playbook's exact follow-up questions"
        >
          <ul className="space-y-2">
            {report.top_gaps.map((g, i) => (
              <li key={i} className="flex items-start gap-2.5 rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
                <Sparkles size={13} className="mt-0.5 shrink-0 text-primary" />
                <div className="min-w-0">
                  <span className="text-xs font-semibold text-fg">
                    {report.domains[g.domain]?.label ?? g.domain} · {g.item}
                  </span>
                  <p className="text-2xs leading-relaxed text-muted">“{g.question}”</p>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* ---- six domains ---- */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {Object.entries(report.domains).map(([key, domain]) => (
          <Card
            key={key}
            title={domain.label}
            subtitle={`Must ≥${domain.must} · Should ≥${domain.should} · Complete ≥${domain.complete}`}
            action={
              <span className="flex items-center gap-2">
                {busy && <Loader2 size={12} className="animate-spin text-muted" />}
                <Badge
                  tone={
                    domain.level === "below_must" ? "danger" : domain.level === "must" ? "warning" : "success"
                  }
                >
                  {domain.score}
                </Badge>
              </span>
            }
          >
            <DomainBar domain={domain} />
            <ul className="mt-3 divide-y divide-line-soft">
              {domain.items.map((item) => (
                <ItemRow key={item.id} item={item} busy={busy || !runId} onToggle={toggle} />
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </div>
  );
}
