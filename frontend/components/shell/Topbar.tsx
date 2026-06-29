import { Search, Bell, ChevronDown, Sparkles } from "lucide-react";

export function Topbar() {
  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-4 border-b border-line bg-bg/70 px-6 backdrop-blur-xl lg:px-8">
      <div>
        <h1 className="text-[15px] font-bold leading-none text-fg">Dashboard</h1>
        <p className="mt-1 text-[11.5px] text-muted">Procure-to-Pay · Acme SME</p>
      </div>

      <div className="ml-2 hidden items-center gap-2 rounded-xl border border-line bg-panel/60 px-3 py-2 md:flex">
        <Search size={15} className="text-muted" />
        <input
          placeholder="Search engagements, processes…"
          className="w-56 bg-transparent text-[13px] text-fg placeholder:text-muted focus:outline-none"
        />
      </div>

      <div className="ml-auto flex items-center gap-3">
        <span className="hidden items-center gap-1.5 rounded-full border border-success/30 bg-success/10 px-2.5 py-1 text-[11px] font-semibold text-success sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-success" /> engine online
        </span>
        <button className="flex items-center gap-1.5 rounded-xl bg-primary-strong px-3 py-2 text-[12.5px] font-semibold text-white transition-colors hover:bg-primary">
          <Sparkles size={14} /> New analysis
        </button>
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
