import {
  LayoutDashboard,
  FolderKanban,
  Database,
  FileText,
  Workflow,
  Settings,
  ShieldCheck,
} from "lucide-react";

const NAV = [
  { icon: LayoutDashboard, label: "Dashboard", active: true },
  { icon: FolderKanban, label: "Engagements" },
  { icon: Workflow, label: "Process map" },
  { icon: FileText, label: "Briefs" },
  { icon: Database, label: "Knowledge" },
  { icon: Settings, label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-screen w-[248px] shrink-0 flex-col border-r border-line bg-bg-elev/70 px-4 py-5 backdrop-blur-xl lg:flex">
      <div className="flex items-center gap-3 px-2 pb-6">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-primary-strong text-white shadow-[0_8px_24px_-8px_rgba(99,102,241,0.7)]">
          <Workflow size={18} strokeWidth={2.4} />
        </div>
        <div className="leading-tight">
          <div className="text-[15px] font-bold text-fg">Process Blueprint</div>
          <div className="text-[11px] font-medium text-muted">Consulting intelligence</div>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map(({ icon: Icon, label, active }) => (
          <a
            key={label}
            href="#"
            className={
              "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13.5px] font-medium transition-colors " +
              (active
                ? "bg-primary/15 text-fg ring-1 ring-inset ring-primary/30"
                : "text-fg-2 hover:bg-panel hover:text-fg")
            }
          >
            <Icon
              size={18}
              className={active ? "text-primary" : "text-muted group-hover:text-fg-2"}
            />
            {label}
          </a>
        ))}
      </nav>

      <div className="mt-auto rounded-xl border border-line bg-panel/60 p-3">
        <div className="flex items-center gap-2 text-[12px] font-semibold text-fg">
          <ShieldCheck size={15} className="text-success" />
          Internal tool
        </div>
        <p className="mt-1 text-[11px] leading-relaxed text-muted">
          Clients receive reports only — never access to the engine.
        </p>
      </div>
    </aside>
  );
}
