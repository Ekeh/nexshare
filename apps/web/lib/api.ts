export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // FormData (image upload) sets its own multipart boundary — forcing
  // application/json on it would break parsing on the server.
  const isFormData = init?.body instanceof FormData;
  const res = await fetch(`/api${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg).join(", ")
      : detail ?? res.statusText;
    throw new ApiError(res.status, message);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface Account {
  id: string;
  email: string;
  role: string;
  full_name: string;
  kyc_status: string;
}

export interface StatValue {
  amount_minor_units: number;
  currency: string;
  change_pct: number | null;
}

export interface PromoterStats {
  today_earnings: StatValue;
  month_earnings: StatValue;
  pending: StatValue;
  total_earned: StatValue;
}

export interface Offer {
  id: string;
  title: string;
  description: string | null;
  offer_type: string;
  price_minor_units: number | null;
  currency: string;
  image_url: string | null;
  commission_model: string;
  commission_config: Record<string, number>;
}

export interface TrackingLink {
  id: string;
  short_code: string;
  url: string;
  offer_id: string;
  offer_title: string;
  offer_image_url: string | null;
}

export interface DailyPoint {
  date: string;
  clicks: number;
  conversions: number;
}

export interface SourceBreakdown {
  channel: string;
  count: number;
  pct: number;
}

export interface Analytics {
  total_clicks: number;
  total_clicks_change_pct: number | null;
  conversions: number;
  conversions_change_pct: number | null;
  conversion_rate: number;
  conversion_rate_change_pct: number | null;
  total_commission_minor_units: number;
  currency: string;
  total_commission_change_pct: number | null;
  series: DailyPoint[];
  top_sources: SourceBreakdown[];
}

export interface BusinessOffer {
  id: string;
  title: string;
  description: string | null;
  offer_type: string;
  price_minor_units: number | null;
  currency: string;
  image_url: string | null;
  status: string;
  commission_model: string;
  commission_config: Record<string, number>;
}

export interface BusinessCommission {
  id: string;
  offer_title: string;
  promoter_name: string;
  amount_minor_units: number;
  currency: string;
  status: CommissionStatus;
  created_at: string;
}

export interface WebhookSecret {
  webhook_secret: string;
}

export type FraudSeverity = "low" | "medium" | "high";

export interface FraudFlag {
  id: string;
  commission_id: string;
  offer_title: string;
  promoter_name: string;
  rule_triggered: string;
  severity: FraudSeverity;
  resolved: boolean;
  created_at: string;
}

export interface CreateOfferInput {
  title: string;
  description?: string | null;
  offer_type: string;
  price_minor_units?: number | null;
  currency?: string;
  image_url?: string | null;
  destination_url?: string | null;
  commission_model: string;
  commission_config: Record<string, number>;
}

export type VerificationChannel = "email" | "phone";

export interface PendingVerification {
  account_id: string;
  email: string;
  phone: string;
  email_verified: boolean;
  phone_verified: boolean;
  pending_verification_token: string;
}

export interface VerifyResult {
  channel: VerificationChannel;
  fully_verified: boolean;
  account: Account | null;
}

export type CommissionStatus = "pending" | "approved" | "available" | "paid" | "rejected" | "reversed";

export interface Commission {
  id: string;
  offer_title: string;
  amount_minor_units: number;
  currency: string;
  status: CommissionStatus;
  created_at: string;
}

export interface StorefrontOffer {
  tracking_link_id: string;
  url: string;
  offer_id: string;
  title: string;
  description: string | null;
  offer_type: string;
  price_minor_units: number | null;
  currency: string;
  image_url: string | null;
}

export interface Storefront {
  promoter_name: string;
  offers: StorefrontOffer[];
}

export type PayoutMethod = "bank_transfer" | "mobile_money";

export interface Payout {
  id: string;
  amount_minor_units: number;
  currency: string;
  payout_method: PayoutMethod;
  status: string;
  failure_reason: string | null;
  requested_at: string;
}

export interface Bank {
  name: string;
  code: string;
}

export interface PayoutAccount {
  payout_method: PayoutMethod;
  bank_name: string;
  account_number_masked: string;
  account_name: string;
}

export const api = {
  login: (email: string, password: string) =>
    request<Account>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (input: {
    email: string;
    phone: string;
    password: string;
    full_name: string;
    role: "promoter" | "business";
  }) => request<PendingVerification>("/auth/register", { method: "POST", body: JSON.stringify(input) }),
  verifyStart: (email: string, password: string) =>
    request<PendingVerification>("/auth/verify/start", { method: "POST", body: JSON.stringify({ email, password }) }),
  verifyCode: (pendingToken: string, channel: VerificationChannel, code: string) =>
    request<VerifyResult>("/auth/verify", {
      method: "POST",
      headers: { Authorization: `Bearer ${pendingToken}` },
      body: JSON.stringify({ channel, code }),
    }),
  resendCode: (pendingToken: string, channel: VerificationChannel) =>
    request<void>("/auth/verify/resend", {
      method: "POST",
      headers: { Authorization: `Bearer ${pendingToken}` },
      body: JSON.stringify({ channel }),
    }),
  logout: () => request<{ ok: boolean }>("/auth/logout", { method: "POST" }),
  me: () => request<Account>("/auth/me"),
  promoterStats: () => request<PromoterStats>("/promoters/me/stats"),
  offers: () => request<Offer[]>("/offers"),
  trackingLinks: () => request<TrackingLink[]>("/tracking-links"),
  createTrackingLink: (offerId: string) =>
    request<TrackingLink>("/tracking-links", { method: "POST", body: JSON.stringify({ offer_id: offerId }) }),
  analytics: () => request<Analytics>("/analytics/me"),
  commissions: () => request<Commission[]>("/commissions"),
  payouts: () => request<Payout[]>("/promoters/me/payouts"),
  requestWithdrawal: (payoutMethod: PayoutMethod) =>
    request<Payout>("/promoters/me/withdraw", { method: "POST", body: JSON.stringify({ payout_method: payoutMethod }) }),
  payoutBanks: () => request<Bank[]>("/promoters/payout-banks"),
  payoutAccount: () => request<PayoutAccount | null>("/promoters/me/payout-account"),
  resolvePayoutAccount: (bankCode: string, accountNumber: string) =>
    request<{ account_name: string }>("/promoters/me/payout-account/resolve", {
      method: "POST",
      body: JSON.stringify({ bank_code: bankCode, account_number: accountNumber }),
    }),
  savePayoutAccount: (input: { payout_method: PayoutMethod; bank_code: string; account_number: string }) =>
    request<PayoutAccount>("/promoters/me/payout-account", { method: "POST", body: JSON.stringify(input) }),
  storefront: (promoterId: string) => request<Storefront>(`/storefront/${promoterId}`),
  businessOffers: () => request<BusinessOffer[]>("/business/offers"),
  createBusinessOffer: (input: CreateOfferInput) =>
    request<BusinessOffer>("/business/offers", { method: "POST", body: JSON.stringify(input) }),
  uploadOfferImage: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<{ url: string }>("/business/offers/upload-image", { method: "POST", body: formData });
  },
  businessCommissions: () => request<BusinessCommission[]>("/business/commissions"),
  approveCommission: (id: string) =>
    request<BusinessCommission>(`/business/commissions/${id}/approve`, { method: "POST" }),
  rejectCommission: (id: string) =>
    request<BusinessCommission>(`/business/commissions/${id}/reject`, { method: "POST" }),
  reverseCommission: (id: string) =>
    request<BusinessCommission>(`/business/commissions/${id}/reverse`, { method: "POST" }),
  webhookSecret: () => request<WebhookSecret>("/business/webhook-secret"),
  rotateWebhookSecret: () => request<WebhookSecret>("/business/webhook-secret/rotate", { method: "POST" }),
  fraudFlags: () => request<FraudFlag[]>("/business/fraud-flags"),
  resolveFraudFlag: (id: string) => request<FraudFlag>(`/business/fraud-flags/${id}/resolve`, { method: "POST" }),
};

export function formatMoney(stat: StatValue): string {
  const amount = stat.amount_minor_units / 100;
  const symbol = stat.currency === "USD" ? "$" : `${stat.currency} `;
  return `${symbol}${amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/** Short display label for an offer's commission, e.g. "12%" or "$12.00". */
export function formatCommission(offer: Pick<Offer, "commission_model" | "commission_config" | "currency">): string {
  const { commission_model, commission_config, currency } = offer;
  switch (commission_model) {
    case "percentage":
      return `${commission_config.pct}%`;
    case "fixed":
    case "qualified_lead":
    case "booking":
    case "milestone":
      return formatMoney({ amount_minor_units: commission_config.amount_minor_units, currency, change_pct: null });
    default:
      return "Custom";
  }
}
