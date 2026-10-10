"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAccount } from "@/components/dashboard/AccountContext";
import { StorefrontOfferCard } from "@/components/storefront/StorefrontOfferCard";
import { CheckIcon, CopyIcon, StoreIcon } from "@/components/icons";
import { api, type Storefront } from "@/lib/api";

export default function StorefrontPage() {
  const account = useAccount();
  const [storefront, setStorefront] = useState<Storefront | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [storeUrl, setStoreUrl] = useState("");

  useEffect(() => {
    setStoreUrl(`${window.location.origin}/store/${account.id}`);
  }, [account.id]);

  useEffect(() => {
    let cancelled = false;
    api
      .storefront(account.id)
      .then((s) => !cancelled && setStorefront(s))
      .catch(() => !cancelled && setError("Couldn't load your storefront. Try refreshing."));
    return () => {
      cancelled = true;
    };
  }, [account.id]);

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">Storefront</h1>
      <p className="mt-1 text-sm text-navy-400">
        One shareable page with every offer you&rsquo;re promoting — send it instead of sharing links one by one.
      </p>

      <div className="mt-6 flex items-center gap-3 rounded-2xl bg-white p-4 shadow-card">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-50">
          <StoreIcon className="h-5 w-5 text-navy-300" />
        </div>
        <div className="min-w-0 flex-1 truncate text-sm font-medium text-navy-600">{storeUrl}</div>
        <button
          type="button"
          onClick={() => {
            navigator.clipboard.writeText(storeUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 1800);
          }}
          className="flex shrink-0 items-center gap-1.5 rounded-full border border-navy-100 px-3.5 py-2 text-xs font-bold text-navy-600 transition hover:bg-slate-50"
        >
          {copied ? <CheckIcon className="h-3.5 w-3.5" /> : <CopyIcon className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>
        <a
          href={storeUrl}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 rounded-full bg-cta-gradient px-4 py-2 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105"
        >
          View
        </a>
      </div>

      {error && <p className="mt-6 text-sm font-medium text-red-500">{error}</p>}

      <h2 className="mt-8 text-sm font-bold text-navy-900">Preview</h2>
      <div className="mt-3">
        {storefront ? (
          storefront.offers.length > 0 ? (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {storefront.offers.map((offer) => (
                <StorefrontOfferCard key={offer.tracking_link_id} offer={offer} />
              ))}
            </div>
          ) : (
            <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-navy-100 bg-white text-center">
              <StoreIcon className="h-8 w-8 text-navy-200" />
              <p className="text-sm font-medium text-navy-400">
                Your storefront is empty — create a tracking link to add an offer here.
              </p>
              <Link
                href="/dashboard/offers"
                className="rounded-full bg-cta-gradient px-5 py-2 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105"
              >
                Find an offer to promote
              </Link>
            </div>
          )
        ) : (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-64 animate-pulse rounded-2xl bg-white shadow-card" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
