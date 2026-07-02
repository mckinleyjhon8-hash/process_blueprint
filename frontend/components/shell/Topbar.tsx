"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, Search, Sparkles } from "lucide-react";
import { apiHealth } from "@/lib/api";
import { StatusDot } from "@/components/ui/Badge";
import { Kbd } from "@/components/ui/Kbd";
import { MobileNav } from "./Sidebar";

const SEGMENT_LABELS: Record<string, string> = {
  engagements: "Engagements",
  runs: "Runs & briefs",
  knowledge: "Knowledge",
  settings: "Settings",
  map: "Map Studio",
};

/** Breadcrumbs derived from the URL — works for dynamic routes too. */
function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  const crumbs = [{ href: "/", label: "Dashboard" }];
  let acc = "";
  for (const seg of segments) {
    acc += `/${seg}`;
    const label =
      SEGMENT_LABELS[seg] ?? (seg.length > 10 ? `${seg.slice(0, 8)}…` : seg); // run ids get shortened
    crumbs.push({ href: acc, label });
  }

  return (
    <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1.5 text-sm">
      {crumbs.map((c, i) => {
        const last = i === crumbs.length - 1;
        return (
          <span key={c.href} className="flex min-w-0 items-center gap-1.5">
            {i > 0 && <ChevronRight size={13} className="shrink-0 text-muted/60" />}
            {last ? (
              <span aria-current="page" className="truncate font-bold text-fg">
                {c.label}
              </span>
            ) : (
              <Link href={c.href} className="truncate font-medium text-muted transition-colors hover:text-fg-2">
                {c.label}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}

function EngineStatus() {
  const [online, setOnline] = useState<boolean | null>(null);
  useEffect(() => {
    let alive = true;
    const check = () => apiHealth().then((ok) => alive && setOnline(ok));
    check();
    const t = setInterval(check, 15000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);
  return (
    <span className="hidden sm:block">
      {online == null ? (
        <StatusDot tone="neutral" label="checking…" />
      ) : online ? (
        <StatusDot tone="success" label="engine online" />
      ) : (
        <StatusDot tone="danger" label="engine offline" pulse />
      )}
    </span>
  );
}

export function Topbar() {
  return (
    <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center gap-3 border-b border-line bg-bg-elev/80 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
      <MobileNav />
      <Breadcrumbs />

      <div className="ml-auto flex items-center gap-2.5">
        <button
          onClick={() => {
            // synthesize the palette hotkey so there is exactly one open-path
            window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }));
          }}
          className="hidden items-center gap-2 rounded-xl border border-line bg-panel/60 px-3 py-2 text-xs font-medium text-muted transition-colors hover:text-fg-2 md:flex"
          aria-label="Open command palette"
        >
          <Search size={13} />
          Search
          <Kbd>Ctrl K</Kbd>
        </button>

        <EngineStatus />

        <Link
          href="/?focus=new"
          className="flex items-center gap-1.5 rounded-xl bg-primary-strong px-3 py-2 text-xs font-semibold text-white shadow-[var(--elev-glow)] transition-colors hover:bg-primary"
        >
          <Sparkles size={14} /> New analysis
        </Link>
      </div>
    </header>
  );
}
