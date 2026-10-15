# NexShare

A performance-commerce network: businesses list offers, promoters share
tracking links to them, and earn commissions on the resulting conversions.

Monorepo layout:

```
apps/api/    FastAPI backend (SQLAlchemy + Alembic + Postgres + Redis)
apps/web/    Next.js 14 frontend (React 18 + Tailwind)
infra/       docker-compose.yml for local Postgres + Redis
```

## Prerequisites

- Docker Desktop (for Postgres + Redis)
- Python 3.12+ (tested on 3.14)
- Node.js 20+ and npm

## 1. Start infrastructure

```bash
cd infra
docker compose up -d
```

This starts:

- **Postgres 16** on `localhost:5432` (db `nexshare`, user/password `nexshare`)
- **Redis 7** on `localhost:6379`

Both have healthchecks; `docker ps` should show them as `healthy` within a
few seconds.

## 2. Backend (apps/api)

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Config is loaded from environment variables (see `app/core/config.py`), with
defaults that already match the `infra/docker-compose.yml` credentials — so
a `.env` file is optional for local dev. Copy `.env.example` to `.env` if you
need to override anything (e.g. CORS origins, JWT secret):

```bash
cp .env.example .env
```

Run database migrations:

```bash
alembic upgrade head
```

Seed a demo account (promoter + business + offer + campaign + a few months
of commission history, so the dashboard has data to show):

```bash
python -m app.scripts.seed_demo
```

This prints the demo promoter login: `demo.promoter@nexshare.app` / `password123`.
A demo business account is also seeded: `demo.business@nexshare.app` / `password123`
(log in and you land on `/business`, the "List Your Offer" flow).

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Verify it's up:

```bash
curl http://localhost:8000/health   # {"status": "ok"}
```

**Port 8000 already taken by something else?** Run the API on any other
port (`--port 8010`, say) and tell the frontend where to find it with
`API_URL` when you start it (see next section) — nothing else needs to
change, `next.config.js`'s proxy already reads `API_URL`.

### API endpoints

| Route | Description |
|---|---|
| `POST /api/auth/register` | Create a promoter or business account, sends verification codes |
| `POST /api/auth/login` | Log in — 403s until email + phone are both verified |
| `POST /api/auth/verify/start` | Re-prove credentials to get a fresh verification session |
| `POST /api/auth/verify` | Submit a code for `email` or `phone`; sets the session cookie once both are done |
| `POST /api/auth/verify/resend` | Resend a code (rate-limited) |
| `POST /api/auth/logout` | Clear the session cookie |
| `GET /api/auth/me` | Current account |
| `GET /api/promoters/me` | Current promoter profile |
| `GET /api/promoters/me/stats` | Today/month/pending/total earnings |
| `POST /api/promoters/me/withdraw` | Withdraw the full available balance |
| `GET /api/promoters/me/payouts` | This promoter's payout history |
| `GET /api/promoters/payout-banks` | List Paystack bank codes for the payout-account form |
| `POST /api/promoters/me/payout-account/resolve` | Look up the real account name for a bank/account-number pair |
| `GET /api/promoters/me/payout-account` | This promoter's saved payout destination, if any |
| `POST /api/promoters/me/payout-account` | Resolve, register with Paystack, and save a payout destination |
| `GET /api/offers` | List active offers, for the promoter "Find Offers" page |
| `POST /api/tracking-links` | Create (or reuse) a tracking link for an offer |
| `GET /api/tracking-links` | List the current promoter's tracking links |
| `GET /api/clicks/{short_code}` | Resolve a tracking link, record the click, redirect to the offer |
| `GET /api/commissions` | List the current promoter's commissions |
| `GET /api/analytics/me` | Promoter performance stats — clicks, conversions, top sources |
| `GET /api/business/offers` | List the current business's offers |
| `POST /api/business/offers` | Publish a new offer + campaign |
| `POST /api/business/offers/upload-image` | Upload an offer image (served from `/uploads`) |
| `GET /api/business/commissions` | List commissions against the current business's offers |
| `POST /api/business/commissions/{id}/approve` | Move a commission `pending` → `approved` |
| `POST /api/business/commissions/{id}/reject` | Move a commission `pending` → `rejected` |
| `POST /api/business/commissions/{id}/reverse` | Reverse a commission (refund/chargeback), any state after `pending` |
| `GET /api/business/webhook-secret` | Get (generating on first call) the credential for the conversion webhook |
| `POST /api/business/webhook-secret/rotate` | Invalidate the old secret and issue a new one |
| `GET /api/business/fraud-flags` | List fraud flags against the current business's commissions |
| `POST /api/business/fraud-flags/{id}/resolve` | Mark a fraud flag resolved, unblocking automatic approval |
| `POST /api/webhooks/conversions` | A business's checkout reports a completed sale/lead — see below |
| `POST /api/webhooks/paystack` | Paystack reports a transfer's final status — see Payment rail below |
| `GET /api/storefront/{promoter_id}` | Public — a promoter's storefront: their name + every actively-promoted offer with a real tracking link |

