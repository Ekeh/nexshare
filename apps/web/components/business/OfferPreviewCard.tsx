import { categoryFor } from "@/components/dashboard/offerCategories";
import { formatCommission, formatMoney } from "@/lib/api";

const CTA_LABEL: Record<string, string> = {
  booking: "Book Now",
  service: "Get Started",
  digital: "Get Access",
  education: "Apply Now",
  lead: "Learn More",
  physical: "Shop Now",
};

export function OfferPreviewCard({
  businessName,
  title,
  description,
  offerType,
  priceMinorUnits,
  currency,
  imageUrl,
  commissionModel,
  commissionConfig,
}: {
  businessName: string;
  title: string;
  description: string;
  offerType: string;
  priceMinorUnits: number | null;
  currency: string;
  imageUrl: string | null;
  commissionModel: string;
  commissionConfig: Record<string, number>;
}) {
  const category = categoryFor(offerType);
  const cta = CTA_LABEL[offerType] ?? "View Offer";
  const commissionLabel = formatCommission({ commission_model: commissionModel, commission_config: commissionConfig, currency });

  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-card-lg">
      <div className="flex items-center gap-2 border-b border-navy-900/5 px-4 py-3">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-navy-900 text-[10px] font-bold text-white">
          {businessName.charAt(0).toUpperCase() || "B"}
        </span>
        <span className="text-xs font-bold text-navy-900">{businessName || "Your Business"}</span>
      </div>

      <div className={`flex h-40 items-center justify-center ${category.bg}`}>
        {imageUrl ? (
          <img src={imageUrl} alt="" className="h-full w-full object-cover" />
        ) : (
          <category.icon className={`h-10 w-10 ${category.fg}`} />
        )}
      </div>

      <div className="p-4">
        <div className="text-sm font-extrabold text-navy-900">{title || "Your offer title"}</div>
        {description && <p className="mt-1 line-clamp-2 text-xs text-navy-400">{description}</p>}

        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-baseline gap-2">
            {priceMinorUnits != null && (
              <span className="text-lg font-extrabold text-navy-900">
                {formatMoney({ amount_minor_units: priceMinorUnits, currency, change_pct: null })}
              </span>
            )}
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-bold text-emerald-600">
              {commissionLabel} commission
            </span>
          </div>
        </div>

        <button
          type="button"
          disabled
          className="mt-3 w-full rounded-full bg-cta-gradient py-2.5 text-sm font-bold text-navy-900 shadow-card"
        >
          {cta}
        </button>
      </div>

      <p className="border-t border-navy-900/5 px-4 py-2 text-[10px] text-navy-300">
        Shown to promoters and shared under your branding.
      </p>
    </div>
  );
}
