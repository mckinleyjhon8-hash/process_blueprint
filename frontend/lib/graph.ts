import type { ProcessFacts } from "./types";

/** Client-side process graph derived purely from ProcessFacts — works for
    archived runs and when Graphviz is absent. Nodes = activities, edges =
    observed hand-offs (top variants ∪ measured bottleneck pairs). */

export interface GraphNode {
  id: string;
  label: string;
  frequency: number;
  rework: number;
  isStart: boolean;
  isEnd: boolean;
  x: number;
  y: number;
  w: number;
  h: number;
  layer: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  weight: number; // cases observed over this hand-off (from variant traffic)
  waitSeconds: number | null; // measured mean wait if this pair is a bottleneck
  isBottleneck: boolean;
  selfLoop: boolean;
  backward: boolean;
}

export interface ProcessGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  width: number;
  height: number;
  /** activities present in the log but not on any top path */
  offPath: string[];
}

export const NODE_W = 176;
export const NODE_H = 52;
const GAP_X = 110;
const GAP_Y = 40;
const MARGIN = 48;

export function buildProcessGraph(facts: ProcessFacts): ProcessGraph {
  // ---- collect edges from the top variants (weight = cases on that path) ----
  const edgeMap = new Map<string, { weight: number }>();
  const inPath = new Set<string>();
  for (const v of facts.top_variants) {
    for (let i = 0; i < v.sequence.length; i++) {
      inPath.add(v.sequence[i]);
      if (i === 0) continue;
      const key = `${v.sequence[i - 1]}→${v.sequence[i]}`;
      const e = edgeMap.get(key) ?? { weight: 0 };
      e.weight += v.frequency;
      edgeMap.set(key, e);
    }
  }

  // ---- overlay measured bottleneck pairs (they come from the real DFG) ----
  const waits = new Map<string, number>();
  for (const b of facts.bottlenecks) {
    const key = `${b.source}→${b.target}`;
    waits.set(key, b.mean_wait_seconds);
    inPath.add(b.source);
    inPath.add(b.target);
    if (!edgeMap.has(key)) edgeMap.set(key, { weight: b.occurrences });
  }

  const starts = new Set(Object.keys(facts.start_activities));
  const ends = new Set(Object.keys(facts.end_activities));

  // ---- longest-path layering (cycle-safe: relaxation capped at |V| passes) ----
  const nodeIds = [...inPath];
  const layer = new Map<string, number>(nodeIds.map((n) => [n, 0]));
  const straight = [...edgeMap.keys()]
    .map((k) => k.split("→"))
    .filter(([s, t]) => s !== t);
  for (let pass = 0; pass < nodeIds.length; pass++) {
    let changed = false;
    for (const [s, t] of straight) {
      const cand = (layer.get(s) ?? 0) + 1;
      if (cand > (layer.get(t) ?? 0) && cand < nodeIds.length) {
        layer.set(t, cand);
        changed = true;
      }
    }
    if (!changed) break;
  }
  // pin true start activities to the first column when nothing points at them
  for (const s of starts) if (layer.has(s) && ![...edgeMap.keys()].some((k) => k.endsWith(`→${s}`))) layer.set(s, 0);

  // ---- position: column per layer, stacked + centered vertically ----
  const byLayer = new Map<number, string[]>();
  for (const n of nodeIds) {
    const l = layer.get(n) ?? 0;
    byLayer.set(l, [...(byLayer.get(l) ?? []), n]);
  }
  const maxLayer = Math.max(...byLayer.keys(), 0);
  const tallest = Math.max(...[...byLayer.values()].map((v) => v.length), 1);
  const height = MARGIN * 2 + tallest * NODE_H + (tallest - 1) * GAP_Y;
  const width = MARGIN * 2 + (maxLayer + 1) * NODE_W + maxLayer * GAP_X;

  const pos = new Map<string, { x: number; y: number }>();
  for (const [l, members] of byLayer) {
    // frequency-sorted so the mainline path stays near the top
    members.sort((a, b) => (facts.activity_frequencies[b] ?? 0) - (facts.activity_frequencies[a] ?? 0));
    const columnH = members.length * NODE_H + (members.length - 1) * GAP_Y;
    members.forEach((n, i) => {
      pos.set(n, {
        x: MARGIN + l * (NODE_W + GAP_X),
        y: (height - columnH) / 2 + i * (NODE_H + GAP_Y),
      });
    });
  }

  const nodes: GraphNode[] = nodeIds.map((id) => ({
    id,
    label: id,
    frequency: facts.activity_frequencies[id] ?? 0,
    rework: facts.rework_activities[id] ?? 0,
    isStart: starts.has(id),
    isEnd: ends.has(id),
    ...pos.get(id)!,
    w: NODE_W,
    h: NODE_H,
    layer: layer.get(id) ?? 0,
  }));

  const edges: GraphEdge[] = [...edgeMap.entries()].map(([key, e]) => {
    const [source, target] = key.split("→");
    const wait = waits.get(key) ?? null;
    return {
      id: key,
      source,
      target,
      weight: e.weight,
      waitSeconds: wait,
      isBottleneck: wait != null,
      selfLoop: source === target,
      backward: (layer.get(target) ?? 0) <= (layer.get(source) ?? 0) && source !== target,
    };
  });

  const offPath = Object.keys(facts.activity_frequencies).filter((a) => !inPath.has(a));

  return { nodes, edges, width, height, offPath };
}
