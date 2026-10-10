"use client";

import Link from "next/link";
import { useState } from "react";
import { CheckIcon, CopyIcon, LinkIcon } from "@/components/icons";
import type { TrackingLink } from "@/lib/api";

export function MyLinksList({ links }: { links: TrackingLink[] }) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (links.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-navy-100 bg-white text-center">
        <LinkIcon className="h-8 w-8 text-navy-200" />
        <p className="text-sm font-medium text-navy-400">
          You haven&rsquo;t created any tracking links yet.
        </p>
        <Link
          href="/dashboard/offers"
          className="rounded-full bg-cta-gradient px-5 py-2 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105"
        >
          Find an offer to promote
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {links.map((link) => (
        <div key={link.id} className="flex items-center gap-4 rounded-2xl bg-white p-4 shadow-card">
          {link.offer_image_url ? (
            <img src={link.offer_image_url} alt="" className="h-12 w-12 shrink-0 rounded-xl object-cover" />
          ) : (
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-slate-50">
              <LinkIcon className="h-5 w-5 text-navy-300" />
            </div>
          )}

          <div className="min-w-0 flex-1">
            <div className="truncate text-sm font-bold text-navy-900">{link.offer_title}</div>
            <div className="mt-0.5 truncate text-xs font-medium text-navy-400">{link.url}</div>
          </div>

          <button
            type="button"
            onClick={() => {
              navigator.clipboard.writeText(link.url);
              setCopiedId(link.id);
              setTimeout(() => setCopiedId((id) => (id === link.id ? null : id)), 1800);
            }}
            className="flex shrink-0 items-center gap-1.5 rounded-full border border-navy-100 px-3.5 py-2 text-xs font-bold text-navy-600 transition hover:bg-slate-50"
          >
            {copiedId === link.id ? <CheckIcon className="h-3.5 w-3.5" /> : <CopyIcon className="h-3.5 w-3.5" />}
            {copiedId === link.id ? "Copied" : "Copy"}
          </button>

          <Link
            href={`/dashboard/links?offer=${link.offer_id}`}
            className="shrink-0 rounded-full bg-cta-gradient px-4 py-2 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105"
          >
            Share
          </Link>
        </div>
      ))}
    </div>
  );
}