Uploaded offer images are saved to `apps/api/uploads/` (gitignored) and served
at `/uploads/*` — proxied through the web app the same way `/api/*` is (see
`next.config.js`), so `image_url` values work whether they point at a static
demo asset in `apps/web/public` or a business-uploaded file.

### Conversion webhook

`GET /api/clicks/{short_code}` redirects to the offer's `destination_url`
with the click's id appended as `?nx_click=...` — that's the mechanism, not
the `nx_click_id` cookie also set alongside it (the cookie is same-origin
only, so it's useless once the browser has navigated to the business's own
domain). A business's checkout is expected to capture that param and carry
it through to checkout completion.

When a sale/lead completes, their backend calls:

```
POST /api/webhooks/conversions
Authorization: Bearer <webhook_secret>
{ "click_id": "<the nx_click value>", "external_ref": "<their own order id>", "value_minor_units": 15000 }
```

authenticated with the static secret from `GET /api/business/webhook-secret`
(`app/api/deps.py` — `get_business_from_webhook_secret` — deliberately not
the cookie/JWT session every other endpoint uses, since this is called
server-to-server, not by a logged-in browser). The endpoint resolves the
click back to a campaign, computes the commission from
`commission_model`/`commission_config`, and creates the `Conversion` +
`Commission` together — this is what actually feeds the state machine in
`app/services/commission_lifecycle.py` outside of seed data. `external_ref`
makes a retried call idempotent (any real webhook sender retries on
timeout/5xx): the same ref returns the original conversion/commission with
`"duplicate": true` instead of recording the sale twice — checked up front,
before the cap/budget checks below, so a retry stays a safe no-op even once
a campaign is exhausted.

Before recording a new (non-duplicate) conversion, the endpoint enforces the
owning campaign's `max_conversions` and `budget_minor_units`, returning 409
if either would be exceeded — `budget_minor_units` is compared against the
sum of that campaign's commission amounts (excluding `rejected`; a
`reversed` commission still counts, since the campaign paid it out at some
point). The campaign row is locked with `SELECT ... FOR UPDATE` for the rest
of the request so two concurrent conversions against a near-exhausted
campaign can't both slip past the check before either commits.

### Fraud detection

`app/services/fraud.py` is a rule-based detector — no ML/external service —
run inline in `POST /api/webhooks/conversions` right after a new conversion
and its commission are created. Two deterministic heuristics, each
independently togglable via env vars (see `app/core/config.py`):

- **`instant_conversion`** (severity `high`): the conversion was reported
  less than `FRAUD_MIN_CLICK_TO_CONVERSION_SECONDS` (default 3) after the
  click it's attributed to — a real checkout can't complete that fast, so
  this is almost certainly a fabricated or replayed webhook call.
- **`velocity_abuse`** (severity `medium`): the same promoter has more than
  `FRAUD_VELOCITY_MAX_CONVERSIONS` (default 3) conversions on the same
  campaign within `FRAUD_VELOCITY_WINDOW_MINUTES` (default 10) — looks like
  self-dealing/farming rather than organic sales.

A flag never blocks recording the conversion itself — it only withholds the
commission from the *automatic* approval step below. A business reviews and
resolves flags for their own commissions at `GET /api/business/fraud-flags`
/ `POST /api/business/fraud-flags/{id}/resolve` (surfaced in the Commissions
dashboard as a "⚠ Flagged" banner with a Clear Flag(s) action), or sidesteps
a flag entirely by approving/rejecting the commission manually — a
deliberate human decision overrides the heuristic.

### Commission lifecycle

