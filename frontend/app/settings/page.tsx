"use client";

import { useEffect, useState } from "react";
import { Cpu, KeyRound, Database, Check, X, Loader2, Sparkles, ShieldCheck } from "lucide-react";
import { getConfig, type AppConfig } from "@/lib/api";
import { useLlm, type Provider } from "@/lib/settings";
import { Card } from "@/components/ui/Card";

const PROVIDERS: { id: Provider; label: string; keyEnv: string }[] = [
  { id: "anthropic", label: "Anthropic (Claude)", keyEnv: "ANTHROPIC_API_KEY" },
  { id: "openai", label: "OpenAI", keyEnv: "OPENAI_API_KEY" },
  { id: "openrouter", label: "OpenRouter", keyEnv: "OPENROUTER_API_KEY" },
];

function KeyBadge({ present }: { present: boolean }) {
  return (
    <span
      className={
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10.5px] font-semibold " +
        (present
          ? "bg-success/12 text-success ring-1 ring-inset ring-success/25"
          : "bg-danger/12 text-danger ring-1 ring-inset ring-danger/25")
      }
    >
      {present ? <Check size={11} /> : <X size={11} />} key {present ? "set" : "missing"}
    </span>
  );
}

export default function SettingsPage() {
  const [cfg, setCfg] = useState<AppConfig | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [llm, setLlm] = useLlm();
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getConfig().then(setCfg).catch((e) => setErr(e.message));
  }, []);

  function update(next: Partial<typeof llm>) {
    setLlm({ ...llm, ...next });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  const providerInfo = cfg?.llm.providers[llm.provider];
  const models = providerInfo?.models ?? [];

  return (
    <div className="mx-auto max-w-[920px] space-y-6">
      <div>
        <h1 className="text-[22px] font-extrabold tracking-tight text-fg">Settings</h1>
        <p className="mt-1 text-[13px] text-muted">
          Choose the model used for brief generation. Selection is saved in this browser and applied to every brief.
        </p>
      </div>

      {err && (
        <div className="rounded-xl bg-danger/10 p-3 text-[13px] text-danger ring-1 ring-inset ring-danger/25">
          Backend unreachable ({err}). Start it with <code className="font-mono">uvicorn backend.api:app --port 8000</code>.
        </div>
      )}

      <Card title="Generation model" subtitle="Provider + model for the AI executive brief"
        action={saved ? <span className="flex items-center gap-1 text-[12px] font-semibold text-success"><Check size={13} /> saved</span> : null}>
        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          {PROVIDERS.map((p) => {
            const info = cfg?.llm.providers[p.id];
            const active = llm.provider === p.id;
            return (
              <button
                key={p.id}
                onClick={() => update({ provider: p.id, model: "" })}
                className={
                  "rounded-xl border p-3 text-left transition-colors " +
                  (active ? "border-primary/50 bg-primary/10" : "border-line bg-panel-2/40 hover:border-line-soft")
                }
              >
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-[13px] font-semibold text-fg">
                    <Cpu size={14} className={active ? "text-primary" : "text-muted"} /> {p.label}
                  </span>
                  {info && <KeyBadge present={info.key_present} />}
                </div>
                <div className="mt-1 font-mono text-[11px] text-muted">{p.keyEnv}</div>
              </button>
            );
          })}
        </div>

        <label className="mb-1 block text-[12px] font-semibold text-fg-2">Model</label>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={models.includes(llm.model) ? llm.model : ""}
            onChange={(e) => update({ model: e.target.value })}
            className="rounded-xl border border-line bg-bg-elev/60 px-3 py-2 text-[13px] text-fg-2 focus:outline-none"
          >
            <option value="">Provider default{providerInfo ? ` (${providerInfo.default_model})` : ""}</option>
            {models.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <input
            value={llm.model}
            onChange={(e) => update({ model: e.target.value })}
            placeholder="or type a custom model id"
            className="min-w-[240px] flex-1 rounded-xl border border-line bg-bg-elev/60 px-3 py-2 font-mono text-[12.5px] text-fg placeholder:text-muted focus:outline-none"
          />
        </div>
        <p className="mt-2 flex items-center gap-1.5 text-[11.5px] text-muted">
          <Sparkles size={12} /> Active: <span className="font-mono text-fg-2">{llm.provider}</span> ·{" "}
          <span className="font-mono text-fg-2">{llm.model || providerInfo?.default_model || "default"}</span>
          {providerInfo && !providerInfo.key_present && (
            <span className="text-danger"> — no API key for this provider, briefs will fail.</span>
          )}
        </p>
      </Card>

      <Card title="Infrastructure" subtitle="Read-only — configured server-side via .env">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="flex items-center justify-between rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
            <span className="flex items-center gap-2 text-[13px] text-fg-2"><KeyRound size={14} className="text-muted" /> Embeddings</span>
            <span className="flex items-center gap-2">
              <span className="font-mono text-[12px] text-fg-2">{cfg?.embeddings.provider ?? "—"}</span>
              {cfg && <KeyBadge present={cfg.embeddings.key_present} />}
            </span>
          </div>
          <div className="flex items-center justify-between rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
            <span className="flex items-center gap-2 text-[13px] text-fg-2"><Database size={14} className="text-muted" /> Supabase</span>
            <span className={"flex items-center gap-1 text-[12px] font-semibold " + (cfg?.supabase.configured ? "text-success" : "text-muted")}>
              {cfg?.supabase.configured ? <><ShieldCheck size={13} /> connected</> : <><Loader2 size={13} className="animate-spin" /> {cfg ? "not configured" : "checking"}</>}
            </span>
          </div>
        </div>
      </Card>
    </div>
  );
}
