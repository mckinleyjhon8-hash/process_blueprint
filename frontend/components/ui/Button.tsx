import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Loader2 } from "lucide-react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-primary-strong text-white hover:bg-primary shadow-[var(--elev-glow)] disabled:shadow-none",
  secondary:
    "border border-line bg-panel/60 text-fg-2 hover:border-line hover:bg-panel-2/70 hover:text-fg",
  ghost: "text-fg-2 hover:bg-panel/70 hover:text-fg",
  danger: "bg-danger/15 text-danger ring-1 ring-inset ring-danger/30 hover:bg-danger/25",
};

const SIZES: Record<Size, string> = {
  sm: "gap-1.5 rounded-lg px-2.5 py-1.5 text-xs",
  md: "gap-1.5 rounded-xl px-3.5 py-2 text-xs",
};

export function Button({
  variant = "secondary",
  size = "md",
  loading = false,
  icon,
  children,
  className = "",
  disabled,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
}) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center font-semibold transition-colors duration-[var(--duration-fast)] disabled:cursor-not-allowed disabled:opacity-45 ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    >
      {loading ? <Loader2 size={14} className="animate-spin" /> : icon}
      {children}
    </button>
  );
}