`app/services/commission_lifecycle.py` is the one place that enforces legal
status transitions (`pending → approved → available → paid`, with `rejected`
and `reversed` branches) and posts the ledger entries they imply — see
`nexshare-skill/references/architecture.md` §4. Two transitions are
automatic and rule-based rather than manual:

- `pending → approved`, once there's no unresolved `FraudFlag` against the
  commission — see Fraud detection above for what writes those flags.
- `approved → available`, once the owning campaign's `hold_period_days`
  (default 3) has elapsed since approval.

There's no task scheduler in this project, so run the sweep by hand (or from
cron) with:

```bash
python -m app.scripts.process_commissions
```

`rejected` and `reversed` are always a deliberate business action — see the
`/api/business/commissions/*` endpoints above. `available → paid` is
triggered by `POST /api/promoters/me/withdraw` (`app/services/payouts.py`):
it withdraws the promoter's *entire* available balance in one action (no
partial-amount withdrawal — splitting a single commission's earned amount
across two payouts would break the one-ledger-entry-per-commission model),
transitions every `available` commission to `paid`, and posts a
`payout_debit` ledger entry that nets exactly against the `commission_earned`
entries it's paying out. The resulting `Payout` row's status depends on
whether Paystack is configured — see below.

Auth is cookie-based (JWT in an HttpOnly cookie), issued once verification
completes.

### Payment rail (Paystack)

Withdrawing is wired to a real payment rail — [Paystack](https://paystack.com)
— via `app/services/paystack.py`. Set `PAYSTACK_SECRET_KEY` (a test key,
`sk_test_...`, exercises the whole flow against Paystack's sandbox without
moving real money) and:

1. A promoter saves a payout destination first: `GET /api/promoters/payout-banks`
   lists Paystack's own bank codes (de-duplicated — Paystack's list has a
   handful of banks listed twice under the same code), `POST
   /api/promoters/me/payout-account/resolve` looks up the real account name
   for a bank/account-number pair (catches a typo'd digit before it's ever
   saved), and `POST /api/promoters/me/payout-account` re-resolves it
   server-side (never trusts a client-supplied name), registers a Paystack
   transfer recipient, and saves the result — one payout account per
   promoter, replaced wholesale rather than edited in place.
2. `POST /api/promoters/me/withdraw` now requires that saved payout account
   and actually initiates a Paystack transfer for the withdrawn amount,
   storing the `reference`/`transfer_code` on the `Payout` row and setting
   its status from Paystack's initial response (usually `processing` —
   `completed`/`failed` only comes back instantly for rare same-bank/instant
   corridors). If Paystack rejects the transfer outright (bad recipient,
   insufficient platform balance), the whole withdrawal — including the
   commission `paid` transitions and ledger entry — is rolled back; nothing
   is left half-done.
3. `POST /api/webhooks/paystack` is how a `processing` payout actually
   becomes `completed` or `failed` — Paystack calls it when the transfer
   settles, signature-verified (HMAC-SHA512 over the raw body with the
   secret key, `x-paystack-signature`) the same way `/webhooks/conversions`
   uses a static secret instead of a session. `app/scripts/sync_payouts.py`
   is a polling fallback for any payout a webhook never reached (no public
   URL in local dev, a dropped delivery in production) — same "no task
   scheduler, run by hand or from cron" pattern as `process_commissions`:
   ```bash
   python -m app.scripts.sync_payouts
   ```

Leave `PAYSTACK_SECRET_KEY` unset and withdrawing behaves exactly as before
this was wired up: a `Payout` is created and just stays `requested` forever,
no payout account required. Paystack transfer recipients are `type: "nuban"`
(bank account) only — `mobile_money` is still a selectable `payout_method`
label but isn't actually wired to a Paystack recipient type yet.

### Email + phone verification

Registration doesn't log you in — it sends a 6-digit code to both email and
phone (`app/services/verification.py`) and returns a short-lived
`pending_verification_token` scoped only to `/api/auth/verify*` (it's
rejected by every other endpoint, see `app/api/deps.py`). Login refuses an
account until both are verified; if that happens, the frontend calls
`/api/auth/verify/start` (password re-check) to get a fresh token and picks
up the same verification UI.

