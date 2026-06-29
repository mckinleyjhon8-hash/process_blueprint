#!/usr/bin/env python
"""
run_phase1.py — CLI to run the Phase-1 engine end-to-end.

Usage:
    python scripts/run_phase1.py                      # runs on a generated sample log
    python scripts/run_phase1.py path/to/log.csv      # runs on your event log
    python scripts/run_phase1.py log.csv --process-type "Order-to-Cash" --json out.json
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

# Windows consoles default to cp1252 and choke on arrows/checkmarks.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Make src/ importable when run directly.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, _ROOT)

from process_blueprint import analyze  # noqa: E402


def _make_sample() -> str:
    from tests.sample_log import write_sample_csv

    path = os.path.join(tempfile.gettempdir(), "pb_sample_p2p.csv")
    write_sample_csv(path)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description="Process Blueprint — Phase 1 runner")
    ap.add_argument("log", nargs="?", help="CSV/XES event log (omit to use a sample)")
    ap.add_argument("--process-type", default="Procure-to-Pay")
    ap.add_argument("--algorithm", default="inductive", choices=["inductive", "heuristics"])
    ap.add_argument("--json", help="Write ProcessFacts JSON to this path")
    args = ap.parse_args()

    log_path = args.log or _make_sample()
    if not args.log:
        print(f"[i] No log given — generated sample at {log_path}\n")

    facts = analyze(log_path, process_type=args.process_type, algorithm=args.algorithm)

    print("=" * 60)
    print(f"ProcessFacts — {facts.process_type}")
    print("=" * 60)
    print(f"  cases ............ {facts.n_cases}")
    print(f"  events ........... {facts.n_events}")
    print(f"  activities ....... {facts.n_activities}")
    print(f"  variants ......... {facts.n_variants}")
    print(f"  avg cycle time ... {facts.avg_cycle_time_hours} h")
    print(f"  model ............ {facts.model.algorithm} "
          f"(fitness={facts.model.fitness}, precision={facts.model.precision}, "
          f"simplicity={facts.model.simplicity})")
    print(f"  top bottleneck ... "
          + (f"{facts.bottlenecks[0].source} -> {facts.bottlenecks[0].target} "
             f"({facts.bottlenecks[0].mean_wait_seconds/3600:.1f} h)"
             if facts.bottlenecks else "none"))
    print(f"  rework ........... {facts.rework_activities or 'none'}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            fh.write(facts.to_json())
        print(f"\n[OK] Wrote ProcessFacts JSON -> {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
