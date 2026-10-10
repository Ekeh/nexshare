"use client";

import { useEffect, useRef, useState } from "react";
import { useAccount } from "@/components/dashboard/AccountContext";
import { categoryFor } from "@/components/dashboard/offerCategories";
import { OfferPreviewCard } from "@/components/business/OfferPreviewCard";
import { formatCommission, formatMoney, api, type BusinessOffer } from "@/lib/api";

const OFFER_TYPE_TABS = [
  { value: "physical", label: "Product" },
  { value: "service", label: "Service" },
  { value: "lead", label: "Lead" },
  { value: "booking", label: "Booking" },
  { value: "digital", label: "Subscription" },
  { value: "other", label: "Other" },
] as const;

const COMMISSION_MODELS = [
  { value: "percentage", label: "Percentage (%)" },
  { value: "fixed", label: "Fixed Amount ($)" },
] as const;

export default function BusinessPage() {
  const account = useAccount();

  const [offerType, setOfferType] = useState<string>("physical");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [destinationUrl, setDestinationUrl] = useState("");
  const [commissionModel, setCommissionModel] = useState<"percentage" | "fixed">("percentage");
  const [commissionRate, setCommissionRate] = useState("10");
  const [commissionAmount, setCommissionAmount] = useState("");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageUploading, setImageUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [justCreated, setJustCreated] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [offers, setOffers] = useState<BusinessOffer[] | null>(null);

  function loadOffers() {
    api.businessOffers().then(setOffers).catch(() => undefined);
  }

  useEffect(loadOffers, []);

  const commissionConfig: Record<string, number> =
    commissionModel === "percentage"
      ? { pct: parseFloat(commissionRate) || 0 }
      : { amount_minor_units: Math.round((parseFloat(commissionAmount) || 0) * 100) };

  const priceMinorUnits = price.trim() === "" ? null : Math.round(parseFloat(price) * 100);

  async function handleImageChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageUploading(true);
    setError(null);
    try {
      const { url } = await api.uploadOfferImage(file);
      setImageUrl(url);
    } catch {
      setError("Couldn't upload that image. Try a JPEG, PNG, or WEBP under 5MB.");
    } finally {
      setImageUploading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setError("Give your offer a title.");
      return;
    }
    setSubmitting(true);
    setError(null);
    setJustCreated(false);
    try {
      await api.createBusinessOffer({
        title,
        description: description || null,
        offer_type: offerType,
        price_minor_units: priceMinorUnits,
        currency: "USD",
        image_url: imageUrl,
        destination_url: destinationUrl || null,
        commission_model: commissionModel,
        commission_config: commissionConfig,
      });
      setJustCreated(true);
      setTitle("");
      setDescription("");
      setPrice("");
      setDestinationUrl("");
      setImageUrl(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      loadOffers();
    } catch {
      setError("Couldn't publish that offer. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-extrabold text-navy-900">List Your Offer</h1>
      <p className="mt-1 text-sm text-navy-400">Publish an offer for promoters to find and share.</p>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.3fr,1fr]">
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <section className="rounded-2xl bg-white p-5 shadow-card">
            <div className="flex flex-wrap gap-2">
              {OFFER_TYPE_TABS.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setOfferType(t.value)}
                  className={`rounded-full px-4 py-1.5 text-xs font-bold transition ${
                    offerType === t.value
                      ? "bg-navy-900 text-white"
                      : "border border-navy-100 bg-white text-navy-400 hover:bg-slate-50"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <h2 className="mt-5 text-sm font-bold text-navy-900">Basic Information</h2>
            <div className="mt-3 flex flex-col gap-3">
              <div>
                <label htmlFor="title" className="block text-xs font-semibold text-navy-600">
                  Offer Title
                </label>
                <input
                  id="title"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Weekend Getaway — 3 Nights"
                  className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
                />
              </div>
              <div>
                <label htmlFor="description" className="block text-xs font-semibold text-navy-600">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Enjoy a relaxing 3-night stay at our beachfront resort."
                  className="mt-1.5 w-full resize-none rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
                />
              </div>
              <div>
                <label htmlFor="destination" className="block text-xs font-semibold text-navy-600">
                  Website / Booking Link <span className="font-normal text-navy-300">(optional)</span>
                </label>
                <input
                  id="destination"
                  type="url"
                  value={destinationUrl}
                  onChange={(e) => setDestinationUrl(e.target.value)}
                  placeholder="https://yourbusiness.com/offer"
                  className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
                />
                <p className="mt-1 text-[11px] text-navy-300">Where a customer lands after clicking a promoter&rsquo;s link.</p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl bg-white p-5 shadow-card">
            <h2 className="text-sm font-bold text-navy-900">Pricing &amp; Commission</h2>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="price" className="block text-xs font-semibold text-navy-600">
                  Price <span className="font-normal text-navy-300">(optional)</span>
                </label>
                <input
                  id="price"
                  type="number"
                  min="0"
                  step="0.01"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  placeholder="299.00"
                  className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
                />
              </div>
              <div>
                <label htmlFor="commission-type" className="block text-xs font-semibold text-navy-600">
                  Commission Type
                </label>
                <select
                  id="commission-type"
                  value={commissionModel}
                  onChange={(e) => setCommissionModel(e.target.value as "percentage" | "fixed")}
                  className="mt-1.5 w-full rounded-xl border border-navy-100 bg-white px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
                >
                  {COMMISSION_MODELS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="col-span-2">
                {commissionModel === "percentage" ? (
                  <>
                    <label htmlFor="commission-rate" className="block text-xs font-semibold text-navy-600">
                      Commission Rate (%)
                    </label>
                    <input
                      id="commission-rate"
                      type="number"
                      min="0"
                      max="100"
                      step="0.5"
                      value={commissionRate}
                      onChange={(e) => setCommissionRate(e.target.value)}
                      className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
                    />
                  </>
                ) : (
                  <>
                    <label htmlFor="commission-amount" className="block text-xs font-semibold text-navy-600">
                      Commission Amount ($)
                    </label>
                    <input
                      id="commission-amount"
                      type="number"
                      min="0"
                      step="0.01"
                      value={commissionAmount}
                      onChange={(e) => setCommissionAmount(e.target.value)}
                      className="mt-1.5 w-full rounded-xl border border-navy-100 px-3.5 py-2.5 text-sm text-navy-900 focus:border-navy-400 focus:outline-none"
                    />
                  </>
                )}
              </div>
            </div>
          </section>

          <section className="rounded-2xl bg-white p-5 shadow-card">
            <h2 className="text-sm font-bold text-navy-900">Image</h2>
            <div className="mt-3 flex items-center gap-4">
              <div className={`flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-xl ${categoryFor(offerType).bg}`}>
                {imageUrl ? (
                  <img src={imageUrl} alt="" className="h-full w-full object-cover" />
                ) : (
                  (() => {
                    const Icon = categoryFor(offerType).icon;
                    return <Icon className={`h-6 w-6 ${categoryFor(offerType).fg}`} />;
                  })()
                )}
              </div>
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleImageChange}
                  className="hidden"
                  id="image-upload"
                />
                <label
                  htmlFor="image-upload"
                  className="cursor-pointer rounded-full border border-navy-100 px-4 py-2 text-xs font-bold text-navy-600 transition hover:bg-slate-50"
                >
                  {imageUploading ? "Uploading…" : imageUrl ? "Replace Image" : "Upload Image"}
                </label>
                <p className="mt-1 text-[11px] text-navy-300">JPEG, PNG, or WEBP — up to 5MB.</p>
              </div>
            </div>
          </section>

          {error && <p className="text-sm font-medium text-red-500">{error}</p>}
          {justCreated && <p className="text-sm font-medium text-emerald-600">Offer published — promoters can find it now.</p>}

          <button
            type="submit"
            disabled={submitting || imageUploading}
            className="rounded-full bg-cta-gradient py-3 text-sm font-bold text-navy-900 shadow-card transition hover:brightness-105 disabled:opacity-60"
          >
            {submitting ? "Publishing…" : "Publish Offer"}
          </button>
        </form>

        <div className="lg:sticky lg:top-8 lg:h-fit">
          <p className="mb-2 text-xs font-bold uppercase tracking-wide text-navy-300">Preview (Branded)</p>
          <OfferPreviewCard
            businessName={account.full_name}
            title={title}
            description={description}
            offerType={offerType}
            priceMinorUnits={priceMinorUnits}
            currency="USD"
            imageUrl={imageUrl}
            commissionModel={commissionModel}
            commissionConfig={commissionConfig}
          />
        </div>
      </div>

      <section className="mt-8">
        <h2 className="text-sm font-bold text-navy-900">Your Offers</h2>
        <div className="mt-3 flex flex-col gap-3">
          {offers === null ? (
            <div className="h-16 animate-pulse rounded-2xl bg-white shadow-card" />
          ) : offers.length === 0 ? (
            <p className="text-sm font-medium text-navy-300">You haven&rsquo;t published any offers yet.</p>
          ) : (
            offers.map((o) => {
              const category = categoryFor(o.offer_type);
              return (
                <div key={o.id} className="flex items-center gap-4 rounded-2xl bg-white p-4 shadow-card">
                  <div className={`flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-xl ${category.bg}`}>
                    {o.image_url ? (
                      <img src={o.image_url} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <category.icon className={`h-5 w-5 ${category.fg}`} />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-bold text-navy-900">{o.title}</div>
                    <div className="mt-0.5 text-xs font-medium text-navy-400">{category.label}</div>
                  </div>
                  {o.price_minor_units != null && (
                    <div className="text-sm font-semibold text-navy-900">
                      {formatMoney({ amount_minor_units: o.price_minor_units, currency: o.currency, change_pct: null })}
                    </div>
                  )}
                  <div className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-600">
                    {formatCommission(o)}
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold capitalize text-navy-500">
                    {o.status}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </section>
    </div>
  );
}
