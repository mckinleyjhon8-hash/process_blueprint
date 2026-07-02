export function Kbd({ children }: { children: string }) {
  return (
    <kbd className="rounded-md border border-line bg-panel-2/80 px-1.5 py-0.5 font-mono text-2xs font-semibold text-muted">
      {children}
    </kbd>
  );
}
