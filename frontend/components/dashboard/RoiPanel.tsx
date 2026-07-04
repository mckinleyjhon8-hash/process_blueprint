"use client";

import { useState } from "react";
import {
  Banknote,
  Calculator,
  Hourglass,
  Loader2,
  ShieldAlert,
  TriangleAlert,
} from "lucide-react";
import type { RoiReport, RoiScenario } from "@/lib/types";
import { postRoi } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Field, Input, Select } from "@/components/ui/Field";

const GATE_TONE = { pass: "success", caveated: "warning", blocked: "danger" } as const;

const TCO_LABELS: Record<string, string> = {
  build: "Build / implementation",
  licence_3yr: "Licence (36 months)",
  maintenance_3yr: "Maintenance (3yr)",
  exception_upkeep_3yr: "Exception handling (3yr)",
  change_3yr: "Change requests (3yr)",
  training: "Training",
  decommission: "Decommission",
  contingency: "Contingency",
};

function gbp(n: number | undefined | null): string {
  return n == null ? "—" : `£${Math.round(n).toLocaleString()}`;
}

function ScenarioCard({ name, s, highlight }: { name: string; s: RoiScenario; highlight: boolean }) {
  return (
    <div className={`rounded-2xl border p-4 ${highlight ? "border-primary/50 bg-primary/8" : "border-line bg-panel-2/30"}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wide text-fg-2">{name}</span>
        <Badge tone={highlight ? "primary" : "neutral"}>
          Y1 {Math.round(s.realisation_curve[0] * 100)}% realised
        </Badge>
      </div>
      <div className="mt-3 font-mono text-2xl font-bold text-fg">{gbp(s.npv_gbp)}</div>
      <div className="text-2xs text-muted">NPV (3yr)</div>
      <dl className="mt-3 space-y-1 text-xs">
        <div className="flex justify-between">
          <dt className="text-muted">Risk-adjusted NPV</dt>
          <dd className="font-mono font-semibold text-fg-2">{gbp(s.risk_adjusted_npv_gbp)}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-muted">Payback</dt>
          <dd className="font-mono font-semibold text-fg-2">
            {s.payback_months != null ? `${s.payback_months} mo` : ">36 mo"}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-muted">3-yr ROI</dt>
          <dd className={`font-mono font-semibold ${s.roi_3yr_pct >= 0 ? "text-success" : "text-danger"}`}>
            {s.roi_3yr_pct}%
          </dd>
        </div>
      </dl>
    </div>
  );
}

/** Deterministic 3-year appraisal: operator states costs, the engine computes
    everything with research-calibrated conservative constants. */
export function RoiPanel({ runId, initial }: { runId?: string; initial: RoiReport }) {
  const [r, setR] = useState<RoiReport>(initial);
  const [form, setForm] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      Object.entries(initial.inputs ?? {}).map(([k, v]) => [k, v == null ? "" : String(v)]),
    ),
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function recompute() {
    if (!runId) return;
    setBusy(true);
    setError(null);
    try {
      const inputs: Record<string, unknown> = {};
      for (const f of r.input_fields) {
        const raw = form[f.id];
        if (raw === "" || raw == null) continue;
        inputs[f.id] = f.kind === "number" ? Number(raw) : raw;
      }
      const next = await postRoi(runId, inputs);
      setR(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Computation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* ---- discovery gate banner ---- */}
      <div
        className={`flex items-start gap-2.5 rounded-xl px-4 py-3 text-sm ring-1 ring-inset ${
          r.gate === "pass"
            ? "bg-success/10 text-success ring-success/25"
            : r.gate === "caveated"
              ? "bg-warning/10 text-warning ring-warning/25"
              : "bg-danger/10 text-danger ring-danger/25"
        }`}
        role={r.gate === "blocked" ? "alert" : undefined}
      >
        <ShieldAlert size={15} className="mt-0.5 shrink-0" />
        <span>
          <span className="font-bold">Discovery ROI gate: {r.gate}.</span> {r.gate_note}
        </span>
      </div>

      {/* ---- inputs ---- */}
      <Card
        title="Financial inputs"
        subtitle={r.provenance_note}
        action={
          <Button variant="primary" size="sm" loading={busy} disabled={!runId} onClick={recompute}
            icon={<Calculator size={13} />}>
            Compute appraisal
          </Button>
        }
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {r.input_fields.map((f) => (
            <Field key={f.id} label={`${f.label}${f.required ? " *" : ""}`}>
              {f.kind.startsWith("select:") ? (
                <Select value={form[f.id] ?? ""} disabled={busy || !runId}
                  onChange={(e) => setForm((p) => ({ ...p, [f.id]: e.target.value }))}>
                  <option value="">choose…</option>
                  {f.kind.slice(7).split(",").map((o) => (
                    <option key={o} value={o}>{o.replaceAll("_", " ")}</option>
                  ))}
                </Select>
              ) : (
                <Input type="number" value={form[f.id] ?? ""} disabled={busy || !runId}
                  onChange={(e) => setForm((p) => ({ ...p, [f.id]: e.target.value }))}
                  className="font-mono" />
              )}
            </Field>
          ))}
        </div>
        {r.missing_inputs.length > 0 && (
          <p className="mt-3 text-xs text-muted">
            Required before computing:{" "}
            <span className="font-semibold text-warning">{r.missing_inputs.join(", ")}</span>
          </p>
        )}
        {error && (
          <p className="mt-3 flex items-center gap-1.5 rounded-lg bg-danger/10 px-3 py-2 text-xs text-danger ring-1 ring-inset ring-danger/25" role="alert">
            <TriangleAlert size={13} /> {error}
          </p>
        )}
      </Card>

      {r.computed && r.scenarios && (
        <>
          {/* ---- scenarios ---- */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {(["conservative", "base", "optimistic"] as const).map((k) => (
              <ScenarioCard key={k} name={k} s={r.scenarios![k]} highlight={k === "base"} />
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* ---- benefit register ---- */}
            <Card
              title="Benefit register"
              subtitle={`Cashable ${gbp(r.cashable_annual_gbp)} / capacity ${gbp(r.capacity_annual_gbp)} per steady-state year`}
            >
              <ul className="space-y-2.5">
                {r.benefits!.filter((b) => b.annual_gbp > 0 || b.id === "labour").map((b) => (
                  <li key={b.id} className="rounded-xl border border-line bg-panel-2/30 px-3 py-2.5">
                    <div className="flex items-center gap-2">
                      <Banknote size={14} className={b.convertibility === "cashable" ? "text-success" : "text-warning"} />
                      <span className="min-w-0 flex-1 text-xs font-medium text-fg">{b.label}</span>
                      <span className="font-mono text-sm font-bold text-fg">{gbp(b.annual_gbp)}</span>
                      <Badge tone={b.convertibility === "cashable" ? "success" : "warning"}>
                        {b.convertibility}
                      </Badge>
                    </div>
                    {b.note && <p className="mt-1.5 text-2xs leading-relaxed text-warning">{b.note}</p>}
                  </li>
                ))}
              </ul>
              {r.double_count_warnings!.map((w, i) => (
                <p key={i} className="mt-2 flex items-start gap-1.5 rounded-lg bg-warning/10 px-2.5 py-1.5 text-2xs text-warning">
                  <TriangleAlert size={11} className="mt-0.5 shrink-0" /> {w}
                </p>
              ))}
              <p className="mt-3 flex items-center gap-1.5 border-t border-line-soft pt-2 text-2xs text-muted">
                <Hourglass size={11} /> Cost of delay ≈ {gbp(r.cost_of_delay_gbp_per_month)}/month ·
                risk EV deducted: {gbp(r.risk_ev_gbp)} over 3yr · STP capped at {r.stp_ceiling_pct}% ·
                discount {r.discount_rate_pct}%
              </p>
            </Card>

            {/* ---- TCO ---- */}
            <Card title="3-year TCO decomposition" subtitle="Seven components + calibrated contingency">
              <table className="w-full text-sm">
                <tbody>
                  {Object.entries(TCO_LABELS).map(([k, label]) => (
                    <tr key={k} className="border-b border-line-soft last:border-0">
                      <td className="py-2 text-xs text-fg-2">
                        {label}
                        {k === "contingency" && (
                          <span className="text-muted"> ({r.tco!.contingency_pct}% — {r.category === "ai" ? "AI" : "RPA"})</span>
                        )}
                      </td>
                      <td className="py-2 text-right font-mono text-xs text-fg">{gbp(r.tco![k])}</td>
                    </tr>
                  ))}
                  <tr>
                    <td className="pt-2.5 text-xs font-bold text-fg">Total 3-year TCO</td>
                    <td className="pt-2.5 text-right font-mono text-sm font-bold text-fg">
                      {gbp(r.tco!.total_3yr)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </Card>
          </div>

          <p className="text-2xs italic leading-relaxed text-muted">{r.calibration_note}</p>
        </>
      )}
    </div>
  );
}
