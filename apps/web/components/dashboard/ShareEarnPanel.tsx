"use client";

import { useState } from "react";
import { CheckIcon, CopyIcon } from "@/components/icons";
import { ShareChannels } from "@/components/dashboard/ShareChannels";
import type { Offer, TrackingLink } from "@/lib/api";
import { buildShareMessage } from "@/lib/shareLinks";

function useCopyStatus() {
  const [copied, setCopied] = useState<string | null>(null);
  function flash(label: string) {
    setCopied(label);
    setTimeout(() => setCopied((c) => (c === label ? null : c)), 1800);
  }
  return { copied, flash };
}

export function ShareEarnPanel({ offer, link }: { offer: Offer; link: TrackingLink }) {
  const { copied, flash } = useCopyStatus();
  const [message, setMessage] = useState(() => buildShareMessage(offer));

  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr,0.9fr]">
      <div className="flex flex-col gap-6">
        <section className="rounded-2xl bg-white p-5 shadow-card">
          <h2 className="text-sm font-bold text-navy-900">Your Tracking Link</h2>
          <div className="mt-3 flex items-center gap-2">
            <input
              readOnly
              value={link.url}
              onFocus={(e) => e.currentTarget.select()}
              className="min-w-0 flex-1 rounded-xl border border-navy-100 bg-slate-50 px-3.5 py-2.5 text-sm text-navy-900"
            />
            <button
              type="button"
              onClick={() => {
                navigator.clipboard.writeText(link.url);
                flash("link");
              }}
              className="flex shrink-0 items-center gap-1.5 rounded-xl bg-cta-gradient px-4 py-2.5 text-sm font-bold text-navy-900 shadow-card transition hover:brightness-105"
            >
              {copied === "link" ? <CheckIcon className="h-4 w-4" /> : <CopyIcon className="h-4 w-4" />}
              {copied === "link" ? "Copied" : "Copy"}
            </button>
          </div>
        </section>

        <section className="rounded-2xl bg-white p-5 shadow-card">
          <h2 className="text-sm font-bold text-navy-900">Share on Social Media</h2>
          <div className="mt-3">
            <ShareChannels link={link.url} message={message} onCopyOnly={(label) => flash(label)} />
          </div>
          {copied && copied !== "link" && copied !== "message" && (
            <p className="mt-3 text-xs font-medium text-emerald-600">
              Link copied — paste it into your {copied} post.
            </p>
          )}
        </section>

        {offer.image_url && (
          <section className="rounded-2xl bg-white p-5 shadow-card">
            <h2 className="text-sm font-bold text-navy-900">Marketing Material</h2>
            <div className="mt-3 flex items-center gap-4">
              <img src={offer.image_url} alt="" className="h-16 w-16 rounded-xl object-cover" />
              <a
                href={offer.image_url}
                download
                className="rounded-full border border-navy-100 px-4 py-2 text-xs font-bold text-navy-600 transition hover:bg-slate-50"
              >
                Download Image
              </a>
            </div>
          </section>
        )}
      </div>

      <section className="h-fit rounded-2xl bg-white p-5 shadow-card">
        <h2 className="text-sm font-bold text-navy-900">Custom Message</h2>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={5}
          className="mt-3 w-full resize-none rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
        />
        <button
          type="button"
          onClick={() => {
            navigator.clipboard.writeText(`${message}\n\n${link.url}`);
            flash("message");
          }}
          className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl bg-navy-900 px-4 py-2.5 text-sm font-bold text-white transition hover:bg-navy-800"
        >
          {copied === "message" ? <CheckIcon className="h-4 w-4" /> : <CopyIcon className="h-4 w-4" />}
          {copied === "message" ? "Copied" : "Copy Message + Link"}
        </button>
      </section>
    </div>
  );
}
