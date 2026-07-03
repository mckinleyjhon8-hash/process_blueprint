"use client";

import { useState } from "react";
import {
  Bot,
  CircleHelp,
  Gavel,
  Loader2,
  Scale,
  ShieldAlert,
  TriangleAlert,
  UserCheck,
} from "lucide-react";
import type { AiAssessment } from "@/lib/types";
import { postAiAssessment } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Select } from "@/components/ui/Field";

const ROUTE_TONE = {
  Automate_Rules: "info",
  Augment_AI: "primary",
  Keep_Manual: "neutral",
  Defer: "warning",
  Pending: "warning",
} as const;

const ROUTE_LABEL: Record<string, string> = {
  Automate_Rules: "Automate with rules — no AI needed",
  Augment_AI: "Augment with AI",
  Keep_Manual: "Keep manual",
  Defer: "Defer AI — build the data first",
  Pending: "Pending answers",
};

const JURISDICTIONS = ["UK", "EU", "US", "KSA", "UAE_ONSHORE", "UAE_DIFC", "CA"];

/** Question controls — each posts immediately and rescores the whole tree. */
function QuestionControl({
  id,
  value,
  busy,
  onAnswer,
}: {
  id: string;
  value: unknown;
  busy: boolean;
  onAnswer: (id: string, v: unknown) => void;
}) {
  const common = "w-auto min-w-[160px] text-xs py-1.5";
  if (id === "task_type")
    return (
      <Select disabled={busy} className={common} value={(value as string) ?? ""}
        onChange={(e) => onAnswer(id, e.target.value || null)}>
        <option value="">choose…</option>
        {["classification", "extraction", "prediction", "language", "multi_step", "none"].map((t) => (
          <option key={t} value={t}>{t.replace("_", " ")}</option>
        ))}
      </Select>
    );
  if (id === "stakes")
    return (
      <Select disabled={busy} className={common} value={(value as string) ?? ""}
        onChange={(e) => onAnswer(id, e.target.value || null)}>
        <option value="">choose…</option>
        <option value="low">low (&lt;£50 per error)</option>
        <option value="medium">medium (£50–£500)</option>
        <option value="high">high (&gt;£500 / regulated)</option>
      </Select>
    );
  // boolean questions
  return (
    <Select disabled={busy} className={common}
      value={value === true ? "yes" : value === false ? "no" : ""}
      onChange={(e) => onAnswer(id, e.target.value === "" ? null : e.target.value === "yes")}>
      <option value="">choose…</option>
      <option value="yes">yes</option>
      <option value="no">no</option>
    </Select>
  );
}

