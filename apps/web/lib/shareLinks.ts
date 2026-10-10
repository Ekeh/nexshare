import { formatMoney, type Offer } from "@/lib/api";

/** Pre-filled promo copy for an offer, e.g. "Weekend Getaway — 3 Nights for $299.00! ..." */
export function buildShareMessage(offer: Offer): string {
  const price =
    offer.price_minor_units != null
      ? ` for ${formatMoney({ amount_minor_units: offer.price_minor_units, currency: offer.currency, change_pct: null })}`
      : "";
  const description = offer.description ? ` ${offer.description}` : "";
  return `${offer.title}${price}!${description}`;
}

/** Tags the link with `?ch=<channel>` so a later click's Analytics "Top
 * Sources" breakdown can attribute it back to the channel it was shared on. */
export function linkForChannel(link: string, channel: string): string {
  return `${link}?ch=${encodeURIComponent(channel)}`;
}

export function buildShareUrls(link: string, message: string) {
  const withChannel = (channel: string) => linkForChannel(link, channel);
  const textFor = (channel: string) => `${message}\n\n${withChannel(channel)}`;
  return {
    whatsapp: `https://wa.me/?text=${encodeURIComponent(textFor("whatsapp"))}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(withChannel("facebook"))}`,
    x: `https://twitter.com/intent/tweet?text=${encodeURIComponent(textFor("x"))}`,
    telegram: `https://t.me/share/url?url=${encodeURIComponent(withChannel("telegram"))}&text=${encodeURIComponent(message)}`,
    sms: `sms:?&body=${encodeURIComponent(textFor("sms"))}`,
    email: `mailto:?subject=${encodeURIComponent("Check this out")}&body=${encodeURIComponent(textFor("email"))}`,
  };
}
