# NexShare — Architecture & Data Model (v0.1)

## 1. Service boundaries

Treat NexShare as a small set of cooperating services from day one, even if they deploy as one binary initially — the commission ledger and click-ingestion paths have very different scaling and consistency needs, and splitting them later is painful.

| Service | Responsibility | Consistency need |
|---|---|---|
| **Identity** | Business/Promoter/Customer accounts, auth, KYC status | Strong |
| **Catalog** | Offer, Campaign, creative assets, eligibility rules | Strong |
| **Attribution** | Tracking links, click capture, click→conversion matching | High volume, eventually-consistent OK |
| **Commission Engine** | Applies campaign commission rules to conversions, runs the lifecycle state machine | Strong (money math) |
| **Ledger** | Append-only financial ledger, wallet balances, payouts | Strong, immutable |
| **Fraud/Risk** | Velocity checks, device fingerprinting, self-referral detection, manual review queue | Async, can lag |
| **Storefront** | Public promoter pages, offer curation | Read-heavy, cacheable |
| **Notifications/Analytics** | Dashboards, alerts | Read-heavy, derived data |

Data flow: `Click → Attribution → Conversion event → Commission Engine → Ledger entry → Payout`. Attribution and Commission Engine should talk over an event stream (Redis Streams to start, Kafka if click volume justifies it later — same pattern you're already using on NexPlus), not synchronous calls, so a burst of clicks never blocks the money-critical path.

## 2. Core entities

- **Business** — the offer publisher, owns Offers/Campaigns, has a payment method for funding commissions.
- **Offer** — the universal commercial object (per spec §4); industry-agnostic, belongs to a Business.
- **Campaign** — a time-bound, rule-bound instantiation of an Offer: commission model, budget, max conversions, geography, eligible promoters.
- **Promoter** — earns commissions; has a PromoterStore, tracking links, a wallet.
- **PromoterStore** — the public curated page (spec §7).
- **TrackingLink** — a unique promoter×campaign attribution surface (link, QR, or creative variant).
- **Click** — a single attribution event.
- **Conversion** — the qualifying action, created once a Click's session/window completes the campaign's defined action.
- **Commission** — one earned-commission record tied to a Conversion, moving through the lifecycle state machine.
- **LedgerEntry** — immutable, append-only financial record. Wallet balances are *derived*, never stored as mutable state.
- **Payout** — a batched withdrawal request against available Ledger balance.
- **FraudFlag** — attached to Click/Conversion/Commission when risk rules fire.

## 3. Data model (PostgreSQL DDL sketch)

```sql
-- Businesses & Promoters share an accounts table; role determines allowed actions
CREATE TABLE accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role TEXT NOT NULL CHECK (role IN ('business','promoter','customer','admin')),
  email TEXT UNIQUE NOT NULL,
  phone TEXT,
  country_code CHAR(2) NOT NULL,          -- drives currency + compliance rules
  kyc_status TEXT NOT NULL DEFAULT 'unverified',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE offers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id UUID NOT NULL REFERENCES accounts(id),
  offer_type TEXT NOT NULL,               -- physical, digital, service, booking, lead, subscription, ...
  title TEXT NOT NULL,
  description TEXT,
  price_minor_units BIGINT,               -- store money as integer minor units, never float
  currency CHAR(3) NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',   -- draft, active, paused, archived
  branding JSONB,                         -- logo, imagery, approved claims, CTA text
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offer_id UUID NOT NULL REFERENCES offers(id),
  commission_model TEXT NOT NULL,         -- percentage | fixed | qualified_lead | booking | milestone | tiered | bonus
  commission_config JSONB NOT NULL,       -- e.g. {"pct": 5} or {"tiers":[{"upto":10,"amount":5000},...]}
  budget_minor_units BIGINT,
  max_conversions INT,
  conversions_count INT NOT NULL DEFAULT 0,  -- incremented atomically, gates campaign auto-stop
  geo_restriction JSONB,
  eligible_promoter_rule JSONB,
  starts_at TIMESTAMPTZ,
  ends_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tracking_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID NOT NULL REFERENCES campaigns(id),
  promoter_id UUID NOT NULL REFERENCES accounts(id),
  short_code TEXT UNIQUE NOT NULL,
  channel TEXT,                           -- whatsapp, instagram, tiktok, sms, email, qr, direct
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE clicks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tracking_link_id UUID NOT NULL REFERENCES tracking_links(id),
  click_id TEXT UNIQUE NOT NULL,          -- opaque id set as cookie/param, survives redirect chain
  ip_hash TEXT,                           -- hash, never store raw IP long-term
  device_fingerprint TEXT,
  user_agent TEXT,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (occurred_at);        -- high volume, time-partition and roll off/archive

CREATE TABLE conversions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  click_id UUID NOT NULL REFERENCES clicks(id),
  campaign_id UUID NOT NULL REFERENCES campaigns(id),
  customer_id UUID REFERENCES accounts(id),
  conversion_value_minor_units BIGINT,
  status TEXT NOT NULL DEFAULT 'pending_validation', -- see lifecycle below
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE commissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversion_id UUID NOT NULL REFERENCES conversions(id),
  promoter_id UUID NOT NULL REFERENCES accounts(id),
  amount_minor_units BIGINT NOT NULL,
  currency CHAR(3) NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending -> approved -> available -> paid | reversed
  status_history JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Append-only. Never UPDATE a row here; reversals are new rows with negative amount.
CREATE TABLE ledger_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id),
  commission_id UUID REFERENCES commissions(id),
  payout_id UUID,
  entry_type TEXT NOT NULL,               -- commission_earned, commission_reversed, payout_debit, fee
  amount_minor_units BIGINT NOT NULL,     -- signed
  currency CHAR(3) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE payouts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  promoter_id UUID NOT NULL REFERENCES accounts(id),
  amount_minor_units BIGINT NOT NULL,
  currency CHAR(3) NOT NULL,
  payout_method TEXT NOT NULL,            -- bank_transfer, mobile_money, wallet (NexPlus integration point)
  status TEXT NOT NULL DEFAULT 'requested',
  requested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE fraud_flags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_type TEXT NOT NULL,             -- click, conversion, commission, account
  subject_id UUID NOT NULL,
  rule_triggered TEXT NOT NULL,
  severity TEXT NOT NULL,
  resolved BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Wallet balances (pending / available / paid) are **views over `ledger_entries`**, not columns anywhere — this is what makes the ledger the source of truth and keeps reversals honest.

## 4. Commission lifecycle — state machine

```
clicked → attributed → conversion_created → pending_validation → approved → available → paid
                                                      ↘ rejected
                                            (any state) → reversed   [refund/cancellation/fraud]
```

- **pending_validation → approved**: campaign-specific rule engine — product sales wait out the return window; leads wait for business verification (webhook or manual); bookings wait for completed service date.
- **approved → available**: a hold period (configurable per campaign, e.g. 3–7 days) to absorb late disputes before funds are withdrawable.
- **available → paid**: triggered by a Payout batch.
- **reversed**: always a *new* ledger entry that nets the original, never a delete/update — preserves the audit trail (spec principle: immutable financial ledger).

Encode this as an explicit state machine (e.g. a `transitions` table or a library like `python-statemachine`) rather than ad-hoc status string checks scattered across the codebase — you'll want one place that enforces legal transitions and emits events for each one.

## 5. Attribution design

- `short_code` on `tracking_links` resolves to a redirect; on hit, mint a `click_id`, set it as both a cookie and a query-param fallback (for in-app browsers that block cookies — WhatsApp/Instagram in-app browsers are a real problem here), then redirect to the actual offer/business destination.
- Attribution window and model (last-click vs. first-click) are campaign-level config, not global — a lead-gen campaign might want a longer window than a flash-sale product campaign.
- Device fingerprint + IP hash on `clicks` feed the fraud service, not the attribution decision itself — keep attribution logic simple and auditable.

## 6. Commission calculation

`campaigns.commission_config` is a JSONB blob whose shape depends on `commission_model`:

| Model | Config shape |
|---|---|
| percentage | `{"pct": 5}` |
| fixed | `{"amount_minor_units": 5000}` |
| qualified_lead | `{"amount_minor_units": 10000}` |
| booking | `{"amount_minor_units": 7500}` |
| milestone | `{"amount_minor_units": 50000, "milestone": "verified_move_in"}` |
| tiered | `{"tiers": [{"upto":10,"amount":5000},{"upto":50,"amount":7500},{"upto":null,"amount":10000}]}` |
| bonus | `{"base_model":"percentage","pct":5,"bonus_amount":2000,"bonus_window_ends":"2026-09-30"}` |

`conversions_count` on the campaign row should be incremented with an atomic `UPDATE ... SET conversions_count = conversions_count + 1 WHERE conversions_count < max_conversions RETURNING ...` so budget/max-conversion caps can't be blown past under concurrent conversions — this is the kind of race condition that's invisible until you have real traffic.

## 7. Fraud & trust

Run these as async checks against `clicks`/`conversions`, writing to `fraud_flags` without blocking the commission pipeline, then gate the `pending_validation → approved` transition on "no unresolved flags":

- Self-referral: compare promoter identity fields (phone/email/device) against the customer's.
- Velocity: clicks or conversions per promoter/IP/device in a rolling window.
- Device farm detection: repeated device_fingerprint across many "distinct" clicks.
- Reversal-rate monitoring per promoter, feeding into eligibility for future campaigns.

## 8. Currency / market scope — flag this now

The spec's commission examples use **"K"** (e.g. "K50 per sale," "K100 per verified lead"), not ₦ or $. That reads like Kwacha (Zambia/Malawi), not Naira — worth confirming with your client before you lock the schema, since it affects whether `currency`/`country_code` need to support multiple markets from day one or whether "K" is just a placeholder in the doc. The schema above already assumes multi-currency (minor-units + ISO currency code per row) so it's not a big lift either way, but the compliance and payout-rail work (mobile money vs. NIBSS) differs a lot by country.

## 9. Tech stack recommendation

Consistent with your existing stack and the NexPlus work:

- **API services**: Python/FastAPI for Catalog, Commission Engine, Ledger (money-critical, want strong typing + easy testing). Node/TypeScript is fine for Attribution (high write volume, thin logic) if you want to split language by service.
- **Event bus**: Redis Streams to start (you already run Redis); migrate hot paths to Kafka only if click volume actually demands it.
- **DB**: PostgreSQL, with `clicks` time-partitioned and rolled off to cold storage after N days.
- **Cache**: Redis for click dedup, rate limiting, session lookups.
- **Object storage**: S3 for offer creatives/media.
- **Frontend**: Next.js/React + Tailwind for marketing site, promoter dashboard, business dashboard, storefront — matches the mockup's component density well.
- **Mobile**: React Native, given the web dashboard is already React — lets you share types/validation logic.

## 10. Open decisions to close before Claude Code scaffolding starts

1. Currency/market scope (see §8).
2. Payout rails: bank transfer + mobile money confirmed in the mockup — does NexPlus wallet become a payout destination at launch or later?
3. Attribution window length and first-click vs last-click, likely per-campaign but need a sane default.
4. Hold period between `approved` and `available`.
5. Single Postgres schema vs. schema-per-business (multi-tenancy) — single schema with `business_id`/`account_id` scoping is almost certainly right at this scale; call it out explicitly so nobody "helpfully" introduces per-tenant schemas later.
6. Whether the AI-assisted promotional copy feature (spec §8) is in scope for MVP or a fast-follow.