export function AiRiskPanel({
  runId,
  initial,
}: {
  runId?: string;
  initial: AiAssessment;
}) {
  const [a, setA] = useState<AiAssessment>(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function answer(id: string, value: unknown) {
    if (!runId) return;
    setBusy(true);
    setError(null);
    try {
      setA(await postAiAssessment(runId, { [id]: value }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  const answers = (a.answers ?? {}) as Record<string, unknown>;
  const dims = Object.entries(a.data_readiness.dimensions);

  return (
    <div className="space-y-6">
      {/* ---- decision route ---- */}
      <Card>
        <div className="flex flex-wrap items-center gap-4">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-primary/12 text-primary">
            <Bot size={24} />
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={ROUTE_TONE[a.decision.route]}>{ROUTE_LABEL[a.decision.route]}</Badge>
              {a.decision.pattern && <Badge tone="violet">{a.decision.pattern}</Badge>}
              {busy && <Loader2 size={13} className="animate-spin text-muted" />}
            </div>
            <p className="mt-1 text-xs text-muted">{a.principle}</p>
            {a.targets.length > 0 && (
              <p className="mt-1 text-2xs text-muted">
                Candidates: {a.targets.slice(0, 4).join(" · ")}
              </p>
            )}
          </div>
        </div>
        <ol className="mt-4 space-y-1 border-t border-line-soft pt-3">
          {a.decision.trace.map((t, i) => (
            <li key={i} className="flex items-start gap-2 text-xs text-fg-2">
              <span className="mt-0.5 font-mono text-2xs text-muted">{i + 1}.</span> {t}
            </li>
          ))}
        </ol>
        {error && (
          <p className="mt-3 flex items-center gap-1.5 rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger ring-1 ring-inset ring-danger/25" role="alert">
            <TriangleAlert size={13} /> {error}
          </p>
        )}
      </Card>

      {/* ---- the questions that decide the route ---- */}
      <Card
        title="Decision inputs"
        subtitle="Each answer re-walks the tree live — unknowns stay conservative"
      >
        <ul className="divide-y divide-line-soft">
          {a.open_questions.map((q) => (
            <li key={q.id} className="flex flex-wrap items-center gap-3 py-2.5">
              <CircleHelp size={14} className="shrink-0 text-warning" />
              <span className="min-w-0 flex-1 text-sm text-fg">{q.question}</span>
              <QuestionControl id={q.id} value={answers[q.id]} busy={busy || !runId} onAnswer={answer} />
            </li>
          ))}
          {a.open_questions.length === 0 && (
            <li className="py-2.5 text-sm text-muted">All decision inputs answered.</li>
          )}
        </ul>
        {Object.keys(answers).length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5 border-t border-line-soft pt-3">
            {Object.entries(answers).filter(([k]) => k !== "readiness").map(([k, v]) => (
              <button key={k} onClick={() => answer(k, null)} disabled={busy || !runId}
                title="Click to clear"
                className="rounded-full bg-panel-2/70 px-2.5 py-1 text-2xs font-semibold text-fg-2 transition-colors hover:bg-danger/10 hover:text-danger">
                {k}: {String(v)} ×
              </button>
            ))}
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* ---- data readiness ---- */}
        <Card title="Data readiness" subtitle="No data = no AI — pattern minimums are hard gates">
          <ul className="space-y-3">
            {dims.map(([dim, d]) => (
              <li key={dim}>
                <div className="mb-1 flex items-center gap-2">
                  <span className="w-20 text-xs font-semibold capitalize text-fg">{dim}</span>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-panel-2">
                    <div
                      className={`h-full rounded-full ${d.score >= 3 ? "bg-success-vivid" : "bg-warning-vivid"}`}
                      style={{ width: `${(d.score / 5) * 100}%` }}
                    />
                  </div>
                  <Select disabled={busy || !runId} className="w-auto py-0.5 text-2xs"
                    value={String(d.score)}
                    onChange={(e) => answer("readiness", { [dim]: Number(e.target.value) })}
                    aria-label={`${dim} score`}>
                    {[0, 1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
                  </Select>
                  <Badge tone={d.basis === "auto" ? "primary" : d.basis === "operator" ? "success" : "neutral"}>
                    {d.basis}
                  </Badge>
                </div>
                <p className="text-2xs text-muted">{d.note}</p>
              </li>
            ))}
          </ul>
          {a.data_readiness.for_route && (
            <p className={`mt-3 rounded-lg px-3 py-2 text-xs font-semibold ${
              a.data_readiness.for_route.gate === "pass"
                ? "bg-success/10 text-success" : "bg-warning/10 text-warning"}`}>
              {a.decision.pattern}: {a.data_readiness.for_route.total}/{a.data_readiness.for_route.minimum}
              {" · "}gate {a.data_readiness.for_route.gate}
              {(a.data_readiness.for_route.precursors?.length ?? 0) > 0 &&
                ` → ${a.data_readiness.for_route.precursors!.join(" + ")}`}
            </p>
          )}
        </Card>

        {/* ---- HITL ---- */}
        <Card title="Human-in-the-loop design" subtitle="Stakes decide; regulation overrides">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-violet/12 text-violet">
              <UserCheck size={18} />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-fg">
                  {a.hitl.pattern.replaceAll("_", " ")}
                </span>
                {a.hitl.auto_process_threshold != null && (
                  <Badge tone="info">auto ≥{Math.round(a.hitl.auto_process_threshold * 100)}%</Badge>
                )}
                <Badge tone={a.hitl.stakes === "high" ? "danger" : a.hitl.stakes === "medium" ? "warning" : "success"}>
                  stakes: {a.hitl.stakes}{a.hitl.stakes_assumed ? " (assumed)" : ""}
                </Badge>
              </div>
              <p className="mt-1 text-xs leading-relaxed text-muted">{a.hitl.rationale}</p>
            </div>
          </div>

          <div className="mt-4 border-t border-line-soft pt-3">
            <div className="mb-2 flex items-center gap-2">
              <Gavel size={14} className="text-muted" />
              <span className="text-xs font-bold text-fg">ADM / regulatory gate</span>
              <Select disabled={busy || !runId} className="ml-auto w-auto py-1 text-2xs"
                value={a.jurisdiction} onChange={(e) => answer("jurisdiction", e.target.value)}
                aria-label="Jurisdiction">
                {JURISDICTIONS.map((j) => <option key={j} value={j}>{j.replaceAll("_", " ")}</option>)}
              </Select>
              <Badge tone={a.adm_gate.applies ? "danger" : a.adm_gate.answered ? "success" : "neutral"}>
                {a.adm_gate.applies ? "applies" : a.adm_gate.answered ? "not engaged" : "unanswered"}
              </Badge>
            </div>
            <p className="text-2xs font-semibold text-fg-2">{a.adm_gate.label}</p>
            <p className="mt-1 text-2xs leading-relaxed text-muted">{a.adm_gate.adm_rule}</p>
            <ul className="mt-2 space-y-1">
              {a.adm_gate.requirements.map((r, i) => (
                <li key={i} className="flex items-start gap-1.5 text-2xs text-fg-2">
                  <Scale size={10} className="mt-0.5 shrink-0 text-muted" /> {r}
                </li>
              ))}
            </ul>
            <p className="mt-2 rounded-lg bg-warning/10 px-2.5 py-1.5 text-2xs text-warning">
              ⚠ Research date {a.adm_gate.research_date}: {a.adm_gate.verify}
            </p>
          </div>
        </Card>
      </div>

      {/* ---- risk register ---- */}
      <Card
        title="Risk register"
        subtitle="Expected values: probability × impact, before and after mitigation"
        padded={false}
        action={
          <span className="text-right font-mono text-xs">
            <span className="text-muted">EV </span>
            <span className="text-danger">£{a.total_risk_ev_gbp.pre_mitigation.toLocaleString()}</span>
            <span className="text-muted"> → </span>
            <span className="font-bold text-success">£{a.total_risk_ev_gbp.post_mitigation.toLocaleString()}</span>
          </span>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-xs text-muted">
                <th className="px-5 py-2.5 font-medium">Risk</th>
                <th className="px-3 py-2.5 text-right font-medium">Impact</th>
                <th className="px-3 py-2.5 text-right font-medium">Pre-EV</th>
                <th className="px-3 py-2.5 text-right font-medium">Post-EV</th>
                <th className="px-5 py-2.5 font-medium">Mitigation</th>
              </tr>
            </thead>
            <tbody>
              {a.risk_register.map((r) => (
                <tr key={r.id} className="border-b border-line-soft last:border-0">
                  <td className="px-5 py-2.5">
                    <span className="flex items-center gap-2 font-medium text-fg">
                      <ShieldAlert size={13} className={r.id.startsWith("R") ? "text-violet" : "text-muted"} />
                      <span className="font-mono text-2xs text-muted">{r.id}</span> {r.label}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono text-fg-2">£{r.impact_gbp.toLocaleString()}</td>
                  <td className="px-3 py-2.5 text-right font-mono text-fg-2">
                    £{r.pre_ev_gbp.toLocaleString()} <span className="text-2xs text-muted">({r.pre_probability_pct}%)</span>
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono font-semibold text-fg">
                    £{r.post_ev_gbp.toLocaleString()} <span className="text-2xs text-muted">({r.post_probability_pct}%)</span>
                  </td>
                  <td className="px-5 py-2.5 text-2xs leading-relaxed text-muted">{r.mitigation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* ---- anti-pattern guards ---- */}
      <div className="flex flex-wrap gap-2">
        {a.anti_pattern_checks.map((c) => (
          <span key={c.id} title={c.note}
            className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-2xs font-semibold ring-1 ring-inset ${
              c.status === "pass" ? "bg-success/10 text-success ring-success/25"
              : c.status === "blocked" ? "bg-danger/10 text-danger ring-danger/25"
              : "bg-warning/10 text-warning ring-warning/25"}`}>
            {c.id}: {c.status}
          </span>
        ))}
      </div>
    </div>
  );
}
