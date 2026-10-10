---
name: nexshare-build
description: Build the NexShare performance-commerce platform — landing page, promoter dashboard, and business dashboard — matched pixel-for-pixel to the provided mockup, backed by a real FastAPI + PostgreSQL API implementing the Offer/Campaign/Commission data model. Use this skill for any NexShare repo work: scaffolding, new pages, API endpoints, or database migrations. Mobile app is explicitly out of scope for this phase.
---

# NexShare Build

## 0. Before you write any code

Open `design/nexshare-mockup.jpg` and look at it directly. **This image is the design spec, not the written product doc.** Every screen you build must visually match its corresponding region of this image: layout, spacing, color palette (navy sidebar/hero, gold/yellow CTA accent, white cards, soft shadows, rounded corners), typography weight and hierarchy, iconography style, and component structure. Where the written doc and the image seem to conflict on layout or flow, **the image wins**.

Read `references/product-spec.md` for business rules (offer types, commission models, lifecycle) and `references/architecture.md` for the data model and API shape already agreed with the product owner. Don't re-derive these — they're settled decisions, not open questions.

## 1. Scope for this phase

Build **web only**:
- Marketing landing page (public)
- Promoter web dashboard (authenticated): dashboard home, find offers, share & earn, analytics, storefront/my page, earnings, withdrawal
- Business dashboard (authenticated): "List Your Offer" / campaign creation flow, at minimum

Do **not** build the mobile app screens shown along the bottom of the mockup (onboarding, choose-your-path, earnings, withdrawal, notifications phone screens). Skip that region of the image entirely — it's a later phase.

## 2. Design fidelity checklist

Apply this to every screen before moving on to the next one:

- [ ] Sidebar/nav structure and iconography match the promoter dashboard nav in the mockup (Dashboard, My Offers, My Links, Storefront, Analytics, Earnings, Withdraw, Training, Support)
- [ ] Stat cards use the same 4-card row layout (value + label + delta indicator) as the "Welcome back, Sarah!" screen
- [ ] Primary CTAs are yellow/gold pill-shaped buttons; secondary actions use dark navy outline/fill
- [ ] Offer cards show image thumbnail, title, category, price/commission badge, and a "Promote" CTA, consistent with the "Find Offers" panel
- [ ] Category badges are color-coded per vertical, matching the "Works for Every Industry" icon row
- [ ] The "List Your Offer" form's live branded preview panel (right side) updates from the form fields on the left, exactly as mocked
- [ ] Charts use the same two-tone navy/gold palette as "Top Performing Offers" and "Clicks vs Conversions"

**Render each screen and visually diff it against the corresponding region of `design/nexshare-mockup.jpg` before starting the next one.** Don't let visual drift accumulate across pages.

## 3. Tech stack

- Frontend: Next.js + React + Tailwind CSS (fastest path to pixel-matching this component-dense a design)
- Backend: Python FastAPI
- Database: PostgreSQL — schema in `references/architecture.md` §3
- Cache/dedup: Redis
- Auth: email/password + session; `kyc_status` field already modeled on the `accounts` table

## 4. Build order

1. Scaffold the repo: `apps/web` (Next.js), `apps/api` (FastAPI), Docker Compose for local Postgres + Redis.
2. Migrate the schema from `references/architecture.md` §3 (Alembic or raw SQL migrations) — get the ledger and commission tables in place even before any UI, since they're the part that's expensive to redesign later.
3. Build the marketing landing page first. It's static and unauthenticated, so it's the fastest way to confirm you're matching the mockup's visual language before touching anything stateful.
4. Build promoter auth + dashboard shell (sidebar + stat card row), wired to real endpoints (seeded data is fine initially, but the endpoints should be real).
5. Build Find Offers, Share & Earn, Analytics, and Storefront pages.
6. Build the business "List Your Offer" flow with live preview.
7. Wire up the commission lifecycle state machine (`references/architecture.md` §4) once the UI is stable — don't let backend state-machine work block frontend design progress.

## 5. Definition of done for this phase

Every in-scope page renders and, placed side-by-side with the mockup, is recognizably the same product — not a reinterpretation. Mobile app screens are untouched. The API has real endpoints backing the dashboards (not hardcoded JSON) for at least: list offers, create a tracking link, record a click, and list a promoter's commissions.
