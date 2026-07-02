"use client";

import { useEffect, useMemo, useState } from "react";
import { BookMarked, Database, Search, TriangleAlert } from "lucide-react";
import { getKnowledge } from "@/lib/api";
import { Page, PageHeader } from "@/components/ui/Page";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

const SOURCE_LABEL: Record<string, string> = {
  benchmark: "Industry benchmarks",
  methodology: "Methodology",
  client_doc: "Client documents",
};

export default function KnowledgePage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof getKnowledge>> | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [source, setSource] = useState<string | null>(null);

  useEffect(() => {
    getKnowledge().then(setData).catch((e) => setErr(e.message));
  }, []);

  const chunks = useMemo(() => {
    let out = data?.chunks ?? [];
    if (source) out = out.filter((c) => c.source === source);
    const q = query.trim().toLowerCase();
    if (q) out = out.filter((c) => c.title.toLowerCase().includes(q));
    return out;
  }, [data, query, source]);

  return (
    <Page>
      <PageHeader
        title="Knowledge base"
        description="Benchmarks and documents retrieved via pgvector to ground every brief in evidence."
      />

      {err && (
        <div className="flex items-center gap-2 rounded-xl bg-danger/10 p-3 text-sm text-danger ring-1 ring-inset ring-danger/25" role="alert">
          <TriangleAlert size={15} /> Backend unreachable ({err}).
        </div>
      )}

      {!data && !err ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24 w-full" />)}
        </div>
      ) : data && !data.configured ? (
        <Card padded={false}>
          <EmptyState
            icon={<Database size={22} />}
            title="Knowledge store not configured"
            description={
              <>
                Set <code className="font-mono text-fg-2">SUPABASE_URL</code> and{" "}
                <code className="font-mono text-fg-2">SUPABASE_SERVICE_KEY</code>, then run{" "}
                <code className="font-mono text-fg-2">python scripts/ingest_knowledge.py</code>.
              </>
            }
          />
        </Card>
      ) : data ? (
        <>
          {/* source stats double as filters */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <button
              onClick={() => setSource(null)}
              aria-pressed={source === null}
              className={`rounded-2xl border p-4 text-left transition-colors ${
                source === null ? "border-primary/50 bg-primary/10" : "border-line bg-panel/70 hover:border-[#c9cede]"
              }`}
            >
              <div className="font-mono text-2xl font-bold text-fg">{data.total}</div>
              <div className="mt-1 text-xs text-muted">total chunks</div>
            </button>
            {Object.entries(data.by_source).map(([src, n]) => (
              <button
                key={src}
                onClick={() => setSource(source === src ? null : src)}
                aria-pressed={source === src}
                className={`rounded-2xl border p-4 text-left transition-colors ${
                  source === src ? "border-primary/50 bg-primary/10" : "border-line bg-panel/70 hover:border-[#c9cede]"
                }`}
              >
                <div className="font-mono text-2xl font-bold text-fg">{n}</div>
                <div className="mt-1 text-xs text-muted">{SOURCE_LABEL[src] ?? src}</div>
              </button>
            ))}
          </div>

          <Card title="Chunks" subtitle="Retrievable units in the vector store" padded={false}
            action={
              <div className="relative">
                <Search size={13} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Filter…"
                  aria-label="Filter chunks"
                  className="w-[180px] rounded-lg border border-line bg-bg-elev/60 py-1.5 pl-8 pr-3 text-xs text-fg placeholder:text-muted focus:border-primary/60"
                />
              </div>
            }
          >
            {chunks.length ? (
              <ul className="divide-y divide-line-soft">
                {chunks.map((c, i) => (
                  <li key={i} className="flex items-center gap-3 px-5 py-3">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/12 text-primary">
                      {c.source === "client_doc" ? <BookMarked size={15} /> : <Database size={15} />}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-sm text-fg">{c.title}</span>
                    <Badge tone="neutral">{c.source}</Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                icon={<Search size={22} />}
                title={query || source ? "No matching chunks" : "Nothing ingested yet"}
                description={
                  query || source
                    ? "Try a different filter."
                    : <>Run <code className="font-mono text-fg-2">python scripts/ingest_knowledge.py</code> to load benchmarks.</>
                }
              />
            )}
          </Card>
        </>
      ) : null}
    </Page>
  );
}