Codes live in **Redis** (`verification:{account_id}:{channel}`, bcrypt-hashed,
expiring via `EXPIRE` — not a Postgres table), since a short-lived,
write-once secret with no reporting value once consumed is exactly what
Redis's TTL is for. The resend cooldown is a second key
(`verification:cooldown:...`) claimed atomically with `SET NX`.

Delivery is provider-agnostic (`app/services/notifications`) — `EmailSender`/
`SmsSender` are small Protocols; swapping providers means writing one new
adapter class, not touching the verification logic. Wired providers:
**Resend** for email, **Termii** for SMS (`RESEND_API_KEY`/`TERMII_API_KEY`
in `.env`). Leave either unset and that channel's code is logged to the API
console instead of actually sent — registration still works end-to-end
without either account.

**TEST MODE banner.** While a channel's provider key is unset,
`/auth/register`, `/auth/verify/start`, and `/auth/verify/resend` also
return that channel's code directly in the response (`email_test_code` /
`phone_test_code` / `test_code`), and the verification screen shows it in
a labeled amber "TEST MODE" banner — no need to go check the `uvicorn`
terminal. This is self-disabling: set a real `RESEND_API_KEY` /
`TERMII_API_KEY` (in `.env` locally, or in Coolify for production) and
redeploy, and the corresponding field comes back `null` — the banner and
code disappear on their own, no code change required.

Accounts that existed before this feature (including the seeded demo
accounts) were grandfathered as verified by the migration that added it —
`demo.promoter@nexshare.app` / `demo.business@nexshare.app` still log in
directly, no code needed.

### Storefront

Each promoter has one public, no-login page — `/store/{promoter_id}` on the
web app, backed by `GET /api/storefront/{promoter_id}` — listing every offer
they're actively promoting. It's not a new tracking mechanism: it just
surfaces their existing `tracking_links`, joined the same way
`GET /api/tracking-links` does (active offer + active campaign), so a click
from the storefront attributes exactly like one from a link shared directly.
A promoter manages/previews theirs at `/dashboard/storefront`, which shows
their shareable storefront URL (copy/view) plus a live preview of the same
page.

### Business Commissions dashboard

`/business/commissions` is the frontend for the approve/reject/reverse and
webhook-secret endpoints listed above — previously API-only, so a business
had no way to actually run the commission-review workflow without `curl`.
Filter pills by status; a pending commission shows Approve/Reject, and any
commission that reached `approved`/`available`/`paid` shows Reverse (mirrors
the states `transition()` actually accepts — see `commission_lifecycle.py`).
The webhook secret is shown masked with Show/Copy/Rotate — rotating asks for
confirmation first since it invalidates the current secret immediately,
breaking the checkout integration until it's updated. Reachable via a new
nav link in `BusinessTopbar`, alongside the existing offer-listing page.

### Data model

`Account` (promoter or business) → `Offer` → `Campaign` → `TrackingLink` →
`Click` → `Conversion` → `Commission` → `LedgerEntry` / `Payout`, with
`FraudFlag`s attachable along the way. See `app/models/core.py`.

## 3. Frontend (apps/web)

