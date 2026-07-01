"""
report.py — assemble a branded, print-ready client deliverable (HTML) from a
ProcessFacts object + the generated brief (+ optional SOP compliance findings).

Design choices:
  * LIGHT, premium document theme (UI/UX Pro Max enterprise: indigo/violet,
    Plus Jakarta Sans) — the right look for something a client prints/keeps,
    not the dark command-center dashboard.
  * Self-contained HTML with embedded CSS + print rules, so the browser's own
    "Save as PDF" produces a perfect PDF. Zero runtime dependencies.
  * Audience-aware: the client deliverable omits the engine mechanics entirely;
    the internal version keeps conformance detail.
  * Process visual: a dependency-free SVG flow of the dominant variant with the
    slowest hand-offs highlighted (used because Graphviz/Petri-net render needs
    a system binary that may be absent).
"""

from __future__ import annotations

import datetime as _dt
import html as _html
import re
from typing import Any, Dict, List, Optional

from .facts import ProcessFacts
from .brief.scoring import health_score

# Activities that should be highlighted come from the bottleneck list.
_BRAND = "Process Blueprint"


def build_report_html(
    facts: ProcessFacts,
    brief_markdown: Optional[str],
    audience: str = "client",
    compliance: Optional[Dict[str, Any]] = None,
    firm: str = "Consulting Intelligence",
    process_map_svg: Optional[str] = None,
) -> str:
    """Return a complete, self-contained branded HTML report.

    `process_map_svg` — optional real Petri-net SVG (from the engine). When given
    it is embedded as the process model; otherwise a dependency-free variant flow.
    """
    audience = audience.lower()
    is_client = audience == "client"
    score, grade = health_score(facts)
    now = _dt.datetime.now().strftime("%d %B %Y")

    sections = [
        _header(facts, firm, now, is_client),
        _summary_band(facts, score, grade),
        _kpi_cards(facts),
        _flow_section(facts, process_map_svg),
        _brief_section(brief_markdown, is_client),
        _bottlenecks_section(facts),
    ]
    if not is_client:
        sections.append(_model_quality_section(facts))
    if compliance:
        sections.append(_compliance_section(compliance))
    sections.append(_footer(is_client, firm))

    body = "\n".join(s for s in sections if s)
    return _DOCUMENT.format(title=f"{facts.process_type} — Brief", css=_CSS, body=body)


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
def _header(facts: ProcessFacts, firm: str, date: str, is_client: bool) -> str:
    tag = "Client deliverable" if is_client else "Internal — full detail"
    return f"""
<header class="cover">
  <div class="brand"><span class="dot"></span>{_BRAND}<span class="firm">· {_e(firm)}</span></div>
  <div class="cover-tag">{tag}</div>
  <h1>{_e(facts.process_type)} — Process Review</h1>
  <p class="cover-sub">Evidence-based analysis of {facts.n_cases:,} cases · {facts.n_events:,} events · {date}</p>
</header>"""


def _summary_band(facts: ProcessFacts, score, grade) -> str:
    s = score if score is not None else "—"
    g = _e(str(grade))
    return f"""
<section class="band">
  <div class="band-score"><div class="ring" style="--p:{score or 0}"><span>{s}</span></div>
    <div><div class="band-grade">{g}</div><div class="band-lbl">Process health</div></div></div>
  <div class="band-note">This review summarises how the process actually runs, where time is lost,
    and the priority actions to improve it.</div>
</section>"""


def _kpi_cards(facts: ProcessFacts) -> str:
    cards = [
        ("Cases analysed", f"{facts.n_cases:,}"),
        ("Activities", f"{facts.n_activities}"),
        ("Distinct paths", f"{facts.n_variants}"),
        ("Avg cycle time", _fmt_hours(facts.avg_cycle_time_seconds)),
    ]
    items = "".join(
        f'<div class="kpi"><div class="kpi-v">{v}</div><div class="kpi-l">{_e(l)}</div></div>'
        for l, v in cards
    )
    return f'<section class="kpis">{items}</section>'


