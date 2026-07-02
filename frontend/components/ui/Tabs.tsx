"use client";

import type { ReactNode } from "react";

export interface TabDef {
  id: string;
  label: string;
  icon?: ReactNode;
  badge?: ReactNode;
}

/** Underline tabs (Linear/GitHub pattern) with keyboard + ARIA support. */
export function Tabs({
  tabs,
  active,
  onChange,
  className = "",
}: {
  tabs: TabDef[];
  active: string;
  onChange: (id: string) => void;
  className?: string;
}) {
  function onKeyDown(e: React.KeyboardEvent) {
    const i = tabs.findIndex((t) => t.id === active);
    if (e.key === "ArrowRight") onChange(tabs[(i + 1) % tabs.length].id);
    if (e.key === "ArrowLeft") onChange(tabs[(i - 1 + tabs.length) % tabs.length].id);
  }

  return (
    <div
      role="tablist"
      aria-label="Sections"
      onKeyDown={onKeyDown}
      className={`flex items-center gap-1 overflow-x-auto border-b border-line ${className}`}
    >
      {tabs.map((t) => {
        const is = t.id === active;
        return (
          <button
            key={t.id}
            role="tab"
            aria-selected={is}
            tabIndex={is ? 0 : -1}
            onClick={() => onChange(t.id)}
            className={
              "relative flex shrink-0 items-center gap-1.5 px-3.5 py-2.5 text-sm font-semibold transition-colors duration-[var(--duration-fast)] " +
              (is ? "text-fg" : "text-muted hover:text-fg-2")
            }
          >
            {t.icon}
            {t.label}
            {t.badge}
            {is && (
              <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-primary" />
            )}
          </button>
        );
      })}
    </div>
  );
}
