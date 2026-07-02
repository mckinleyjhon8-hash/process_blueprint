"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Maximize, Minimize, ZoomIn, ZoomOut, Scan, Percent } from "lucide-react";

const MIN_SCALE = 0.1;
const MAX_SCALE = 3;

/** Infinite-canvas viewport: wheel zoom (cursor-anchored), drag pan, fit,
    100%, fullscreen and a live minimap. Content is any fixed-size child —
    the dependency-graph SVG or the Graphviz Petri net. */
export function ProcessCanvas({
  children,
  contentWidth,
  contentHeight,
  className = "",
}: {
  children: ReactNode;
  contentWidth: number;
  contentHeight: number;
  className?: string;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [view, setView] = useState({ scale: 1, tx: 0, ty: 0 });
  const [fullscreen, setFullscreen] = useState(false);
  const drag = useRef<{ x: number; y: number; tx: number; ty: number } | null>(null);

  const fit = useCallback(() => {
    const el = wrapRef.current;
    if (!el || !contentWidth || !contentHeight) return;
    const scale = Math.min(
      (el.clientWidth / contentWidth) * 0.94,
      (el.clientHeight / contentHeight) * 0.94,
      MAX_SCALE,
    );
    setView({
      scale,
      tx: (el.clientWidth - contentWidth * scale) / 2,
      ty: (el.clientHeight - contentHeight * scale) / 2,
    });
  }, [contentWidth, contentHeight]);

  // Fit on mount + whenever the content dimensions change.
  useEffect(() => {
    fit();
  }, [fit]);

  const zoomAt = useCallback((cx: number, cy: number, factor: number) => {
    setView((v) => {
      const scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, v.scale * factor));
      const k = scale / v.scale;
      return { scale, tx: cx - (cx - v.tx) * k, ty: cy - (cy - v.ty) * k };
    });
  }, []);

  // Native wheel listener (non-passive) so we can preventDefault page scroll.
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const r = el.getBoundingClientRect();
      zoomAt(e.clientX - r.left, e.clientY - r.top, e.deltaY < 0 ? 1.12 : 1 / 1.12);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [zoomAt]);

  // Fullscreen tracking.
  useEffect(() => {
    const onFs = () => setFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", onFs);
    return () => document.removeEventListener("fullscreenchange", onFs);
  }, []);

  function center(factor: number) {
    const el = wrapRef.current;
    if (!el) return;
    zoomAt(el.clientWidth / 2, el.clientHeight / 2, factor);
  }

  // ---- minimap geometry ----
  const el = wrapRef.current;
  const MM_W = 148;
  const mmScale = contentWidth ? MM_W / contentWidth : 0;
  const mmH = contentHeight * mmScale;
  const vp = el
    ? {
        x: Math.max(0, (-view.tx / view.scale) * mmScale),
        y: Math.max(0, (-view.ty / view.scale) * mmScale),
        w: Math.min(MM_W, (el.clientWidth / view.scale) * mmScale),
        h: Math.min(mmH, (el.clientHeight / view.scale) * mmScale),
      }
    : null;

  const btn =
    "grid h-8 w-8 place-items-center rounded-lg border border-line bg-bg-elev/95 text-fg-2 shadow-[var(--elev-1)] backdrop-blur transition-colors hover:text-fg";

  return (
    <div
      ref={wrapRef}
      className={`relative touch-none overflow-hidden bg-[var(--map-canvas)] ${className}`}
      style={{
        backgroundImage: "radial-gradient(circle, var(--map-dot) 1px, transparent 1px)",
        backgroundSize: "24px 24px",
      }}
      onPointerDown={(e) => {
        if (e.button !== 0) return;
        if ((e.target as HTMLElement).closest("[data-canvas-ui]")) return;
        e.currentTarget.setPointerCapture(e.pointerId);
        drag.current = { x: e.clientX, y: e.clientY, tx: view.tx, ty: view.ty };
      }}
      onPointerMove={(e) => {
        const d = drag.current;
        if (!d) return;
        // snapshot before setView — pointerup may null drag.current before
        // React runs the deferred updater
        const tx = d.tx + e.clientX - d.x;
        const ty = d.ty + e.clientY - d.y;
        setView((v) => ({ ...v, tx, ty }));
      }}
      onPointerUp={() => (drag.current = null)}
      onPointerLeave={() => (drag.current = null)}
      role="application"
      aria-label="Process map canvas — drag to pan, scroll to zoom"
    >
      <div
        className="absolute left-0 top-0 origin-top-left will-change-transform"
        style={{ transform: `translate(${view.tx}px, ${view.ty}px) scale(${view.scale})` }}
      >
        {children}
      </div>

      {/* ---- controls ---- */}
      <div data-canvas-ui className="absolute left-3 top-3 flex flex-col gap-1.5">
        <button className={btn} onClick={() => center(1.25)} aria-label="Zoom in" title="Zoom in">
          <ZoomIn size={15} />
        </button>
        <button className={btn} onClick={() => center(1 / 1.25)} aria-label="Zoom out" title="Zoom out">
          <ZoomOut size={15} />
        </button>
        <button className={btn} onClick={fit} aria-label="Fit to view" title="Fit to view">
          <Scan size={15} />
        </button>
        <button
          className={btn}
          onClick={() => setView((v) => ({ ...v, scale: 1 }))}
          aria-label="Zoom to 100%"
          title="100%"
        >
          <Percent size={15} />
        </button>
        <button
          className={btn}
          onClick={() =>
            document.fullscreenElement
              ? document.exitFullscreen()
              : wrapRef.current?.requestFullscreen()
          }
          aria-label={fullscreen ? "Exit fullscreen" : "Fullscreen"}
          title={fullscreen ? "Exit fullscreen" : "Fullscreen"}
        >
          {fullscreen ? <Minimize size={15} /> : <Maximize size={15} />}
        </button>
      </div>

      <span
        data-canvas-ui
        className="absolute bottom-3 left-3 rounded-lg border border-line bg-bg-elev/90 px-2 py-1 font-mono text-2xs font-semibold text-muted backdrop-blur"
      >
        {Math.round(view.scale * 100)}%
      </span>

      {/* ---- minimap ---- */}
      {vp && mmH > 0 && (
        <button
          data-canvas-ui
          aria-label="Minimap — click to recenter"
          className="absolute bottom-3 right-3 hidden overflow-hidden rounded-lg border border-line bg-bg-elev/90 backdrop-blur sm:block"
          style={{ width: MM_W, height: Math.min(mmH, 110) }}
          onClick={(e) => {
            const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
            const cx = ((e.clientX - r.left) / mmScale) * view.scale;
            const cy = ((e.clientY - r.top) / mmScale) * view.scale;
            const elw = wrapRef.current!;
            setView((v) => ({ ...v, tx: elw.clientWidth / 2 - cx, ty: elw.clientHeight / 2 - cy }));
          }}
        >
          <span className="absolute inset-0 bg-primary/8" />
          <span
            className="absolute rounded-[3px] border border-primary/80 bg-primary/20"
            style={{ left: vp.x, top: vp.y, width: vp.w, height: vp.h }}
          />
        </button>
      )}
    </div>
  );
}