def _flow_section(facts: ProcessFacts, process_map_svg: Optional[str] = None) -> str:
    if process_map_svg:
        # Embed the real discovered Petri net (strip any XML prolog/doctype).
        svg = re.sub(r"<\?xml.*?\?>", "", process_map_svg, flags=re.S)
        svg = re.sub(r"<!DOCTYPE.*?>", "", svg, flags=re.S)
        return f"""
<section>
  <h2>Discovered process model</h2>
  <p class="muted">The as-is process mined from the event data (Petri net).</p>
  <div class="flow flow-map">{svg}</div>
</section>"""
    if not facts.top_variants:
        return ""
    svg = _flow_svg(facts)
    pct = round(100 * facts.top_variants[0].frequency / max(facts.n_cases, 1))
    return f"""
<section>
  <h2>Primary process flow</h2>
  <p class="muted">The most common path ({pct}% of cases). Amber steps are the slowest hand-offs.</p>
  <div class="flow">{svg}</div>
</section>"""


def _brief_section(brief_markdown: Optional[str], is_client: bool) -> str:
    if not brief_markdown:
        return ('<section><h2>Findings &amp; recommendations</h2>'
                '<p class="muted">The written brief has not been generated for this run yet.</p></section>')
    return f'<section class="brief">{_md_to_html(brief_markdown)}</section>'


def _bottlenecks_section(facts: ProcessFacts) -> str:
    if not facts.bottlenecks:
        return ""
    rows = "".join(
        f"<tr><td>{_e(b.source)} &rarr; {_e(b.target)}</td>"
        f"<td class='num'>{b.mean_wait_seconds / 3600:.0f} h</td>"
        f"<td class='num'>{b.occurrences:,}</td></tr>"
        for b in facts.bottlenecks[:8]
    )
    return f"""
<section>
  <h2>Slowest hand-offs</h2>
  <table class="tbl"><thead><tr><th>Step transition</th><th class="num">Avg wait</th><th class="num">Occurrences</th></tr></thead>
  <tbody>{rows}</tbody></table>
</section>"""


def _model_quality_section(facts: ProcessFacts) -> str:
    m = facts.model

    def f(v):
        return f"{v:.3f}" if isinstance(v, (int, float)) else "—"

    return f"""
<section class="internal">
  <h2>Model quality <span class="pill">internal only</span></h2>
  <table class="tbl">
    <tr><td>Discovery algorithm</td><td class="num">{_e(m.algorithm)}</td></tr>
    <tr><td>Fitness</td><td class="num">{f(m.fitness)}</td></tr>
    <tr><td>Precision</td><td class="num">{f(m.precision)}</td></tr>
    <tr><td>Generalization</td><td class="num">{f(m.generalization)}</td></tr>
    <tr><td>Simplicity</td><td class="num">{f(m.simplicity)}</td></tr>
  </table>
</section>"""


def _compliance_section(compliance: Dict[str, Any]) -> str:
    labels = {
        "sanctions_check_missing": "Sanctions check skipped on a booking · SOP 1.2",
        "ocrs_check_missing": "OCRS health gate skipped before award · SOP 4.7",
        "cmr_after_pickup": "CMR issued after pickup · SOP 5.1",
        "kyc_after_award": "Carrier KYC after award · SOP 2.3/4",
        "claim_outside_9_day_window": "Claim outside BIFA 9-day window · SOP 7.6",
    }
    rules = compliance.get("rules", {})
    rows = ""
    for key, info in rules.items():
        n = info.get("violations", 0)
        cls = "bad" if n else "ok"
        rows += (f"<tr class='{cls}'><td>{_e(labels.get(key, key))}</td>"
                 f"<td class='num'>{n}</td><td class='num'>{info.get('pct_of_cases', 0)}%</td></tr>")
    total = sum(r.get("violations", 0) for r in rules.values())
    return f"""
<section>
  <h2>SOP compliance check <span class="pill warn">{total} breaches</span></h2>
  <p class="muted">Control breaches detected directly from the event log, each citing its controlling instrument.</p>
  <table class="tbl"><thead><tr><th>Control</th><th class="num">Cases</th><th class="num">%</th></tr></thead>
  <tbody>{rows}</tbody></table>
</section>"""


def _footer(is_client: bool, firm: str) -> str:
    note = ("Prepared for the client. Figures are indicative and should be confirmed with the engagement team."
            if is_client else
            "Internal working document — contains process-mining mechanics not for client distribution.")
    return f'<footer><div>{_BRAND} · {_e(firm)}</div><div class="muted">{note}</div></footer>'


