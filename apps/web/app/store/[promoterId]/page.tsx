"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { StorefrontOfferCard } from "@/components/storefront/StorefrontOfferCard";
import { api, ApiError, type Storefront } from "@/lib/api";

export default function StorefrontPage() {
  const params = useParams<{ promoterId: string }>();
  const [storefront, setStorefront] = useState<Storefront | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .storefront(params.promoterId)
      .then((s) => !cancelled && setStorefront(s))
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) setNotFound(true);
      });
    return () => {
      cancelled = true;
    };
  }, [params.promoterId]);

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-navy-100 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link href="/">
            <Logo dark tagline={false} />
          </Link>
        </div>
      </header>

      <div className="mx-auto max-w-5xl px-6 py-10">
        {notFound ? (
          <div className="flex h-64 flex-col items-center justify-center gap-2 text-center">
            <p className="text-lg font-bold text-navy-900">Storefront not found</p>
            <p className="text-sm font-medium text-navy-400">This promoter&rsquo;s store doesn&rsquo;t exist or is unavailable.</p>
          </div>
        ) : storefront ? (
          <>
            <h1 className="text-2xl font-extrabold text-navy-900">{storefront.promoter_name}&rsquo;s Store</h1>
            <p className="mt-1 text-sm text-navy-400">Hand-picked deals, shared by {storefront.promoter_name}.</p>

            {storefront.offers.length > 0 ? (
              <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {storefront.offers.map((offer) => (
                  <StorefrontOfferCard key={offer.tracking_link_id} offer={offer} />
                ))}
              </div>
            ) : (
              <div className="mt-8 flex h-48 flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-navy-100 bg-white text-center">
                <p className="text-sm font-medium text-navy-400">No deals here yet — check back soon.</p>
              </div>
            )}
          </>
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-64 animate-pulse rounded-2xl bg-white shadow-card" />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