```bash
cd apps/web
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The dev server proxies
`/api/*` requests to the backend (`http://localhost:8000` by default — see
`next.config.js`); override with an `API_URL` env var if the backend runs
elsewhere.

Log in at `/login` with the demo credentials above, or register a new
account at `/register`.

### Known Next.js security advisories

Pinned to `14.2.35` (bumped from `14.2.5`), which patches a High-severity
React Server Components DoS and a Medium source-code-exposure issue
(CVE-2025-55184/67779, CVE-2025-55183) — see
[Next.js's advisory](https://nextjs.org/blog/security-update-2025-12-11).
That was a same-minor patch bump, no breaking changes.

Separately, `npm audit` flags a **Critical** unauthenticated RCE in Next's
built-in Image Optimization API when AVIF files are used
([GHSA-2xp9-vwfh-vxw4](https://github.com/advisories/GHSA-2xp9-vwfh-vxw4))
— this one has **no fix within the 14.x line**; the real patch requires
Next 15.5.24+ or 16.x, a major upgrade out of scope here (breaking changes
across the App Router APIs this app uses throughout). Since this app never
uses `next/image` — every image is a plain `<img>` tag — the vulnerable
route provides no benefit, so it's disabled outright instead:
`images: { unoptimized: true }` in `next.config.js`. That closes the actual
attack surface without needing the major upgrade; it does mean a real
Next.js 15/16 upgrade is still a legitimate future task if this app is ever
deployed publicly and wants `next/image`'s optimization back.

## Running everything together

In three terminals:

```bash
# 1
cd infra && docker compose up -d

# 2
cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# 3
cd apps/web && npm run dev
```

If port 8000 is already in use by something else on your machine, change
terminal 2 to a free port and pass that same port to terminal 3:

```bash
# 2
cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8010

# 3
cd apps/web && API_URL=http://localhost:8010 npm run dev
```

## Database migrations

Migrations live in `apps/api/alembic/versions`. To create a new one after
changing a model in `app/models/core.py`:

```bash
cd apps/api
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Testing & CI

`.github/workflows/ci.yml` runs on every push/PR: a backend job (pytest
against real Postgres + Redis service containers) and a frontend job
(`tsc --noEmit`, `next lint`, `next build`).

### Backend tests

```bash
cd apps/api
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Requires Docker Desktop running (`docker compose up -d` in `infra/`) —
tests run against a disposable `nexshare_test` Postgres database,
drop-and-recreated fresh each run and migrated with the real Alembic chain
(see `tests/conftest.py`), and Redis logical db 15. Neither ever touches
the dev database/Redis db 0 a developer might have real data in, and
`PAYSTACK_SECRET_KEY` is force-unset for the whole run regardless of what's
in `.env` — no test can reach the real Paystack API even by accident.

Coverage, deliberately scoped to the money-critical logic rather than the
whole app: the commission lifecycle state machine and its automatic
sweep gates (`tests/test_commission_lifecycle.py`), the fraud rules
(`tests/test_fraud.py`), the conversion webhook's idempotency/cap/budget
enforcement (`tests/test_webhooks_conversions.py`), the payout flow
including its rollback-on-provider-rejection path
(`tests/test_payouts.py`), and the Paystack webhook's signature
verification and status mapping (`tests/test_paystack_webhook.py`).
Everything else (auth/verification, storefront, business offer CRUD,
analytics) is still only hand-verified — a real gap, not claimed as
covered.

### Frontend checks

```bash
cd apps/web
npx tsc --noEmit
npm run lint
npm run build
```

No component/integration test suite exists yet for the frontend — these
three are compile/lint/build correctness checks, not behavior tests.

## Troubleshooting

- **`uvicorn` won't start / "address already in use" on port 8000**:
  something else on your machine already owns that port. Run the API on
  a different port and pass the same value as `API_URL` to the frontend —
  see "Running everything together" above.
- **Login/API calls hang or return 500s referencing a Postgres connection
  timeout**: Docker Desktop isn't responding. Check `docker ps` — if it
  hangs too, restart Docker Desktop, wait for the containers in
  `infra/docker-compose.yml` to come back healthy, then restart the API
  process (it does not auto-reconnect after Postgres was unreachable for a
  while).
- **`alembic upgrade head` can't connect**: make sure `docker compose up -d`
  finished and Postgres is healthy (`docker ps`) before running migrations.
- **Verification codes seem to vanish, or you see Redis keys you didn't
  create**: something else on your machine is already running
  `redis-server` bound to `localhost:6379` — macOS routes a `localhost`
  connection to that specific-address bind ahead of Docker's `0.0.0.0:6379`
  wildcard bind, so the API silently talks to that other Redis instead of
  `nexshare-redis`. Check with `lsof -i :6379`; if something other than
  `com.docker...` owns `localhost:6379` specifically, stop it or change
  `REDIS_URL`/the compose port mapping to a non-default port.
- **`/payout-account/resolve` fails with "Test mode daily limit of 3 live
  bank resolves exceeded"**: a Paystack test key can only resolve *real*
  bank codes 3 times a day — a sandbox-wide cap, not per-bank-code. Use
  bank code `001` (a dedicated always-succeeds test entry, not listed in
  `/api/promoters/payout-banks` since it isn't a real bank) for resolve
  during development; note that `001` only works for `/bank/resolve`, not
  for actually registering a transfer recipient, so it can't complete a
  full save → withdraw cycle — only real bank codes can.
- **Withdrawing fails with "Please set a phone number for your business
  from the compliance page"**: a one-time requirement on the Paystack
  *account* the secret key belongs to, not something this app can satisfy
  via API — add a phone number on that Paystack dashboard's compliance/
  settings page.
