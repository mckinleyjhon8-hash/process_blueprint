/** Shared formatting — facts carry seconds; format only at the edge. */

export function fmtDuration(seconds: number): string {
  const h = seconds / 3600;
  if (h >= 48) return `${(h / 24).toFixed(1)}d`;
  if (h >= 1) return `${h.toFixed(1)}h`;
  return `${Math.round(seconds / 60)}m`;
}

export function fmtInt(n: number | null | undefined): string {
  return n == null ? "—" : n.toLocaleString();
}

export function fmtRatio(v: number | null | undefined, digits = 2): string {
  return v == null ? "—" : Number(v).toFixed(digits);
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short" }) +
    " · " +
    d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}
