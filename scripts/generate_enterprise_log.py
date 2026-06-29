#!/usr/bin/env python
"""
generate_enterprise_log.py — write a comprehensive enterprise P2P CSV.

Usage:
    python scripts/generate_enterprise_log.py                 # 3000 cases -> data/enterprise_p2p.csv
    python scripts/generate_enterprise_log.py --cases 5000 --out data/big.csv
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.enterprise_log import write_enterprise_csv  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a comprehensive P2P event log")
    ap.add_argument("--cases", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=os.path.join("data", "enterprise_p2p.csv"))
    args = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    write_enterprise_csv(args.out, n_cases=args.cases, seed=args.seed)
    size = os.path.getsize(args.out)
    print(f"[OK] Wrote {args.cases} cases -> {args.out} ({size/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
