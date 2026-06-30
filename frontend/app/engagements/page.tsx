"use client";

import { useEffect, useState } from "react";
import { FolderKanban, Loader2, AlertTriangle } from "lucide-react";
import { getEngagements } from "@/lib/api";
import { Card } from "@/components/ui/Card";

export default function EngagementsPage() {
  const [data, setData] = useState<{ source: string; engagements: any[] } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getEngagements().then(setData).catch((e) => setErr(e.message));
  }, []);

  return (
    <div className="mx-auto max-w-[1100px] space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight text-fg">Engagements</h1>
          <p className="mt-1 text-[13px] text-muted">Clients and projects, with the number of analysis runs each has.</p>
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
        ) : data && data.engagements.length ? (
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-line text-left text-[12px] text-muted">
                <th className="px-5 py-3 font-medium">Engagement</th>
                <th className="px-5 py-3 font-medium">Client</th>
                <th className="px-5 py-3 font-medium">Process</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 text-right font-medium">Runs</th>
              </tr>
            </thead>
            <tbody>
              {data.engagements.map((e, i) => (
                <tr key={e.id ?? i} className="border-b border-line-soft last:border-0">
                  <td className="px-5 py-3 font-semibold text-fg">
                    <span className="flex items-center gap-2"><FolderKanban size={14} className="text-primary" /> {e.name}</span>
                  </td>
                  <td className="px-5 py-3 text-fg-2">{e.client_name ?? "—"}</td>
                  <td className="px-5 py-3 text-fg-2">{e.process_type ?? "—"}</td>
                  <td className="px-5 py-3">
                    <span className="rounded-full bg-success/12 px-2 py-0.5 text-[11px] font-semibold text-success">{e.status ?? "active"}</span>
                  </td>
                  <td className="px-5 py-3 text-right font-mono font-semibold text-fg">{e.runs ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="p-6 text-[13px] text-muted">No engagements yet. Run an analysis on the Dashboard to create one.</p>
        )}
      </Card>
    </div>
  );
}
