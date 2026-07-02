"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink, FileText, Map, Play, TriangleAlert } from "lucide-react";
import { getRuns, reportUrl, type RunSummary } from "@/lib/api";
import { fmtDate, fmtInt, fmtRatio } from "@/lib/format";
import { Page, PageHeader } from "@/components/ui/Page";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";

const COLUMNS: Column<RunSummary>[] = [
  {
    id: "process",
    header: "Process",
    sortValue: (r) => r.process_type,
    cell: (r) =>
      r.run_id ? (
        <Link
          href={`/runs/${r.run_id}`}
          className="flex items-center gap-2 font-semibold text-fg transition-colors hover:text-primary"
        >
          <FileText size={14} className="shrink-0 text-primary" />
          {r.process_type ?? "—"}
        </Link>
      ) : (
        <span className="flex items-center gap-2 font-semibold text-fg">
          <FileText size={14} className="shrink-0 text-muted" />
          {r.process_type ?? "—"}
        </span>
      ),
  },
  {
    id: "created",
    header: "When",
    sortValue: (r) => r.created_at,
    cell: (r) => <span className="whitespace-nowrap text-fg-2">{fmtDate(r.created_at)}</span>,
  },
  {
    id: "cases",
    header: "Cases",
    align: "right",
    sortValue: (r) => r.n_cases,
    cell: (r) => <span className="font-mono text-fg-2">{fmtInt(r.n_cases)}</span>,
  },
  {
    id: "variants",
    header: "Variants",
    align: "right",
    sortValue: (r) => r.n_variants,
    cell: (r) => <span className="font-mono text-fg-2">{fmtInt(r.n_variants)}</span>,
  },
  {
    id: "fitness",
    header: "Fitness",
    align: "right",
    sortValue: (r) => r.model_fitness,
    cell: (r) => <span className="font-mono text-fg-2">{fmtRatio(r.model_fitness)}</span>,
  },
  {
    id: "precision",
    header: "Precision",
    align: "right",
    sortValue: (r) => r.model_precision,
    cell: (r) => <span className="font-mono text-fg-2">{fmtRatio(r.model_precision)}</span>,
  },
  {
    id: "actions",
    header: "Open",
    align: "right",
    cell: (r) =>
      r.run_id ? (
        <span className="flex items-center justify-end gap-3">
          <Link
            href={`/runs/${r.run_id}/map`}
            className="inline-flex items-center gap-1 text-xs font-semibold text-fg-2 transition-colors hover:text-fg"
          >
            <Map size={12} /> map
          </Link>
          <a
            href={reportUrl(r.run_id, "internal")}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
          >
            <ExternalLink size={12} /> report
          </a>
        </span>
      ) : (
        <span className="text-2xs text-muted">—</span>
      ),
  },
];

export default function RunsPage() {
  const [data, setData] = useState<{ source: string; runs: RunSummary[] } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getRuns().then(setData).catch((e) => setErr(e.message));
  }, []);

  return (
    <Page>
      <PageHeader
        title="Runs & briefs"
        description="Every analysis recorded by the engine — open a run for its full workspace."
        actions={data && <Badge tone="neutral">source: {data.source}</Badge>}
      />

      {err && (
        <div className="flex items-center gap-2 rounded-xl bg-danger/10 p-3 text-sm text-danger ring-1 ring-inset ring-danger/25" role="alert">
          <TriangleAlert size={15} /> Backend unreachable ({err}).
        </div>
      )}

      <Card padded={false}>
        <DataTable
          columns={COLUMNS}
          rows={data?.runs ?? []}
          rowKey={(r, i) => r.run_id ?? String(i)}
          loading={!data && !err}
          searchPlaceholder="Filter runs…"
          searchText={(r) => `${r.process_type ?? ""} ${r.run_id ?? ""}`}
          initialSort={{ id: "created", dir: "desc" }}
          empty={
            <EmptyState
              icon={<Play size={22} />}
              title="No runs yet"
              description="Analyse an event log from the dashboard — every run lands here with its workspace, map and report."
              action={
                <Link href="/?focus=new" className="text-sm font-semibold text-primary hover:underline">
                  Start an analysis →
                </Link>
              }
            />
          }
        />
      </Card>
    </Page>
  );
}
