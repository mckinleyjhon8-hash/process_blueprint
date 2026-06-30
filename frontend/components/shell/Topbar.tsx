"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, ChevronDown, Sparkles } from "lucide-react";
import { apiHealth } from "@/lib/api";

const TITLES: Record<string, { title: string; sub: string }> = {
  "/": { title: "Dashboard", sub: "Mine a log, generate the brief, export the report" },
  "/engagements": { title: "Engagements", sub: "Clients, projects and their analysis runs" },
  "/briefs": { title: "Briefs & runs", sub: "Every analysis recorded by the engine" },
  "/knowledge": { title: "Knowledge", sub: "Benchmarks and documents grounding the briefs" },
  "/settings": { title: "Settings", sub: "Models, providers and infrastructure" },
};

export function Topbar() {
  const pathname = usePathname();
  const meta = TITLES[pathname] ?? TITLES["/"];
  const [online, setOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;
    apiHealth().then((ok) => alive && setOnline(ok));
    const t = setInterval(() => apiHealth().then((ok) => alive && setOnline(ok)), 15000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b border-line bg-bg/70 px-6 backdrop-blur-xl lg:px-8">
      <div>
        <h1 className="text-[15px] font-bold leading-none text-fg">{meta.title}</h1>
        <p className="mt-1 text-[11.5px] text-muted">{meta.sub}</p>
      </div>

      <div className="ml-auto flex items-center gap-3">
        <span
          className={
            "hidden items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold sm:flex " +
            (online
              ? "border-success/30 bg-success/10 text-success"
              : online === false
                ? "border-danger/30 bg-danger/10 text-danger"
                : "border-line bg-panel/60 text-muted")
          }
        >
          <span
            className={
              "h-1.5 w-1.5 rounded-full " +
              (online ? "bg-success" : online === false ? "bg-danger" : "bg-muted")
            }
          />
          {online ? "engine online" : online === false ? "engine offline" : "checking…"}
        </span>
        <Link
          href="/"
          className="flex items-center gap-1.5 rounded-xl bg-primary-strong px-3 py-2 text-[12.5px] font-semibold text-white transition-colors hover:bg-primary"
        >
          <Sparkles size={14} /> New analysis
        </Link>
        <button className="grid h-9 w-9 place-items-center rounded-xl border border-line bg-panel/60 text-fg-2 hover:text-fg">
          <Bell size={16} />
        </button>
        <button className="flex items-center gap-2 rounded-xl border border-line bg-panel/60 py-1 pl-1 pr-2">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-violet/20 text-[11px] font-bold text-violet">
            JM
          </span>
          <ChevronDown size={14} className="text-muted" />
        </button>
      </div>
    </header>
  );
}
