"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { MyLinksList } from "@/components/dashboard/MyLinksList";
import { ShareEarnPanel } from "@/components/dashboard/ShareEarnPanel";
import { api, type Offer, type TrackingLink } from "@/lib/api";

export default function LinksPage() {
  // useSearchParams opts the tree into client rendering — Next requires a
  // Suspense boundary around it so the rest of the route isn't forced
  // fully dynamic too.
  return (
    <Suspense fallback={null}>
      <LinksRoute />
    </Suspense>
  );
}

function LinksRoute() {
  const searchParams = useSearchParams();
  const offerId = searchParams.get("offer");

  if (offerId) {
    return <ShareEarnRoute offerId={offerId} />;
  }
  return <MyLinksRoute />;
}

function MyLinksRoute() {
  const [links, setLinks] = useState<TrackingLink[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .trackingLinks()
      .then((l) => !cancelled && setLinks(l))
      .catch(() => !cancelled && setError("Couldn't load your links. Try refreshing."));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">My Links</h1>
      <p className="mt-1 text-sm text-navy-400">Your tracking links, ready to share.</p>

      {error && <p className="mt-6 text-sm font-medium text-red-500">{error}</p>}

      <div className="mt-6">
        {links ? (
          <MyLinksList links={links} />
        ) : (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-[82px] animate-pulse rounded-2xl bg-white shadow-card" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ShareEarnRoute({ offerId }: { offerId: string }) {
  const [offer, setOffer] = useState<Offer | null>(null);
  const [link, setLink] = useState<TrackingLink | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.offers(), api.createTrackingLink(offerId)])
      .then(([offers, trackingLink]) => {
        if (cancelled) return;
        const found = offers.find((o) => o.id === offerId);
        if (!found) {
          setError("That offer couldn't be found.");
          return;
        }
        setOffer(found);
        setLink(trackingLink);
      })
      .catch(() => !cancelled && setError("Couldn't set up your tracking link. Try again."));
    return () => {
      cancelled = true;
    };
  }, [offerId]);

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">Share &amp; Earn</h1>
      <p className="mt-1 text-sm text-navy-400">
        {offer ? `Promote "${offer.title}" and earn on every conversion.` : "Setting up your tracking link…"}
      </p>

      {error && <p className="mt-6 text-sm font-medium text-red-500">{error}</p>}

      <div className="mt-6">
        {offer && link ? (
          <ShareEarnPanel offer={offer} link={link} />
        ) : (
          !error && (
            <div className="grid gap-6 lg:grid-cols-[1.1fr,0.9fr]">
              <div className="h-64 animate-pulse rounded-2xl bg-white shadow-card" />
              <div className="h-64 animate-pulse rounded-2xl bg-white shadow-card" />
            </div>
          )
        )}
      </div>
    </div>
  );
}
