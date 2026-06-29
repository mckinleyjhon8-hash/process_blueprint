"""
enterprise_log.py — a realistic, comprehensive Procure-to-Pay event log.

Far richer than the simple fixture: tiered approvals, requisition rejections,
PO cancellations, supplier clarification, goods returns/re-inspection, invoice
exceptions with re-matching, escalations, early terminations, named resources,
and business-hours timestamps (Mon-Fri 09:00-17:00, weekends skipped).

Produces dozens-to-hundreds of variants with real bottlenecks and rework — the
kind of log that actually stresses discovery, conformance and diagnostics.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import List, Tuple

import pandas as pd

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"
RES = "org:resource"

_DAY_START, _DAY_END = 9, 17  # business hours


def _biz_advance(t: dt.datetime, hours: float) -> dt.datetime:
    """Advance `hours` of elapsed work time within Mon-Fri 09:00-17:00."""
    remaining = float(hours)
    cur = t
    guard = 0
    while remaining > 1e-9 and guard < 10000:
        guard += 1
        if cur.weekday() >= 5:  # weekend -> Monday 09:00
            cur = (cur + dt.timedelta(days=7 - cur.weekday())).replace(
                hour=_DAY_START, minute=0, second=0, microsecond=0
            )
            continue
        if cur.hour < _DAY_START:
            cur = cur.replace(hour=_DAY_START, minute=0, second=0, microsecond=0)
        elif cur.hour >= _DAY_END:
            cur = (cur + dt.timedelta(days=1)).replace(
                hour=_DAY_START, minute=0, second=0, microsecond=0
            )
            continue
        end_of_day = cur.replace(hour=_DAY_END, minute=0, second=0, microsecond=0)
        avail = (end_of_day - cur).total_seconds() / 3600.0
        step = min(remaining, avail)
        cur = cur + dt.timedelta(hours=step)
        remaining -= step
        if remaining > 1e-9:
            cur = (cur + dt.timedelta(days=1)).replace(
                hour=_DAY_START, minute=0, second=0, microsecond=0
            )
    return cur


def _trace(rng: random.Random) -> List[Tuple[str, str, float]]:
    """Return [(activity, resource, wait_hours_before), ...] for one case."""
    steps: List[Tuple[str, str, float]] = []

    def add(a: str, role: str, lo: float, hi: float) -> None:
        steps.append((a, role, rng.uniform(lo, hi)))

    add("Create Purchase Requisition", "Requester", 0, 2)
    add("Approve Requisition", "Manager", 2, 20)

    if rng.random() < 0.07:  # requisition rejected
        add("Reject Requisition", "Manager", 1, 4)
        if rng.random() < 0.5:  # resubmit
            add("Create Purchase Requisition", "Requester", 4, 24)
            add("Approve Requisition", "Manager", 2, 16)
        else:
            return steps  # abandoned

    add("Create Purchase Order", "Buyer", 1, 6)
    add("Approve Purchase Order", "Manager", 2, 24)
    if rng.random() < 0.12:  # high-value -> second approval
        add("Approve Purchase Order", "Senior Manager", 4, 36)

    if rng.random() < 0.05:  # cancelled after approval
        add("Cancel Purchase Order", "Buyer", 1, 8)
        return steps

    add("Send PO to Supplier", "Buyer", 0, 2)
    if rng.random() < 0.72:
        add("Receive Order Confirmation", "Supplier", 4, 56)
    else:
        add("Request Supplier Clarification", "Buyer", 2, 12)
        add("Receive Order Confirmation", "Supplier", 8, 80)

    add("Receive Goods", "Warehouse", 24, 140)
    add("Inspect Goods", "Quality", 1, 8)
    if rng.random() < 0.16:  # failed inspection -> return + re-receive
        add("Return Goods", "Warehouse", 2, 12)
        add("Receive Goods", "Warehouse", 24, 110)
        add("Inspect Goods", "Quality", 1, 8)

    add("Receive Invoice", "AP Clerk", 2, 80)
    add("Match Invoice", "AP Clerk", 1, 8)
    if rng.random() < 0.24:  # invoice exception -> resolve -> re-match
        add("Resolve Invoice Exception", "AP Clerk", 4, 56)
        add("Match Invoice", "AP Clerk", 1, 8)
        if rng.random() < 0.18:  # escalated second exception
            add("Resolve Invoice Exception", "AP Manager", 4, 48)
            add("Match Invoice", "AP Clerk", 1, 8)

    add("Approve Payment", "AP Manager", 2, 28)
    add("Pay Invoice", "AP Clerk", 1, 10)
    return steps


def build_enterprise_log(n_cases: int = 3000, seed: int = 7) -> pd.DataFrame:
    """Return a rich, normalised P2P event log with named resources."""
    rng = random.Random(seed)
    base = dt.datetime(2026, 1, 5, 9, 0, 0)  # a Monday
    rows = []
    for i in range(n_cases):
        case = f"PO-{100000 + i}"
        t = _biz_advance(base, rng.uniform(0, 180 * 8))  # arrival over ~180 work-days
        for act, role, wait in _trace(rng):
            t = _biz_advance(t, wait)
            rows.append({CASE: case, ACT: act, TS: t, RES: role})
    df = pd.DataFrame(rows)
    df[TS] = pd.to_datetime(df[TS], utc=True)
    return df


def write_enterprise_csv(path: str, n_cases: int = 3000, seed: int = 7) -> str:
    build_enterprise_log(n_cases=n_cases, seed=seed).to_csv(path, index=False)
    return path
