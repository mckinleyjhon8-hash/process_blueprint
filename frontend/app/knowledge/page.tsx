"use client";

import { useEffect, useState } from "react";
import { Database, Loader2, AlertTriangle, BookMarked } from "lucide-react";
import { getKnowledge } from "@/lib/api";
import { Card } from "@/components/ui/Card";

const SOURCE_LABEL: Record<string, string> = {
  benchmark: "Industry benchmarks",
  methodology: "Methodology",
  client_doc: "Client documents",
};

export default function KnowledgePage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof getKnowledge>> | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getKnowledge().then(setData).catch((e) => setErr(e.message));
  }, []);

  return (
    <div className="mx-auto max-w-[1000px] space-y-6">
      <div>
        <h1 className="text-[22px] font-extrabold tracking-tight text-fg">Knowledge base</h1>
        <p className="mt-1 text-[13px] text-muted">
          Benchmarks and documents retrieved via pgvector to ground each brief.
        </p>
      </div>

      {err && (
        <div className="flex items-center gap-2 rounded-xl bg-danger/10 p-3 text-[13px] text-danger ring-1 ring-inset ring-danger/25">
          <AlertTriangle size={15} /> Backend unreachable ({err}).
        </div>
      )}

      {!data && !err ? (
        <Card><div className="flex items-center gap-2 text-[13px] text-muted"><Loader2 size={16} className="animate-spin text-primary" /> Loading…</div></Card>
      ) : data && !data.configured ? (
        <Card>
          <p className="text-[13px] text-muted">
            Supabase is not configured, so the knowledge store is unavailable. Set <code className="font-mono">SUPABASE_URL</code> and{" "}
            <code className="font-mono">SUPABASE_SERVICE_KEY</code>, then run <code className="font-mono">python scripts/ingest_knowledge.py</code>.
          </p>
        </Card>
      ) : data ? (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-2xl border border-line bg-panel/70 p-4">
              <div className="font-mono text-[26px] font-bold text-fg">{data.total}</div>
              <div className="mt-1 text-[12px] text-muted">total chunks</div>
            </div>
            {Object.entries(data.by_source).map(([src, n]) => (
              <div key={src} className="rounded-2xl border border-line bg-panel/70 p-4">
                <div className="font-mono text-[26px] font-bold text-fg">{n}</div>
                <div className="mt-1 text-[12px] text-muted">{SOURCE_LABEL[src] ?? src}</div>
              </div>
            ))}
          </div>

          <Card title="Chunks" subtitle="Retrievable units in the vector store" className="p-0">
            {data.chunks.length ? (
              <div className="divide-y divide-line-soft">
                {data.chunks.map((c, i) => (
                  <div key={i} className="flex items-center gap-3 px-5 py-3">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/12 text-primary">
                      {c.source === "client_doc" ? <BookMarked size={15} /> : <Database size={15} />}
                    </span>
                    <span className="text-[13px] text-fg">{c.title}</span>
                    <span className="ml-auto rounded-full bg-panel-2/60 px-2 py-0.5 text-[11px] text-muted">{c.source}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="p-6 text-[13px] text-muted">No chunks ingested yet. Run <code className="font-mono">python scripts/ingest_knowledge.py</code>.</p>
            )}
          </Card>
        </>
      ) : null}
    </div>
  );
}
