"use client";

import { useMemo } from "react";
import type { ProcessGraph } from "@/lib/graph";
import { fmtDuration } from "@/lib/format";

/** SVG renderer for the facts-derived process graph: weighted edges, measured
    bottleneck hand-offs, rework loops, start/end markers, node selection. */
export function DependencyGraph({
  graph,
  selected,
  onSelect,
  highlight,
}: {
  graph: ProcessGraph;
  selected: string | null;
  onSelect: (id: string | null) => void;
  highlight: string;
}) {
  const byId = useMemo(() => new Map(graph.nodes.map((n) => [n.id, n])), [graph]);
  const maxWeight = Math.max(...graph.edges.map((e) => e.weight), 1);
  const q = highlight.trim().toLowerCase();

  const dimmed = (id: string) => (q ? !id.toLowerCase().includes(q) : false);

  return (
    <svg
      width={graph.width}
      height={graph.height}
      viewBox={`0 0 ${graph.width} ${graph.height}`}
      className="select-none"
      role="img"
      aria-label="Process dependency graph"
      onClick={() => onSelect(null)}
    >
      <defs>
        <marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 z" fill="var(--map-arrow)" />
        </marker>
        <marker id="arrow-hot" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 z" fill="var(--color-warning-vivid)" />
        </marker>
      </defs>

      {/* ---- edges ---- */}
      {graph.edges.map((e) => {
        const s = byId.get(e.source);
        const t = byId.get(e.target);
        if (!s || !t) return null;
        const stroke = e.isBottleneck ? "var(--color-warning-vivid)" : "var(--map-edge)";
        const sw = 1.25 + (e.weight / maxWeight) * 3.5;
        const touched = selected && (e.source === selected || e.target === selected);
        const opacity = selected ? (touched ? 1 : 0.18) : q && (dimmed(e.source) || dimmed(e.target)) ? 0.12 : 0.9;

        let d: string;
        let labelX: number;
        let labelY: number;
        if (e.selfLoop) {
          // rework loop drawn above the node
          const x = s.x + s.w / 2;
          const y = s.y;
          d = `M ${x - 18} ${y} C ${x - 30} ${y - 42}, ${x + 30} ${y - 42}, ${x + 18} ${y}`;
          labelX = x;
          labelY = y - 38;
        } else if (e.backward) {
          // return edge arcs underneath the flow
          const x1 = s.x + s.w / 2;
          const y1 = s.y + s.h;
          const x2 = t.x + t.w / 2;
          const y2 = t.y + t.h;
          const dip = Math.max(y1, y2) + 56;
          d = `M ${x1} ${y1} C ${x1} ${dip}, ${x2} ${dip}, ${x2} ${y2}`;
          labelX = (x1 + x2) / 2;
          labelY = dip - 6;
        } else {
          const x1 = s.x + s.w;
          const y1 = s.y + s.h / 2;
          const x2 = t.x;
          const y2 = t.y + t.h / 2;
          const mid = (x1 + x2) / 2;
          d = `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`;
          labelX = mid;
          labelY = (y1 + y2) / 2 - 8;
        }

        return (
          <g key={e.id} opacity={opacity} className="transition-opacity duration-200">
            <path
              d={d}
              fill="none"
              stroke={stroke}
              strokeWidth={sw}
              markerEnd={e.isBottleneck ? "url(#arrow-hot)" : "url(#arrow)"}
            />
            {e.isBottleneck && e.waitSeconds != null && (
              <g>
                <rect x={labelX - 26} y={labelY - 12} width="52" height="17" rx="8" fill="var(--map-wait-chip)" stroke="var(--color-warning-vivid)" strokeOpacity="0.6" />
                <text x={labelX} y={labelY} textAnchor="middle" fontSize="10" fontWeight="700" fill="var(--color-warning)" fontFamily="var(--font-jet)">
                  {fmtDuration(e.waitSeconds)}
                </text>
              </g>
            )}
          </g>
        );
      })}

      {/* ---- nodes ---- */}
      {graph.nodes.map((n) => {
        const isSel = n.id === selected;
        const dim = selected ? !isSel && !graph.edges.some((e) => (e.source === selected && e.target === n.id) || (e.target === selected && e.source === n.id)) : dimmed(n.id);
        const accent = n.isStart ? "var(--color-success-vivid)" : n.isEnd ? "var(--color-violet)" : "var(--color-primary)";
        return (
          <g
            key={n.id}
            transform={`translate(${n.x}, ${n.y})`}
            opacity={dim ? 0.25 : 1}
            className="cursor-pointer transition-opacity duration-200"
            onClick={(ev) => {
              ev.stopPropagation();
              onSelect(isSel ? null : n.id);
            }}
            role="button"
            aria-label={`Activity ${n.label}`}
          >
            <rect
              width={n.w}
              height={n.h}
              rx="12"
              fill={isSel ? "var(--map-node-fill-active)" : "var(--map-node-fill)"}
              stroke={isSel ? "var(--color-primary)" : "var(--map-node-stroke)"}
              strokeWidth={isSel ? 2 : 1.25}
            />
            <rect x="0" y="0" width="4" height={n.h} rx="2" fill={accent} />
            <text x="14" y="22" fontSize="12" fontWeight="700" fill="var(--color-fg)" fontFamily="var(--font-jakarta)">
              {n.label.length > 22 ? `${n.label.slice(0, 21)}…` : n.label}
            </text>
            <text x="14" y="39" fontSize="10" fill="var(--color-muted)" fontFamily="var(--font-jet)">
              {n.frequency.toLocaleString()}×{n.rework > 0 ? ` · ↺ ${n.rework} rework` : ""}
            </text>
            {(n.isStart || n.isEnd) && (
              <text x={n.w - 12} y="20" textAnchor="end" fontSize="9" fontWeight="700" fill={accent} fontFamily="var(--font-jakarta)">
                {n.isStart ? "START" : "END"}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
