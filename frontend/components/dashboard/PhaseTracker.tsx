import { Check } from "lucide-react";

const PHASES = [
  { id: "1", label: "Engine", done: true },
  { id: "1.5", label: "Supabase", done: true },
  { id: "2", label: "LLM brief", done: true },
  { id: "3", label: "Knowledge", done: true },
  { id: "4", label: "Portal", current: true },
  { id: "5", label: "Hardening" },
];

export function PhaseTracker() {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {PHASES.map((p) => (
        <span
          key={p.id}
          className={
            "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[12px] font-semibold " +
            (p.done
              ? "bg-success/12 text-success ring-1 ring-inset ring-success/25"
              : p.current
                ? "bg-primary/15 text-primary ring-1 ring-inset ring-primary/35"
                : "bg-panel-2/60 text-muted ring-1 ring-inset ring-line")
          }
        >
          {p.done ? <Check size={12} strokeWidth={3} /> : <span className="font-mono">{p.id}</span>}
          {p.label}
        </span>
      ))}
    </div>
  );
}
