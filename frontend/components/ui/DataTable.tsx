"use client";

import { useMemo, useState, type ReactNode } from "react";
import { ArrowDown, ArrowUp, ChevronsUpDown, Search, SearchX } from "lucide-react";
import { SkeletonRows } from "./Skeleton";
import { EmptyState } from "./EmptyState";

export interface Column<T> {
  id: string;
  header: string;
  cell: (row: T) => ReactNode;
  /** value used for sorting; omit to make the column unsortable */
  sortValue?: (row: T) => string | number | null;
  align?: "left" | "right";
  className?: string;
}

/** Enterprise table: client-side sort + search, sticky header, loading
    skeleton and designed empty states. Rows are plain data — rendering
    stays in `columns`, so every page reuses one implementation. */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  loading = false,
  searchable = true,
  searchPlaceholder = "Filter…",
  searchText,
  empty,
  initialSort,
  toolbar,
  maxHeight = "max-h-[560px]",
}: {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T, index: number) => string;
  loading?: boolean;
  searchable?: boolean;
  searchPlaceholder?: string;
  /** text blob per row that the search box matches against */
  searchText?: (row: T) => string;
  empty: ReactNode;
  initialSort?: { id: string; dir: "asc" | "desc" };
  toolbar?: ReactNode;
  maxHeight?: string;
}) {
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<{ id: string; dir: "asc" | "desc" } | null>(
    initialSort ?? null,
  );

  const visible = useMemo(() => {
    let out = rows;
    const q = query.trim().toLowerCase();
    if (q && searchText) out = out.filter((r) => searchText(r).toLowerCase().includes(q));
    if (sort) {
      const col = columns.find((c) => c.id === sort.id);
      if (col?.sortValue) {
        const mul = sort.dir === "asc" ? 1 : -1;
        out = [...out].sort((a, b) => {
          const va = col.sortValue!(a);
          const vb = col.sortValue!(b);
          if (va == null) return 1;
          if (vb == null) return -1;
          if (typeof va === "number" && typeof vb === "number") return (va - vb) * mul;
          return String(va).localeCompare(String(vb)) * mul;
        });
      }
    }
    return out;
  }, [rows, query, sort, columns, searchText]);

  function toggleSort(id: string) {
    setSort((s) =>
      s?.id === id ? { id, dir: s.dir === "asc" ? "desc" : "asc" } : { id, dir: "desc" },
    );
  }

  return (
    <div>
      {(searchable || toolbar) && (
        <div className="flex flex-wrap items-center gap-2 border-b border-line px-4 py-3">
          {searchable && (
            <div className="relative">
              <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={searchPlaceholder}
                aria-label={searchPlaceholder}
                className="w-[220px] rounded-lg border border-line bg-bg-elev/60 py-1.5 pl-8 pr-3 text-xs text-fg placeholder:text-muted focus:border-primary/60"
              />
            </div>
          )}
          <span className="text-2xs text-muted">
            {loading ? "" : `${visible.length}${visible.length !== rows.length ? ` of ${rows.length}` : ""} rows`}
          </span>
          <div className="ml-auto flex items-center gap-2">{toolbar}</div>
        </div>
      )}

      {loading ? (
        <SkeletonRows rows={6} cols={columns.length} />
      ) : rows.length === 0 ? (
        empty
      ) : visible.length === 0 ? (
        <EmptyState
          icon={<SearchX size={22} />}
          title="No matches"
          description={`Nothing matches “${query}”. Try a different filter.`}
        />
      ) : (
        <div className={`overflow-auto ${maxHeight}`}>
          <table className="w-full text-sm">
            <thead className="sticky top-0 z-10 bg-panel">
              <tr className="border-b border-line text-left text-xs text-muted">
                {columns.map((c) => (
                  <th
                    key={c.id}
                    className={`whitespace-nowrap px-5 py-3 font-medium ${c.align === "right" ? "text-right" : ""} ${c.className ?? ""}`}
                    aria-sort={
                      sort?.id === c.id ? (sort.dir === "asc" ? "ascending" : "descending") : undefined
                    }
                  >
                    {c.sortValue ? (
                      <button
                        onClick={() => toggleSort(c.id)}
                        className={`inline-flex items-center gap-1 hover:text-fg-2 ${sort?.id === c.id ? "text-fg" : ""}`}
                      >
                        {c.header}
                        {sort?.id === c.id ? (
                          sort.dir === "asc" ? <ArrowUp size={12} /> : <ArrowDown size={12} />
                        ) : (
                          <ChevronsUpDown size={12} className="opacity-50" />
                        )}
                      </button>
                    ) : (
                      c.header
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visible.map((row, i) => (
                <tr
                  key={rowKey(row, i)}
                  className="border-b border-line-soft transition-colors duration-[var(--duration-fast)] last:border-0 hover:bg-panel-2/40"
                >
                  {columns.map((c) => (
                    <td
                      key={c.id}
                      className={`px-5 py-3 ${c.align === "right" ? "text-right" : ""} ${c.className ?? ""}`}
                    >
                      {c.cell(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
