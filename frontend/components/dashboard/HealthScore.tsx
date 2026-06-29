export function HealthScore({
  score,
  grade,
  label,
}: {
  score: number;
  grade: string;
  label: string;
}) {
  const r = 56;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const dash = c * pct;

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative h-[160px] w-[160px]">
        <svg viewBox="0 0 140 140" className="h-full w-full -rotate-90">
          <circle cx="70" cy="70" r={r} fill="none" stroke="var(--color-line)" strokeWidth="10" />
          <defs>
            <linearGradient id="hs" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#6366f1" />
            </linearGradient>
          </defs>
          <circle
            cx="70"
            cy="70"
            r={r}
            fill="none"
            stroke="url(#hs)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${c}`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono text-[40px] font-bold leading-none text-fg">{score}</span>
          <span className="mt-1 text-[11px] font-medium text-muted">out of 100</span>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <span className="rounded-lg bg-success/15 px-2.5 py-1 text-[13px] font-bold text-success">
          {grade}
        </span>
        <span className="text-[13px] font-medium text-fg-2">{label}</span>
      </div>
      <p className="mt-3 max-w-[220px] text-center text-[11.5px] leading-relaxed text-muted">
        Weighted from fitness, precision, generalization &amp; simplicity.
      </p>
    </div>
  );
}
