import type { ModelQuality } from "@/lib/types";

const AXES: { key: keyof ModelQuality; label: string }[] = [
  { key: "fitness", label: "Fitness" },
  { key: "precision", label: "Precision" },
  { key: "generalization", label: "Generalization" },
  { key: "simplicity", label: "Simplicity" },
];

export function ModelRadar({ model }: { model: ModelQuality }) {
  const cx = 130;
  const cy = 120;
  const R = 88;
  const n = AXES.length;

  const point = (i: number, radius: number) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    return [cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)];
  };

  const rings = [0.25, 0.5, 0.75, 1];
  const values = AXES.map((a) => Math.max(0, Math.min(1, (model[a.key] as number) ?? 0)));
  const poly = values.map((v, i) => point(i, R * v).join(",")).join(" ");

  return (
    <svg viewBox="0 0 260 230" className="h-[220px] w-full">
      {rings.map((rr) => (
        <polygon
          key={rr}
          points={AXES.map((_, i) => point(i, R * rr).join(",")).join(" ")}
          fill="none"
          stroke="var(--color-line)"
          strokeWidth="1"
        />
      ))}
      {AXES.map((_, i) => {
        const [x, y] = point(i, R);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--color-line)" strokeWidth="1" />;
      })}
      <polygon points={poly} fill="rgba(97,97,255,0.16)" stroke="var(--color-primary)" strokeWidth="2" />
      {values.map((v, i) => {
        const [x, y] = point(i, R * v);
        return <circle key={i} cx={x} cy={y} r="3" fill="var(--color-violet)" />;
      })}
      {AXES.map((a, i) => {
        const [x, y] = point(i, R + 18);
        return (
          <text
            key={a.label}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="font-sans"
            fill="var(--color-muted)"
            fontSize="11"
            fontWeight="600"
          >
            {a.label}
          </text>
        );
      })}
    </svg>
  );
}
