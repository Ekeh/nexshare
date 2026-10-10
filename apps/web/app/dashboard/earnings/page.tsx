"use client";

import { useEffect, useMemo, useState } from "react";
import { StatCard } from "@/components/dashboard/StatCard";
import { COMMISSION_STATUS_META } from "@/components/dashboard/commissionStatus";
import { api, formatMoney, type Commission } from "@/lib/api";

const SUMMARY_STATUSES = ["pending", "approved", "available", "paid"] as const;

export default function EarningsPage() {
  const [commissions, setCommissions] = useState<Commission[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .commissions()
      .then((c) => !cancelled && setCommissions(c))
      .catch(() => !cancelled && setError("Couldn't load your earnings. Try refreshing."));
    return () => {
      cancelled = true;
    };
  }, []);

  const currency = commissions?.[0]?.currency ?? "USD";
  const sums = useMemo(() => {
    const totals: Record<string, number> = { pending: 0, approved: 0, available: 0, paid: 0 };
    for (const c of commissions ?? []) {
      if (c.status in totals) totals[c.status] += c.amount_minor_units;
    }
    return totals;
  }, [commissions]);

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">Earnings</h1>
      <p className="mt-1 text-sm text-navy-400">Every commission, and where it is in the payout pipeline.</p>

      {error && <p className="mt-6 text-sm font-medium text-red-500">{error}</p>}

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {commissions ? (
          SUMMARY_STATUSES.map((status) => (
            <StatCard
              key={status}
              value={formatMoney({ amount_minor_units: sums[status], currency, change_pct: null })}
              label={
                status === "available"
                  ? "Available to Withdraw"
                  : status === "paid"
                    ? "Paid Out"
                    : COMMISSION_STATUS_META[status].label
              }
            />
          ))
        ) : (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[104px] animate-pulse rounded-2xl bg-white shadow-card" />
          ))
        )}
      </div>

      <div className="mt-6 flex flex-col gap-3">
        {commissions ? (
          commissions.length > 0 ? (
            commissions.map((c) => {
              const meta = COMMISSION_STATUS_META[c.status];
              return (
                <div key={c.id} className="flex items-center gap-4 rounded-2xl bg-white p-4 shadow-card">
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-bold text-navy-900">{c.offer_title}</div>
                    <div className="mt-0.5 text-xs font-medium text-navy-400">
                      {new Date(c.created_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </div>
                  </div>
                  <div className="text-sm font-semibold text-navy-900">
                    {formatMoney({ amount_minor_units: c.amount_minor_units, currency: c.currency, change_pct: null })}
                  </div>
                  <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${meta.bg} ${meta.fg}`}>
                    {meta.label}
                  </span>
                </div>
              );
            })
          ) : (
            <p className="text-sm font-medium text-navy-300">
              No commissions yet — share an offer to start earning.
            </p>
          )
        ) : (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[68px] animate-pulse rounded-2xl bg-white shadow-card" />
          ))
        )}
      </div>
    </div>
  );
}
