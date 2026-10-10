"use client";

import { useEffect, useState } from "react";
import { ClicksVsConversionsChart } from "@/components/dashboard/ClicksVsConversionsChart";
import { StatCard } from "@/components/dashboard/StatCard";
import { TopSources } from "@/components/dashboard/TopSources";
import { api, formatMoney, type Analytics } from "@/lib/api";

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .analytics()
      .then((a) => !cancelled && setData(a))
      .catch(() => !cancelled && setError("Couldn't load analytics. Try refreshing."));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">Analytics</h1>
      <p className="mt-1 text-sm text-navy-400">Performance overview — last 7 days.</p>

      {error && <p className="mt-6 text-sm font-medium text-red-500">{error}</p>}

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {data ? (
          <>
            <StatCard value={data.total_clicks.toLocaleString()} label="Total Clicks" deltaPct={data.total_clicks_change_pct} />
            <StatCard value={data.conversions.toLocaleString()} label="Conversions" deltaPct={data.conversions_change_pct} />
            <StatCard value={`${data.conversion_rate}%`} label="Conversion Rate" deltaPct={data.conversion_rate_change_pct} />
            <StatCard
              value={formatMoney({ amount_minor_units: data.total_commission_minor_units, currency: data.currency, change_pct: null })}
              label="Commission Earned"
              deltaPct={data.total_commission_change_pct}
            />
          </>
        ) : (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[104px] animate-pulse rounded-2xl bg-white shadow-card" />
          ))
        )}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr,1fr]">
        <section className="rounded-2xl bg-white p-5 shadow-card">
          <h2 className="text-sm font-bold text-navy-900">Clicks vs Conversions</h2>
          {data ? (
            <div className="mt-4">
              <ClicksVsConversionsChart series={data.series} />
            </div>
          ) : (
            <div className="mt-4 h-56 animate-pulse rounded-xl bg-slate-50" />
          )}
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-card">
          <h2 className="text-sm font-bold text-navy-900">Top Sources</h2>
          <div className="mt-4">
            {data ? <TopSources sources={data.top_sources} /> : <div className="h-40 animate-pulse rounded-xl bg-slate-50" />}
          </div>
        </section>
      </div>
    </div>
  );
}
