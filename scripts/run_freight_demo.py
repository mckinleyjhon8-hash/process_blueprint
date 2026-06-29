#!/usr/bin/env python
"""
run_freight_demo.py — mine the UK freight-brokerage SOP log and run the SOP
compliance check, all in one go.

    python scripts/run_freight_demo.py            # 500 cases
    python scripts/run_freight_demo.py --cases 800 --json data/freight_facts.json
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, _ROOT)

from process_blueprint.engine import analyze_dataframe          # noqa: E402
from tests.freight_log import build_freight_log, check_sop_compliance  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="UK freight brokerage SOP demo")
    ap.add_argument("--cases", type=int, default=500)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--json", help="Write ProcessFacts JSON here")
    args = ap.parse_args()

    df = build_freight_log(n_cases=args.cases, seed=args.seed)
    facts = analyze_dataframe(df, process_type="UK Freight Brokerage")

    print("=" * 66)
    print("ProcessFacts — UK Freight Brokerage")
    print("=" * 66)
    print(f"  cases ............ {facts.n_cases}")
    print(f"  events ........... {facts.n_events}")
    print(f"  activities ....... {facts.n_activities}")
    print(f"  variants ......... {facts.n_variants}")
    print(f"  avg cycle time ... {facts.avg_cycle_time_hours} h "
          f"({facts.avg_cycle_time_hours / 24:.1f} days)")
    print(f"  model ............ {facts.model.algorithm} "
          f"(fitness={facts.model.fitness}, precision={facts.model.precision})")
    print("  top bottlenecks:")
    for b in facts.bottlenecks[:4]:
        print(f"     {b.source} -> {b.target}: {b.mean_wait_seconds / 3600:.0f} h "
              f"(n={b.occurrences})")
    print(f"  rework ........... "
          + ", ".join(f"{k} x{v}" for k, v in list(facts.rework_activities.items())[:5]))

    print("\n" + "=" * 66)
    print("SOP compliance check (rule-based conformance)")
    print("=" * 66)
    report = check_sop_compliance(df)
    labels = {
        "sanctions_check_missing": "Sanctions Check skipped on a booking (SOP 1.2)",
        "ocrs_check_missing": "OCRS health gate skipped before award (SOP 4.7)",
        "cmr_after_pickup": "CMR issued after pickup (SOP 5.1)",
        "kyc_after_award": "Carrier KYC after award (SOP 2.3/4)",
        "claim_outside_9_day_window": "Claim outside BIFA 9-day window (SOP 7.6)",
    }
    for rule, info in report["rules"].items():
        flag = "!!" if info["violations"] else "ok"
        print(f"  [{flag}] {labels[rule]:48} "
              f"{info['violations']:>4} cases ({info['pct_of_cases']}%)")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            fh.write(facts.to_json())
        print(f"\n[OK] Wrote ProcessFacts JSON -> {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