# --------------------------------------------------------------------------- #
# Process-flow SVG (dependency-free)
# --------------------------------------------------------------------------- #
def _flow_svg(facts: ProcessFacts) -> str:
    seq = list(facts.top_variants[0].sequence)
    hot = {b.source for b in facts.bottlenecks} | {b.target for b in facts.bottlenecks}

    per_row = 4
    bw, bh, hgap, vgap = 196, 46, 26, 44
    pad = 16
    n = len(seq)
    rows = (n + per_row - 1) // per_row

    def pos(i):
        r = i // per_row
        idx = i % per_row
        col = idx if r % 2 == 0 else (per_row - 1 - idx)  # snake
        return pad + col * (bw + hgap), pad + r * (bh + vgap)

    width = pad * 2 + per_row * bw + (per_row - 1) * hgap
    height = pad * 2 + rows * bh + (rows - 1) * vgap
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" xmlns="http://www.w3.org/2000/svg">',
             '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" '
             'orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" stroke="#94a3b8" '
             'stroke-width="1.6" stroke-linecap="round"/></marker></defs>']

    # connectors
    for i in range(n - 1):
        x1, y1 = pos(i)
        x2, y2 = pos(i + 1)
        if y1 == y2:  # same row -> horizontal
            sx = x1 + bw if x2 > x1 else x1
            ex = x2 if x2 > x1 else x2 + bw
            parts.append(f'<line x1="{sx}" y1="{y1 + bh / 2}" x2="{ex}" y2="{y2 + bh / 2}" '
                         f'stroke="#cbd5e1" stroke-width="1.6" marker-end="url(#ah)"/>')
        else:  # drop to next row (same column in snake)
            cx = x1 + bw / 2
            parts.append(f'<line x1="{cx}" y1="{y1 + bh}" x2="{cx}" y2="{y2}" '
                         f'stroke="#cbd5e1" stroke-width="1.6" marker-end="url(#ah)"/>')

    # boxes
    for i, act in enumerate(seq):
        x, y = pos(i)
        is_hot = act in hot
        fill = "#fef3e2" if is_hot else "#eef2ff"
        stroke = "#f59e0b" if is_hot else "#c7d2fe"
        txt = "#92400e" if is_hot else "#3730a3"
        label = act if len(act) <= 26 else act[:25] + "…"
        parts.append(
            f'<g><rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            f'<text x="{x + bw / 2}" y="{y + bh / 2 + 4}" text-anchor="middle" '
            f'font-family="Plus Jakarta Sans, sans-serif" font-size="12.5" font-weight="600" fill="{txt}">{_e(label)}</text></g>'
        )
    parts.append("</svg>")
    return "".join(parts)


# --------------------------------------------------------------------------- #
# tiny markdown -> html (headings, bold, lists, tables, hr, paragraphs)
# --------------------------------------------------------------------------- #
def _inline(t: str) -> str:
    t = _e(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return t


def _md_to_html(md: str) -> str:
    out: List[str] = []
    lines = md.split("\n")
    i = 0
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>"); in_ul = False
        if in_ol:
            out.append("</ol>"); in_ol = False

    while i < len(lines):
        line = lines[i].rstrip()
        # table block
        if line.strip().startswith("|") and line.strip().endswith("|"):
            close_lists()
            tbl = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl.append(lines[i].strip())
                i += 1
            out.append(_md_table(tbl))
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            close_lists()
            lvl = min(len(m.group(1)) + 1, 4)  # # -> h2 in report
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
        elif re.match(r"^\s*[-*]\s+", line):
            if not in_ul:
                close_lists(); out.append("<ul>"); in_ul = True
            item = re.sub(r"^\s*[-*]\s+", "", line)  # no backslash in f-string (py3.11)
            out.append(f"<li>{_inline(item)}</li>")
        elif re.match(r"^\s*\d+\.\s+", line):
            if not in_ol:
                close_lists(); out.append("<ol>"); in_ol = True
            item = re.sub(r"^\s*\d+\.\s+", "", line)
            out.append(f"<li>{_inline(item)}</li>")
        elif re.match(r"^-{3,}$", line.strip()):
            close_lists(); out.append("<hr/>")
        elif not line.strip():
            close_lists()
        else:
            close_lists(); out.append(f"<p>{_inline(line)}</p>")
        i += 1
    close_lists()
    return "\n".join(out)


def _md_table(rows: List[str]) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.match(r"^:?-+:?$", c or "-") for c in r)]
    if not cells:
        return ""
    head = "".join(f"<th>{_inline(c)}</th>" for c in cells[0])
    body = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in cells[1:])
    return f'<table class="tbl"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


