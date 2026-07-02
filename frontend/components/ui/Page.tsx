import type { ReactNode } from "react";

/** Standard page container: consistent gutters + max width across routes.
    Pages that need full-bleed (Map Studio) simply don't use it. */
export function Page({
  children,
  width = "default",
  className = "",
}: {
  children: ReactNode;
  width?: "default" | "narrow" | "wide";
  className?: string;
}) {
  const max =
    width === "narrow" ? "max-w-[920px]" : width === "wide" ? "max-w-[1400px]" : "max-w-[1200px]";
  return (
    <div className={`mx-auto w-full ${max} space-y-6 px-4 py-6 sm:px-6 lg:px-8 ${className}`}>
      {children}
    </div>
  );
}

/** Page heading block: title + description + optional right-side actions. */
export function PageHeader({
  title,
  description,
  actions,
  eyebrow,
}: {
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  eyebrow?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {eyebrow}
        <h1 className="text-xl font-extrabold tracking-tight text-fg">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
