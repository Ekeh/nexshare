import { categoryFor } from "@/components/dashboard/offerCategories";
import { formatMoney, type StorefrontOffer } from "@/lib/api";

export function StorefrontOfferCard({ offer }: { offer: StorefrontOffer }) {
  const category = categoryFor(offer.offer_type);

  return (
    <div className="flex flex-col overflow-hidden rounded-2xl bg-white shadow-card">
      <div className={`aspect-video w-full ${category.bg}`}>
        {offer.image_url ? (
          <img src={offer.image_url} alt="" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center">
            <category.icon className={`h-10 w-10 ${category.fg}`} />
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col p-4">
        <span className="inline-flex w-fit rounded-full bg-slate-50 px-2 py-0.5 text-xs font-bold text-navy-400">
          {category.label}
        </span>
        <h3 className="mt-2 text-sm font-bold text-navy-900">{offer.title}</h3>
        {offer.description && (
          <p className="mt-1 line-clamp-2 text-xs font-medium text-navy-400">{offer.description}</p>
        )}

        <div className="mt-auto flex items-center justify-between pt-4">
          {offer.price_minor_units != null ? (
            <span className="text-sm font-extrabold text-navy-900">
              {formatMoney({ amount_minor_units: offer.price_minor_units, currency: offer.currency, change_pct: null })}
            </span>
          ) : (
            <span />
          )}
          <a
            href={offer.url}
            className="rounded-full bg-cta-gradient px-4 py-2 text-xs font-bold text-navy-900 shadow-card transition hover:brightness-105"
          >
            Get This Deal
          </a>
        </div>
      </div>
    </div>
  );
}
