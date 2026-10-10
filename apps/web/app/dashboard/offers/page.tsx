"use client";

import { useEffect, useMemo, useState } from "react";
import { OfferCard } from "@/components/dashboard/OfferCard";
import { categoryFor } from "@/components/dashboard/offerCategories";
import { api, type Offer } from "@/lib/api";

export default function FindOffersPage() {
  const [offers, setOffers] = useState<Offer[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeType, setActiveType] = useState<string>("all");

  useEffect(() => {
    let cancelled = false;
    api
      .offers()
      .then((o) => !cancelled && setOffers(o))
      .catch(() => !cancelled && setError("Couldn't load offers. Try refreshing."));
    return () => {
      cancelled = true;
    };
  }, []);

  const types = useMemo(() => Array.from(new Set((offers ?? []).map((o) => o.offer_type))), [offers]);
  const visible = useMemo(
    () => (activeType === "all" ? offers ?? [] : (offers ?? []).filter((o) => o.offer_type === activeType)),
    [offers, activeType]
  );

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">Find Offers</h1>
      <p className="mt-1 text-sm text-navy-400">Choose an offer to promote and start earning.</p>

      {offers && offers.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2">
          <FilterPill label="All" active={activeType === "all"} onClick={() => setActiveType("all")} />
          {types.map((type) => (
            <FilterPill
              key={type}
              label={categoryFor(type).label}
              active={activeType === type}
              onClick={() => setActiveType(type)}
            />
          ))}
        </div>
      )}

      {error && <p className="mt-6 text-sm font-medium text-red-500">{error}</p>}

      <div className="mt-6 flex flex-col gap-3">
        {offers ? (
          visible.length > 0 ? (
            visible.map((offer) => <OfferCard key={offer.id} offer={offer} />)
          ) : (
            !error && <p className="text-sm font-medium text-navy-300">No offers in this category yet.</p>
          )
        ) : (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[82px] animate-pulse rounded-2xl bg-white shadow-card" />
          ))
        )}
      </div>
    </div>
  );
}

function FilterPill({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-4 py-1.5 text-xs font-bold transition ${
        active ? "bg-navy-900 text-white" : "border border-navy-100 bg-white text-navy-400 hover:bg-slate-50"
      }`}
    >
      {label}
    </button>
  );
}
