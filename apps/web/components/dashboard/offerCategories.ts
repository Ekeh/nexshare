import { AppsIcon, BriefcaseIcon, CartIcon, GraduationCapIcon, HotelIcon, TagIcon } from "@/components/icons";

export interface OfferCategoryMeta {
  label: string;
  icon: typeof TagIcon;
  bg: string;
  fg: string;
}

// Mirrors the "Works for Every Industry" color language on the landing page
// (components/landing/Industries.tsx) so an offer's category badge reads as
// the same visual system across the site.
const CATEGORIES: Record<string, OfferCategoryMeta> = {
  physical: { label: "Physical Goods", icon: CartIcon, bg: "bg-orange-50", fg: "text-orange-500" },
  booking: { label: "Hotels & Travel", icon: HotelIcon, bg: "bg-sky-50", fg: "text-sky-500" },
  digital: { label: "Digital", icon: AppsIcon, bg: "bg-indigo-50", fg: "text-indigo-500" },
  education: { label: "Education", icon: GraduationCapIcon, bg: "bg-emerald-50", fg: "text-emerald-500" },
  service: { label: "Service", icon: BriefcaseIcon, bg: "bg-blue-50", fg: "text-blue-500" },
};

const FALLBACK: OfferCategoryMeta = { label: "Other", icon: TagIcon, bg: "bg-slate-50", fg: "text-slate-500" };

export function categoryFor(offerType: string): OfferCategoryMeta {
  return CATEGORIES[offerType] ?? { ...FALLBACK, label: offerType.replace(/_/g, " ") };
}
