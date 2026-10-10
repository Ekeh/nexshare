"use client";

import { useEffect, useState } from "react";
import { useAccount } from "@/components/dashboard/AccountContext";
import { StatCard } from "@/components/dashboard/StatCard";
import { api, formatMoney, type PromoterStats } from "@/lib/api";

export default function DashboardHomePage() {
  const account = useAccount();
  const [stats, setStats] = useState<PromoterStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const firstName = account.full_name.split(" ")[0] || account.email;

  useEffect(() => {
    let cancelled = false;
    api
      .promoterStats()
      .then((s) => !cancelled && setStats(s))
      .catch(() => !cancelled && setError("Couldn't load your stats. Try refreshing."));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">
        Welcome back, {firstName}! <span aria-hidden>👋</span>
      </h1>
      <p className="mt-1 text-sm text-navy-400">Let&rsquo;s keep sharing and earning.</p>

      {error && <p className="mt-6 text-sm font-medium text-red-500">{error}</p>}

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats ? (
          <>
            <StatCard
              value={formatMoney(stats.today_earnings)}
              label="Today's Earnings"
              deltaPct={stats.today_earnings.change_pct}
            />
            <StatCard
              value={formatMoney(stats.month_earnings)}
              label="This Month"
              deltaPct={stats.month_earnings.change_pct}
            />
            <StatCard value={formatMoney(stats.pending)} label="Pending" deltaPct={stats.pending.change_pct} />
            <StatCard
              value={formatMoney(stats.total_earned)}
              label="Total Earned"
              deltaPct={stats.total_earned.change_pct}
            />
          </>
        ) : (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[104px] animate-pulse rounded-2xl bg-white shadow-card" />
          ))
        )}
      </div>
    </div>
  );
}
