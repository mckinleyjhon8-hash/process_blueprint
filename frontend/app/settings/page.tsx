"use client";

import { useEffect, useState } from "react";
import { Check, Cpu, Database, KeyRound, ShieldCheck, Sparkles, Workflow, X } from "lucide-react";
import { getConfig, type AppConfig } from "@/lib/api";
import { useLlm, type Provider } from "@/lib/settings";
import { Page, PageHeader } from "@/components/ui/Page";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Field, Input, Select } from "@/components/ui/Field";

const PROVIDERS: { id: Provider; label: string; keyEnv: string }[] = [
  { id: "anthropic", label: "Anthropic (Claude)", keyEnv: "ANTHROPIC_API_KEY" },
  { id: "openai", label: "OpenAI", keyEnv: "OPENAI_API_KEY" },
  { id: "openrouter", label: "OpenRouter", keyEnv: "OPENROUTER_API_KEY" },
];

function KeyBadge({ present }: { present: boolean }) {
  return (
    <Badge tone={present ? "success" : "danger"}>
      {present ? <Check size={11} /> : <X size={11} />} key {present ? "set" : "missing"}
    </Badge>
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
    <Page width="narrow">
      <PageHeader
        title="Settings"
        description="Choose the model used for brief generation. Saved in this browser and applied to every brief."
      />

      {err && (
        <div className="rounded-xl bg-danger/10 p-3 text-sm text-danger ring-1 ring-inset ring-danger/25" role="alert">
          Backend unreachable ({err}). Start it with{" "}
          <code className="font-mono">uvicorn backend.api:app --port 8000</code>.
        </div>
      )}

      <Card
        title="Generation model"
        subtitle="Provider + model for the AI executive brief"
        action={
          saved ? (
            <span className="fade-in flex items-center gap-1 text-xs font-semibold text-success">
              <Check size={13} /> saved
            </span>
          ) : null
        }
      >
        <div className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-3" role="radiogroup" aria-label="Provider">
          {PROVIDERS.map((p) => {
            const info = cfg?.llm.providers[p.id];
            const active = llm.provider === p.id;
            return (
              <button
                key={p.id}
                role="radio"
                aria-checked={active}
                onClick={() => update({ provider: p.id, model: "" })}
                className={
                  "rounded-xl border p-3 text-left transition-colors duration-[var(--duration-fast)] " +
                  (active ? "border-primary/50 bg-primary/10" : "border-line bg-panel-2/40 hover:border-[#c9cede]")
                }
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-1.5 text-sm font-semibold text-fg">
                    <Cpu size={14} className={active ? "text-primary" : "text-muted"} /> {p.label}
                  </span>
                  {info && <KeyBadge present={info.key_present} />}
                </div>
                <div className="mt-1 font-mono text-2xs text-muted">{p.keyEnv}</div>
              </button>
            );
          })}
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Suggested models">
            <Select
              value={models.includes(llm.model) ? llm.model : ""}
              onChange={(e) => update({ model: e.target.value })}
            >
              <option value="">Provider default{providerInfo ? ` (${providerInfo.default_model})` : ""}</option>
              {models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </Select>
          </Field>
          <Field label="Custom model id" helper="Overrides the selection — any id the provider accepts.">
            <Input
              value={llm.model}
              onChange={(e) => update({ model: e.target.value })}
              placeholder="e.g. claude-opus-4-8"
              className="font-mono"
            />
          </Field>
        </div>

        <p className="mt-4 flex flex-wrap items-center gap-1.5 text-2xs text-muted">
          <Sparkles size={12} /> Active:{" "}
          <span className="font-mono text-fg-2">{llm.provider}</span> ·{" "}
          <span className="font-mono text-fg-2">{llm.model || providerInfo?.default_model || "default"}</span>
          {providerInfo && !providerInfo.key_present && (
            <span className="font-semibold text-danger"> — no API key for this provider, briefs will fail.</span>
          )}
        </p>
      </Card>

      <Card title="Infrastructure" subtitle="Read-only — configured server-side via .env">
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <li className="flex items-center justify-between rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
            <span className="flex items-center gap-2 text-sm text-fg-2">
              <KeyRound size={14} className="text-muted" /> Embeddings
            </span>
            <span className="flex items-center gap-2">
              <span className="font-mono text-xs text-fg-2">{cfg?.embeddings.provider ?? "—"}</span>
              {cfg && <KeyBadge present={cfg.embeddings.key_present} />}
            </span>
          </li>
          <li className="flex items-center justify-between rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
            <span className="flex items-center gap-2 text-sm text-fg-2">
              <Database size={14} className="text-muted" /> Supabase
            </span>
            {cfg?.supabase.configured ? (
              <Badge tone="success"><ShieldCheck size={11} /> connected</Badge>
            ) : (
              <Badge tone="neutral">{cfg ? "not configured" : "checking…"}</Badge>
            )}
          </li>
          <li className="flex items-center justify-between rounded-xl border border-line bg-panel-2/40 px-3 py-2.5">
            <span className="flex items-center gap-2 text-sm text-fg-2">
              <Workflow size={14} className="text-muted" /> Petri-net render
            </span>
            {cfg?.render?.graphviz ? (
              <Badge tone="success">graphviz ready</Badge>
            ) : (
              <Badge tone="neutral">dependency-graph fallback</Badge>
            )}
          </li>
        </ul>
      </Card>
    </Page>
  );
}
