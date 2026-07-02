"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard,
  FolderKanban,
  FileText,
  Database,
  Settings,
  Search,
  Play,
  Map,
  CornerDownLeft,
} from "lucide-react";
import { getRuns, type RunSummary } from "@/lib/api";
import { Kbd } from "@/components/ui/Kbd";

interface Item {
  id: string;
  label: string;
  hint?: string;
  group: "Navigate" | "Actions" | "Recent runs";
  icon: React.ReactNode;
  keywords: string;
  run: () => void;
}

/** Global ⌘K / Ctrl+K palette: navigate, act, jump to recent runs. */
export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  // Open with Ctrl/Cmd+K anywhere.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Reset + focus + lazily fetch recent runs each time it opens.
  useEffect(() => {
    if (!open) return;
    setQuery("");
    setCursor(0);
    const t = setTimeout(() => inputRef.current?.focus(), 10);
    getRuns()
      .then((d) => setRuns((d.runs || []).filter((r) => r.run_id).slice(0, 5)))
      .catch(() => setRuns([]));
    return () => clearTimeout(t);
  }, [open]);

  const go = useCallback(
    (href: string) => {
      setOpen(false);
      router.push(href);
    },
    [router],
  );

  const items = useMemo<Item[]>(() => {
    const nav: Item[] = [
      { id: "nav-dash", label: "Dashboard", group: "Navigate", icon: <LayoutDashboard size={15} />, keywords: "home overview dashboard", run: () => go("/") },
      { id: "nav-eng", label: "Engagements", group: "Navigate", icon: <FolderKanban size={15} />, keywords: "clients projects engagements", run: () => go("/engagements") },
      { id: "nav-runs", label: "Runs & briefs", group: "Navigate", icon: <FileText size={15} />, keywords: "runs briefs analyses reports", run: () => go("/runs") },
      { id: "nav-knw", label: "Knowledge", group: "Navigate", icon: <Database size={15} />, keywords: "knowledge benchmarks evidence pgvector", run: () => go("/knowledge") },
      { id: "nav-set", label: "Settings", group: "Navigate", icon: <Settings size={15} />, keywords: "settings model provider admin", run: () => go("/settings") },
    ];
    const actions: Item[] = [
      { id: "act-new", label: "New analysis", hint: "upload or sample", group: "Actions", icon: <Play size={15} />, keywords: "new analysis upload log mine sample", run: () => go("/?focus=new") },
    ];
    const recent: Item[] = runs.map((r) => ({
      id: `run-${r.run_id}`,
      label: `${r.process_type ?? "Run"} · ${r.n_cases ?? "?"} cases`,
      hint: r.run_id!.slice(0, 8),
      group: "Recent runs" as const,
      icon: <Map size={15} />,
      keywords: `run ${r.process_type ?? ""} ${r.run_id}`,
      run: () => go(`/runs/${r.run_id}`),
    }));
    return [...nav, ...actions, ...recent];
  }, [go, runs]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (i) => i.label.toLowerCase().includes(q) || i.keywords.toLowerCase().includes(q),
    );
  }, [items, query]);

  useEffect(() => setCursor(0), [filtered.length]);

  if (!open) return null;

  const groups = ["Navigate", "Actions", "Recent runs"] as const;
  let flat = -1; // running index across groups for cursor mapping

  return (
    <div
      className="fixed inset-0 z-[60] flex items-start justify-center px-4 pt-[12vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div className="fade-in absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setOpen(false)} />
      <div className="pop relative w-full max-w-[560px] overflow-hidden rounded-2xl border border-line bg-bg-elev shadow-[var(--elev-2)]">
        <div className="flex items-center gap-2.5 border-b border-line px-4">
          <Search size={16} className="shrink-0 text-muted" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setCursor((c) => Math.min(c + 1, filtered.length - 1));
              }
              if (e.key === "ArrowUp") {
                e.preventDefault();
                setCursor((c) => Math.max(c - 1, 0));
              }
              if (e.key === "Enter") filtered[cursor]?.run();
            }}
            placeholder="Search pages, actions, runs…"
            aria-label="Search commands"
            className="w-full bg-transparent py-3.5 text-sm text-fg placeholder:text-muted focus:outline-none"
          />
          <Kbd>esc</Kbd>
        </div>

        <div className="max-h-[46vh] overflow-y-auto p-2" role="listbox">
          {filtered.length === 0 && (
            <p className="px-3 py-8 text-center text-sm text-muted">No results for “{query}”.</p>
          )}
          {groups.map((g) => {
            const inGroup = filtered.filter((i) => i.group === g);
            if (!inGroup.length) return null;
            return (
              <div key={g} className="mb-1">
                <div className="px-3 pb-1 pt-2 text-2xs font-bold uppercase tracking-[0.08em] text-muted/80">
                  {g}
                </div>
                {inGroup.map((item) => {
                  flat += 1;
                  const idx = flat;
                  const active = idx === cursor;
                  return (
                    <button
                      key={item.id}
                      role="option"
                      aria-selected={active}
                      onMouseEnter={() => setCursor(idx)}
                      onClick={item.run}
                      className={
                        "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-colors duration-[var(--duration-fast)] " +
                        (active ? "bg-primary/10 text-fg" : "text-fg-2")
                      }
                    >
                      <span className={active ? "text-primary" : "text-muted"}>{item.icon}</span>
                      <span className="flex-1 truncate font-medium">{item.label}</span>
                      {item.hint && <span className="font-mono text-2xs text-muted">{item.hint}</span>}
                      {active && <CornerDownLeft size={13} className="text-muted" />}
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
