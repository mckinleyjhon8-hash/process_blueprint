"""
freight_log.py — a realistic UK road-freight brokerage event log, modelled on the
asset-light broker SOP (8 stages: Inquiry → Quote → Book-in → Carrier Procurement
→ Compliance Pack-out → Execution → POD/Billing/Claims → Finance/KPI close).

It mirrors the SOP's real branching — high-risk sector EDD, lost quotes, new-carrier
KYC, Tier-2 load-board fallback, hazmat/ADR, cross-border customs, in-transit
exceptions, damage→claims, refusals→returns — with named roles (org:resource) and
business-hours timing.

It also INJECTS five SOP compliance deviations so the analysis has something real
to catch:
  1. Sanctions Check skipped on a booking            (§1.2 must run every booking)
  2. OCRS Check skipped before award                 (§4.7 OCRS health gate)
  3. CMR issued AFTER pickup                          (§5.1 CMR must be pre-pickup)
  4. Carrier KYC done AFTER award                     (§2.3/§4 KYC must precede award)
  5. Claim handled later than the 9-day window        (§7.6 BIFA STC claim window)

`check_sop_compliance(df)` is a lightweight rule-based conformance check (the kind
a full declarative-conformance layer would generalise) that detects these from the
event log and reports counts + example cases.
"""

from __future__ import annotations

import datetime as dt
import random
from typing import Any, Dict, List, Tuple

import pandas as pd

from tests.enterprise_log import _biz_advance  # reuse the business-hours clock

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"
RES = "org:resource"

CLAIM_WINDOW_DAYS = 9  # BIFA STC international claim window (§7.6)


