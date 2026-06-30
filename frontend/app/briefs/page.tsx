"use client";

import { useEffect, useState } from "react";
import { FileText, Loader2, AlertTriangle, ExternalLink } from "lucide-react";
import { getRuns, reportUrl } from "@/lib/api";
import { Card } from "@/components/ui/Card";

export default function BriefsPage() {
  const [data, setData] = useState<{ source: string; runs: any[] } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getRuns().then(setData).catch((e) => setErr(e.message));
  }, []);

  return (
    <div className="mx-auto max-w-[1100px] space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight text-fg">Briefs &amp; runs</h1>
          <p className="mt-1 text-[13px] text-muted">Every analysis the engine has recorded. Open a report for runs from this session.</p>
        </div>
        {data && (
          <span className="rounded-full bg-panel-2/60 px-2.5 py-1 text-[11px] font-semibold text-muted ring-1 ring-inset ring-line">
            source: {data.source}
          </span>
        )}
      </div>

      {err && (
        <div className="flex items-center gap-2 rounded-xl bg-danger/10 p-3 text-[13px] text-danger ring-1 ring-inset ring-danger/25">
          <AlertTriangle size={15} /> Backend unreachable ({err}).
        </div>
      )}

      <Card className="p-0">
        {!data && !err ? (
          <div className="flex items-center gap-2 p-6 text-[13px] text-muted"><Loader2 size={16} className="animate-spin text-primary" /> Loading…</div>
        ) : data && data.runs.length ? (
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-line text-left text-[12px] text-muted">
                <th className="px-5 py-3 font-medium">Process</th>
                <th className="px-5 py-3 text-right font-medium">Cases</th>
                <th className="px-5 py-3 text-right font-medium">Variants</th>
                <th className="px-5 py-3 text-right font-medium">Fitness</th>
                <th className="px-5 py-3 text-right font-medium">Precision</th>
                <th className="px-5 py-3 text-right font-medium">Report</th>
              </tr>
            </thead>
            <tbody>
              {data.runs.map((r, i) => (
                <tr key={r.run_id ?? i} className="border-b border-line-soft last:border-0">
                  <td className="px-5 py-3 font-semibold text-fg">
                    <span className="flex items-center gap-2"><FileText size={14} className="text-primary" /> {r.process_type ?? "—"}</span>
                  </td>
                  <td className="px-5 py-3 text-right font-mono text-fg-2">{(r.n_cases ?? 0).toLocaleString()}</td>
                  <td className="px-5 py-3 text-right font-mono text-fg-2">{r.n_variants ?? "—"}</td>
                  <td className="px-5 py-3 text-right font-mono text-fg-2">{r.model_fitness != null ? Number(r.model_fitness).toFixed(2) : "—"}</td>
                  <td className="px-5 py-3 text-right font-mono text-fg-2">{r.model_precision != null ? Number(r.model_precision).toFixed(2) : "—"}</td>
                  <td className="px-5 py-3 text-right">
                    {data.source === "memory" && r.run_id ? (
                      <a href={reportUrl(r.run_id, "internal")} target="_blank" rel="noreferrer"
                        className="inline-flex items-center gap-1 text-[12px] font-semibold text-primary hover:underline">
                        <ExternalLink size={12} /> open
                      </a>
                    ) : (
                      <span className="text-[11px] text-muted">archived</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="p-6 text-[13px] text-muted">No runs yet. Analyse a log on the Dashboard.</p>
        )}
      </Card>
    </div>
  );
}
