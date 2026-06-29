"use client";

import { useState } from "react";
import { ShieldCheck, Lock, Sparkles, Download } from "lucide-react";

function renderMarkdown(md: string) {
  return md.split("\n").map((line, i) => {
    if (line.startsWith("# "))
      return (
        <h3 key={i} className="mb-2 text-[16px] font-bold text-fg">
          {line.slice(2)}
        </h3>
      );
    if (line.startsWith("## "))
      return (
        <h4 key={i} className="mt-4 mb-1 text-[13px] font-bold uppercase tracking-wide text-primary">
          {line.slice(3)}
        </h4>
      );
    if (line.trim() === "") return <div key={i} className="h-1" />;
    return (
      <p key={i} className="text-[13px] leading-relaxed text-fg-2">
        {line}
      </p>
    );
  });
}

export function BriefPanel({ clientBrief }: { clientBrief: string }) {
  const [audience, setAudience] = useState<"internal" | "client">("client");

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-violet/15 text-violet">
            <Sparkles size={16} />
          </span>
          <div>
            <h2 className="text-[14px] font-bold text-fg">AI executive brief</h2>
            <p className="text-[11.5px] text-muted">claude-opus-4-8 · BABOK-shaped</p>
          </div>
        </div>
        <div className="flex items-center gap-1 rounded-xl border border-line bg-bg-elev/60 p-1">
          {(["internal", "client"] as const).map((a) => (
            <button
              key={a}
              onClick={() => setAudience(a)}
              className={
                "rounded-lg px-3 py-1.5 text-[12px] font-semibold capitalize transition-colors " +
                (audience === a ? "bg-primary-strong text-white" : "text-fg-2 hover:text-fg")
              }
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      {audience === "client" ? (
        <span className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-success/12 px-2.5 py-1 text-[11px] font-semibold text-success ring-1 ring-inset ring-success/25">
          <ShieldCheck size={12} /> Client-safe — engine details stripped
        </span>
      ) : (
        <span className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-warning/12 px-2.5 py-1 text-[11px] font-semibold text-warning ring-1 ring-inset ring-warning/25">
          <Lock size={12} /> Internal — includes mining mechanics
        </span>
      )}

      <div className="max-h-[420px] overflow-y-auto rounded-xl border border-line bg-bg-elev/40 p-5">
        {audience === "client" ? (
          renderMarkdown(clientBrief)
        ) : (
          <div className="space-y-2 text-[13px] leading-relaxed text-fg-2">
            <p className="text-fg">
              <span className="font-semibold">Internal view</span> adds the full mechanics the
              client never sees:
            </p>
            <ul className="ml-4 list-disc space-y-1 font-mono text-[12.5px]">
              <li>algorithm: inductive miner</li>
              <li>fitness 1.000 · alignment 1.000</li>
              <li>precision 0.971 · generalization 0.823 · simplicity 0.895</li>
              <li>bottleneck Approve PO → Receive Invoice 52.9h (n=11)</li>
              <li>rework Approve PO ×7 · 3 variants / 60 cases</li>
            </ul>
            <p className="pt-2 text-muted">
              Switch to <span className="font-semibold text-success">Client</span> to see the
              same findings in business language with all of this removed.
            </p>
          </div>
        )}
      </div>

      <div className="mt-4 flex gap-2">
        <button className="flex items-center gap-1.5 rounded-xl bg-primary-strong px-3.5 py-2 text-[12.5px] font-semibold text-white hover:bg-primary">
          <Sparkles size={14} /> Regenerate
        </button>
        <button className="flex items-center gap-1.5 rounded-xl border border-line bg-panel/60 px-3.5 py-2 text-[12.5px] font-semibold text-fg-2 hover:text-fg">
          <Download size={14} /> Export PDF
        </button>
      </div>
    </div>
  );
}