# --------------------------------------------------------------------------- #
def _e(s: Any) -> str:
    return _html.escape(str(s))


def _fmt_hours(seconds: float) -> str:
    h = (seconds or 0) / 3600
    if h >= 24:
        return f"{h / 24:.1f} d"
    return f"{h:.1f} h"


_CSS = """
:root{--bg:#f4f6fb;--ink:#0f172a;--muted:#64748b;--line:#e2e8f0;--primary:#4f46e5;--violet:#7c3aed;--warn:#b45309}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:'Plus Jakarta Sans',Segoe UI,system-ui,sans-serif;line-height:1.55}
.page{max-width:880px;margin:24px auto;background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden;box-shadow:0 24px 60px -40px rgba(15,23,42,.4)}
.cover{padding:34px 40px 26px;background:linear-gradient(120deg,#eef2ff 0%,#f5f3ff 100%);border-bottom:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:8px;font-weight:800;letter-spacing:-.01em}
.brand .dot{width:12px;height:12px;border-radius:4px;background:var(--primary)}
.brand .firm{color:var(--muted);font-weight:600}
.cover-tag{margin-top:14px;display:inline-block;font-size:11.5px;font-weight:700;color:var(--primary);background:#e0e7ff;padding:3px 10px;border-radius:999px;text-transform:uppercase;letter-spacing:.04em}
.cover h1{margin:10px 0 4px;font-size:26px;letter-spacing:-.02em}
.cover-sub{margin:0;color:var(--muted);font-size:13.5px}
section{padding:18px 40px}
h2{font-size:16px;margin:18px 0 8px;letter-spacing:-.01em}
h3{font-size:14px;margin:14px 0 4px}
h4{font-size:12.5px;margin:10px 0 2px;text-transform:uppercase;letter-spacing:.05em;color:var(--primary)}
p{margin:6px 0;font-size:13.5px}
.muted{color:var(--muted);font-size:12.5px}
.band{display:flex;gap:22px;align-items:center;padding:18px 40px;border-bottom:1px solid var(--line);background:#fbfcff}
.band-score{display:flex;align-items:center;gap:14px}
.ring{width:74px;height:74px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(var(--primary) calc(var(--p)*1%),#e2e8f0 0)}
.ring span{width:56px;height:56px;border-radius:50%;background:#fff;display:grid;place-items:center;font-weight:800;font-size:21px}
.band-grade{font-weight:800}
.band-lbl{color:var(--muted);font-size:12px}
.band-note{color:var(--muted);font-size:13px;max-width:480px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding-top:18px}
.kpi{background:#f8fafc;border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.kpi-v{font-weight:800;font-size:22px;font-family:'JetBrains Mono',monospace}
.kpi-l{color:var(--muted);font-size:12px;margin-top:2px}
.flow{margin-top:10px;background:#fbfcff;border:1px solid var(--line);border-radius:14px;padding:16px}
.flow-map{overflow:auto}
.flow-map svg{max-width:100%;height:auto}
.tbl{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0}
.tbl th{text-align:left;color:var(--muted);font-weight:600;border-bottom:1px solid var(--line);padding:7px 8px;font-size:12px}
.tbl td{border-bottom:1px solid #f1f5f9;padding:7px 8px}
.tbl td.num,.tbl th.num{text-align:right;font-family:'JetBrains Mono',monospace}
.tbl tr.bad td:first-child{color:#b91c1c;font-weight:600}
.pill{font-size:11px;font-weight:700;color:var(--primary);background:#e0e7ff;padding:2px 9px;border-radius:999px;vertical-align:middle}
.pill.warn{color:#b91c1c;background:#fee2e2}
.brief h2{border-top:1px solid var(--line);padding-top:14px}
.internal{background:#fafafa}
footer{padding:18px 40px 26px;border-top:1px solid var(--line);display:flex;justify-content:space-between;font-size:12px;color:var(--muted);font-weight:600}
@media print{body{background:#fff}.page{box-shadow:none;border:none;margin:0;border-radius:0}section{break-inside:avoid}}
"""

_DOCUMENT = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{css}</style></head>
<body><div class="page">{body}</div></body></html>"""
