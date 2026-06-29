import { ShieldAlert, ShieldCheck } from "lucide-react";
import type { ComplianceReport } from "@/lib/types";

const LABELS: Record<string, string> = {
  sanctions_check_missing: "Sanctions check skipped on a booking · SOP 1.2",
  ocrs_check_missing: "OCRS health gate skipped before award · SOP 4.7",
  cmr_after_pickup: "CMR issued after pickup · SOP 5.1",
  kyc_after_award: "Carrier KYC after award · SOP 2.3/4",
  claim_outside_9_day_window: "Claim outside BIFA 9-day window · SOP 7.6",
};

export function Compliance({ report }: { report: ComplianceReport }) {
  const rows = Object.entries(report.rules);
  const total = rows.reduce((s, [, r]) => s + r.violations, 0);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-danger/12 text-danger">
            <ShieldAlert size={16} />
          </span>
          <div>
            <h2 className="text-[14px] font-bold text-fg">SOP compliance check</h2>
            <p className="text-[11.5px] text-muted">Rule-based conformance vs the documented SOP</p>
          </div>
        </div>
        <span className="rounded-full bg-danger/12 px-2.5 py-1 text-[11px] font-semibold text-danger ring-1 ring-inset ring-danger/25">
          {total} breaches across {report.n_cases} jobs
        </span>
      </div>

      <div className="space-y-2">
        {rows.map(([rule, r]) => {
          const breached = r.violations > 0;
          return (
            <div
              key={rule}
              className="flex items-center justify-between gap-3 rounded-xl border border-line bg-panel-2/50 px-3 py-2.5"
            >
              <div className="flex min-w-0 items-center gap-2.5">
                {breached ? (
                  <ShieldAlert size={15} className="shrink-0 text-danger" />
                ) : (
                  <ShieldCheck size={15} className="shrink-0 text-success" />
                )}
                <span className="truncate text-[13px] text-fg-2">{LABELS[rule] ?? rule}</span>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <span
                  className={
                    "font-mono text-[13px] font-bold " + (breached ? "text-danger" : "text-success")
                  }
                >
                  {r.violations}
                </span>
                <span className="text-[11px] text-muted">({r.pct_of_cases}%)</span>
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-[11px] leading-relaxed text-muted">
        Detected directly from the event log — these are control breaches an HMRC, Traffic
        Commissioner, ICO or CMA audit would flag, each citing its controlling instrument.
      </p>
    </div>
  );
}
