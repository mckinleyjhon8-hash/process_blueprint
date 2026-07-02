import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
  title,
  subtitle,
  action,
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  padded?: boolean;
}) {
  return (
    <section
      className={`rise rounded-2xl border border-line bg-panel shadow-[var(--elev-1)] ${
        padded ? "p-5" : ""
      } ${className}`}
    >
      {(title || action) && (
        <div className={`flex items-start justify-between gap-3 ${padded ? "mb-4" : "border-b border-line px-5 py-4"}`}>
          <div>
            {title && <h2 className="text-base font-bold text-fg">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  );
}
