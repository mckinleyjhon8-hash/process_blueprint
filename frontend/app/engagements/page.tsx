"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FolderKanban, TriangleAlert } from "lucide-react";
import { getEngagements, type Engagement } from "@/lib/api";
import { Page, PageHeader } from "@/components/ui/Page";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";

const COLUMNS: Column<Engagement>[] = [
  {
    id: "name",
    header: "Engagement",
    sortValue: (e) => e.name,
    cell: (e) => (
      <span className="flex items-center gap-2 font-semibold text-fg">
        <FolderKanban size={14} className="shrink-0 text-primary" /> {e.name}
      </span>
    ),
  },
  {
    id: "client",
    header: "Client",
    sortValue: (e) => e.client_name ?? null,
    cell: (e) => <span className="text-fg-2">{e.client_name ?? "—"}</span>,
  },
  {
    id: "process",
    header: "Process",
    sortValue: (e) => e.process_type ?? null,
    cell: (e) => <span className="text-fg-2">{e.process_type ?? "—"}</span>,
  },
  {
    id: "status",
    header: "Status",
    sortValue: (e) => e.status ?? "active",
    cell: (e) => <Badge tone={e.status === "closed" ? "neutral" : "success"}>{e.status ?? "active"}</Badge>,
  },
  {
    id: "runs",
    header: "Runs",
    align: "right",
    sortValue: (e) => e.runs ?? 0,
    cell: (e) => <span className="font-mono font-semibold text-fg">{e.runs ?? 0}</span>,
  },
];

export default function EngagementsPage() {
  const [data, setData] = useState<{ source: string; engagements: Engagement[] } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getEngagements().then(setData).catch((e) => setErr(e.message));
  }, []);

  return (
    <Page>
      <PageHeader
        title="Engagements"
        description="Clients and projects, with the analysis runs recorded for each."
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
          rows={data?.engagements ?? []}
          rowKey={(e, i) => e.id ?? String(i)}
          loading={!data && !err}
          searchPlaceholder="Filter engagements…"
          searchText={(e) => `${e.name} ${e.client_name ?? ""} ${e.process_type ?? ""}`}
          empty={
            <EmptyState
              icon={<FolderKanban size={22} />}
              title="No engagements yet"
              description="Analysing a log creates the client and engagement automatically when Supabase is configured."
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
