"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  FolderKanban,
  FileText,
  Database,
  Settings,
  Workflow,
  ShieldCheck,
  X,
  Menu,
} from "lucide-react";

export const NAV_SECTIONS = [
  {
    label: "Overview",
    items: [{ href: "/", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Workspace",
    items: [
      { href: "/engagements", label: "Engagements", icon: FolderKanban },
      { href: "/runs", label: "Runs & briefs", icon: FileText },
      { href: "/knowledge", label: "Knowledge", icon: Database },
    ],
  },
  {
    label: "System",
    items: [{ href: "/settings", label: "Settings", icon: Settings }],
  },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Primary" className="flex flex-1 flex-col gap-5 overflow-y-auto">
      {NAV_SECTIONS.map((section) => (
        <div key={section.label}>
          <div className="px-3 pb-1.5 text-2xs font-bold uppercase tracking-[0.08em] text-muted/80">
            {section.label}
          </div>
          <div className="flex flex-col gap-0.5">
            {section.items.map(({ href, label, icon: Icon }) => {
              const active = isActive(pathname, href);
              return (
                <Link
                  key={href}
                  href={href}
                  onClick={onNavigate}
                  aria-current={active ? "page" : undefined}
                  className={
                    "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold transition-colors duration-[var(--duration-fast)] " +
                    (active
                      ? "bg-primary/10 text-primary ring-1 ring-inset ring-primary/20"
                      : "text-fg-2 hover:bg-panel-2 hover:text-fg")
                  }
                >
                  <Icon
                    size={17}
                    className={active ? "text-primary" : "text-muted group-hover:text-fg-2"}
                  />
                  {label}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

function Brand() {
  return (
    <Link href="/" className="flex items-center gap-3 px-2 pb-6">
      <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary-strong text-white shadow-[var(--elev-glow)]">
        <Workflow size={18} strokeWidth={2.4} />
      </div>
      <div className="leading-tight">
        <div className="text-[15px] font-bold text-fg">Process Blueprint</div>
        <div className="text-2xs font-medium text-muted">Consulting intelligence</div>
      </div>
    </Link>
  );
}

function InternalNote() {
  return (
    <div className="mt-auto rounded-xl border border-line bg-panel-2/50 p-3">
      <div className="flex items-center gap-2 text-xs font-semibold text-fg">
        <ShieldCheck size={15} className="text-success" />
        Internal tool
      </div>
      <p className="mt-1 text-2xs leading-relaxed text-muted">
        Clients receive reports only — never access to the engine.
      </p>
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-screen w-[248px] shrink-0 flex-col border-r border-line bg-bg-elev/70 px-4 py-5 backdrop-blur-xl lg:flex">
      <Brand />
      <NavList />
      <InternalNote />
    </aside>
  );
}

/** Mobile: hamburger in the topbar opens a slide-in drawer with the same nav. */
export function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  // Close on route change + Escape; lock scroll while open.
  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label="Open navigation"
        className="grid h-9 w-9 place-items-center rounded-xl border border-line bg-panel/60 text-fg-2 hover:text-fg lg:hidden"
      >
        <Menu size={17} />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <div className="fade-in absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setOpen(false)} />
          <div className="pop absolute inset-y-0 left-0 flex w-[280px] flex-col border-r border-line bg-bg-elev px-4 py-5">
            <div className="flex items-start justify-between">
              <Brand />
              <button
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
                className="grid h-8 w-8 place-items-center rounded-lg text-muted hover:text-fg"
              >
                <X size={16} />
              </button>
            </div>
            <NavList onNavigate={() => setOpen(false)} />
            <InternalNote />
          </div>
        </div>
      )}
    </>
  );
}
