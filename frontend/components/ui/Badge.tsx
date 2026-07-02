import type { ReactNode } from "react";

type Tone = "neutral" | "primary" | "success" | "warning" | "danger" | "info" | "violet";

const TONES: Record<Tone, string> = {
  neutral: "bg-panel-2/60 text-muted ring-line",
  primary: "bg-primary/12 text-primary ring-primary/30",
  success: "bg-success/12 text-success ring-success/25",
  warning: "bg-warning/12 text-warning ring-warning/25",
  danger: "bg-danger/12 text-danger ring-danger/25",
  info: "bg-info/12 text-info ring-info/25",
  violet: "bg-violet/12 text-violet ring-violet/25",
};

export function Badge({
  tone = "neutral",
  children,
  className = "",
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-2xs font-semibold ring-1 ring-inset ${TONES[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

/** Small status dot + label, used for live/health indicators. */
export function StatusDot({
  tone,
  label,
  pulse = false,
}: {
  tone: Tone;
  label: string;
  pulse?: boolean;
}) {
  const dot: Record<Tone, string> = {
    neutral: "bg-muted",
    primary: "bg-primary",
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-danger",
    info: "bg-info",
    violet: "bg-violet",
  };
  return (
    <Badge tone={tone}>
      <span className={`h-1.5 w-1.5 rounded-full ${dot[tone]} ${pulse ? "animate-pulse" : ""}`} />
      {label}
    </Badge>
  );
}