def _trace(rng: random.Random, dev: bool = True) -> List[Tuple[str, str, float]]:
    """Return [(activity, resource, wait_hours_before), ...] for one freight job.

    `dev=False` produces a clean, fully-conformant "to-be" trace (no injected SOP
    breaches) — useful as a reference for BPMN/declarative conformance.
    """
    steps: List[Tuple[str, str, float]] = []

    def add(a: str, role: str, lo: float, hi: float) -> None:
        steps.append((a, role, rng.uniform(lo, hi)))

    # --- Stage 1: Inquiry & CDD ---
    add("Capture Inquiry", "Sales Exec", 0, 1)
    add("Customer Due Diligence", "Compliance", 0.5, 6)
    if rng.random() < 0.18:  # high-risk sector -> EDD
        add("Enhanced Due Diligence", "Compliance", 4, 24)
    skip_sanctions = dev and rng.random() < 0.06  # DEVIATION 1
    if not skip_sanctions:
        add("Sanctions Check", "Compliance", 0.2, 2)

    # --- Stage 2: Quote & Contract ---
    add("Build Quote", "Pricing Analyst", 0.5, 4)
    add("Issue Quote", "Sales Exec", 0.2, 2)
    if rng.random() < 0.15:  # lost quote -> job ends
        add("Quote Rejected", "Sales Exec", 1, 8)
        return steps
    add("Customer Accepts Quote", "Customer Service", 2, 48)

    # --- Stage 3: Order Book-in ---
    add("Receive Booking", "Customer Service", 0.2, 4)
    add("Acknowledge Order", "Customer Service", 0.1, 1)
    add("Generate Job Number", "TMS Admin", 0.05, 0.3)
    add("Issue Order Confirmation", "Customer Service", 0.2, 2)

    # --- Stage 4: Carrier Procurement ---
    new_carrier = rng.random() < 0.22
    kyc_before_award = not (dev and new_carrier and rng.random() < 0.05)  # DEVIATION 4
    if new_carrier and kyc_before_award:
        add("Carrier KYC", "Compliance", 4, 36)
    add("Source Capacity", "Capacity Buyer", 0.2, 3)
    if rng.random() < 0.25:  # Tier-2 load-board fallback
        add("Broadcast to Load Board", "Capacity Buyer", 0.5, 6)
    if rng.random() < 0.08:  # carrier refused -> re-source (rework)
        add("Reject Carrier", "Compliance", 0.5, 4)
        add("Source Capacity", "Capacity Buyer", 0.5, 6)
    add("Negotiate Buy Rate", "Capacity Buyer", 0.2, 2)
    add("Award Carrier", "Capacity Buyer", 0.1, 1)
    if new_carrier and not kyc_before_award:
        add("Carrier KYC", "Compliance", 4, 36)  # out-of-order (DEVIATION 4)
    if (not dev) or rng.random() >= 0.07:  # DEVIATION 2: skip OCRS ~7%
        add("OCRS Check", "Capacity Buyer", 0.1, 1)

    # --- Stage 5: Compliance Pack-out ---
    cross_border = rng.random() < 0.30
    cmr_after_pickup = dev and cross_border and rng.random() < 0.08  # DEVIATION 3
    if cross_border and not cmr_after_pickup:
        add("Issue CMR", "Operations Admin", 0.3, 3)
    elif not cross_border:
        add("Issue Consignment Note", "Operations Admin", 0.3, 3)
    if rng.random() < 0.15:  # hazmat / ADR
        add("Dangerous Goods Declaration", "Compliance", 0.5, 4)
    if cross_border:
        add("Customs Entry CDS ENS", "Customs Desk", 2, 24)
    add("Driver Hours Check", "Compliance", 0.1, 1)
    add("Photo Evidence at Collection", "Operations Admin", 0.1, 0.5)

    # --- Stage 6: Execution & Delivery ---
    add("Confirm Pickup", "Capacity Buyer", 1, 12)
    if cmr_after_pickup:
        add("Issue CMR", "Operations Admin", 0.3, 3)  # out-of-order (DEVIATION 3)
    add("Status Polling", "Tracking", 2, 24)
    add("ETA Update", "Account Exec", 1, 12)
    if rng.random() < 0.22:
        add("Exception Handling", "Operations Controller", 1, 18)
    damaged = rng.random() < 0.12
    refused = rng.random() < 0.05
    add("Confirm Delivery", "Account Exec", 4, 72)

    # --- Stage 7: POD, Billing, Claims, Returns ---
    add("Capture POD", "Operations Admin", 0.5, 8)
    if damaged:  # claims are triggered at delivery and handled within the SOP window
        late = dev and rng.random() < 0.30  # DEVIATION 5: late claim
        wait = rng.uniform(96, 180) if late else rng.uniform(4, 20)
        steps.append(("Handle Claim", "Claims Handler", wait))
    if refused:
        add("Process Return", "Returns", 4, 48)
    add("Raise Carrier Invoice", "Finance AR", 4, 48)
    add("Raise Customer Invoice", "Finance AR", 0.5, 24)
    add("Reconcile Invoices", "Finance Controller", 1, 24)

    # --- Stage 8: Finance & KPI close ---
    add("Post Transactions", "Finance", 2, 48)
    add("Close Job", "Operations Manager", 1, 24)
    return steps


def build_freight_log(n_cases: int = 500, seed: int = 11, deviations: bool = True) -> pd.DataFrame:
    """Return a normalised UK freight-brokerage event log with named resources.

    `deviations=False` yields a clean, fully-conformant "to-be" log.
    """
    rng = random.Random(seed)
    base = dt.datetime(2026, 1, 5, 9, 0, 0)  # a Monday
    rows = []
    for i in range(n_cases):
        case = f"JOB-{440000 + i}"
        t = _biz_advance(base, rng.uniform(0, 180 * 8))
        for act, role, wait in _trace(rng, dev=deviations):
            t = _biz_advance(t, wait)
            rows.append({CASE: case, ACT: act, TS: t, RES: role})
    df = pd.DataFrame(rows)
    df[TS] = pd.to_datetime(df[TS], utc=True)
    return df


def write_freight_csv(path: str, n_cases: int = 500, seed: int = 11) -> str:
    build_freight_log(n_cases=n_cases, seed=seed).to_csv(path, index=False)
    return path


# --------------------------------------------------------------------------- #
# Rule-based SOP compliance check (a tiny declarative-conformance layer)
# --------------------------------------------------------------------------- #
def check_sop_compliance(df: pd.DataFrame) -> Dict[str, Any]:
    """Detect SOP control breaches via the declarative compliance engine."""
    from process_blueprint.compliance import check_rules, FREIGHT_SOP_RULES

    return check_rules(df, FREIGHT_SOP_RULES)
