import type { ReactNode } from "react";

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}: {
  icon: ReactNode;
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={`grid place-items-center px-6 py-14 text-center ${className}`}>
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-primary/12 text-primary">
        {icon}
      </span>
      <h3 className="mt-3 text-base font-bold text-fg">{title}</h3>
      {description && (
        <p className="mt-1 max-w-[380px] text-sm leading-relaxed text-muted">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
