import Link from "next/link";
import { categoryFor } from "@/components/dashboard/offerCategories";
import { formatCommission, formatMoney, type Offer } from "@/lib/api";

export function OfferCard({ offer }: { offer: Offer }) {
  const category = categoryFor(offer.offer_type);

  return (
    <div className="flex items-center gap-4 rounded-2xl bg-white p-4 shadow-card">
      <div className={`h-14 w-14 shrink-0 overflow-hidden rounded-xl ${category.bg}`}>
        {offer.image_url ? (
          <img src={offer.image_url} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <category.icon className={`h-6 w-6 ${category.fg}`} />
          </div>
        )}
      </div>

      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-bold text-navy-900">{offer.title}</div>
        <div className="mt-0.5 text-xs font-medium text-navy-400">{category.label}</div>
      </div>

      <div className="hidden shrink-0 text-right sm:block">
        {offer.price_minor_units != null && (
          <div className="text-sm font-semibold text-navy-900">
            {formatMoney({ amount_minor_units: offer.price_minor_units, currency: offer.currency, change_pct: null })}
          </div>
        )}
        <div className="mt-0.5 inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-bold text-emerald-600">
          {formatCommission(offer)}
        </div>
      </div>

      <Link
        href={`/dashboard/links?offer=${offer.id}`}
        className="shrink-0 rounded-full bg-cta-gradient px-4 py-2 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105"
      >
        Promote
      </Link>
    </div>
  );
}
