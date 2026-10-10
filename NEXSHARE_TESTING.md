# NexShare — End-to-End Test Plan

A manual test script for a human tester to walk through the whole
application by hand: promoter and business onboarding, offer creation,
tracking links, the public storefront, the conversion webhook, fraud
detection, the commission lifecycle, and the Paystack payout flow.

Check boxes off as you go. Each step says what to do and what you should
see — anything else is a bug, worth filing with a screenshot and the exact
step number.

## 0. Before you start

- [ ] `cd infra && docker compose up -d` — wait until `docker ps` shows
      both `nexshare-postgres` and `nexshare-redis` as `healthy`.
- [ ] Backend: `cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8010`
      — leave this terminal visible, you'll read OTP codes from it.
- [ ] Frontend: `cd apps/web && npm run dev`
- [ ] `curl http://localhost:8010/health` returns `{"status": "ok"}`.
- [ ] Open `http://localhost:3000` — the landing page loads.

Use throwaway email addresses for every account you create in this test
(e.g. `yourname+promoter1@example.com`) — **never** the account you
actually use day to day. At the end of this script, §9 tells you how to
remove everything you created.

If `RESEND_API_KEY` / `TERMII_API_KEY` aren't set in `apps/api/.env`,
verification codes aren't actually emailed/texted — they're printed to the
backend terminal instead (`WARNING` level), which is what this script
assumes. If those keys _are_ set, check the real inbox/phone instead.

---

## 1. Promoter registration & verification

- [ ] Go to `/register`, select **I'm a Promoter**.
- [ ] Fill in full name, a throwaway email, a real-format phone number
      (`+234801xxxxxxx` or similar), and a password (8+ characters).
- [ ] Submit. You land on a verification screen showing masked email and
      phone, each with an "unverified" state and a code-entry box.
- [ ] In the backend terminal, find two `WARNING` lines with 6-digit
      codes — one for the email channel, one for phone.
- [ ] Enter the email code. That channel flips to verified.
- [ ] Enter the phone code. You're redirected straight into
      `/dashboard` — **logged in**, no separate login step.
- [ ] Try clicking "Resend" immediately after a send — it should refuse
      with a cooldown message (don't wait it out; just confirm it's
      blocked).
- [ ] Enter a deliberately wrong 6-digit code once — it should say the
      code isn't right, not crash or silently accept it.

## 2. Business registration & verification

- [ ] Log out (top-right).
- [ ] Repeat §1, this time selecting **I'm a Business**.
- [ ] Confirm you land on `/business` (not `/dashboard`) once verified.

## 3. Login edge cases

- [ ] Log out. At `/login`, try the promoter's email with a **wrong**
      password — should fail with a clear error, not a crash.
- [ ] Log back in with the correct password — should land back on
      `/dashboard`.

## 4. Business: publish an offer

Log in as the business account from §2.

- [ ] Go to `/business` (should be the default landing page for a
      business).
- [ ] Fill out **List Your Offer**: pick a category, give it a title and
      description, set a price and a commission (percentage or fixed —
      try percentage first), and a destination URL (any real URL, e.g.
      `https://example.com`).
- [ ] Optional: upload an image and confirm the live preview panel updates
      as you type.
- [ ] Submit. A success message appears and the offer shows up in **Your
      Offers** below the form.
- [ ] Go to `/business/commissions`. Confirm a **Webhook Secret** card is
      visible with a masked secret, and **Show** / **Copy** / **Rotate**
      buttons. Click **Show** — the full secret appears. Click **Copy** and
      confirm the button briefly shows "Copied."
      **Don't click Rotate** unless you're prepared to redo this from
      §4 — it invalidates the secret immediately.
- [ ] Copy the full webhook secret somewhere for §7.

## 5. Promoter: find the offer, create a tracking link

Log in as the promoter account from §1 (or open a second browser/incognito
window so both sessions are live at once — useful for the rest of this
script).

- [ ] Go to `/dashboard/offers` ("Find Offers"). The offer from §4 appears,
      with its commission shown as a badge.
- [ ] Click **Promote** on it. You land on a Share & Earn screen with a
      real tracking link (a short URL) and share buttons.
- [ ] Copy the tracking link somewhere for §7.
- [ ] Go to `/dashboard/links` ("My Links"). The same link appears there.
- [ ] Click **Copy** on it — confirm the "Copied" state appears briefly.

## 6. Storefront

- [ ] Go to `/dashboard/storefront`. Confirm it shows a shareable URL
      (`/store/<a long id>`) and, below it, a live preview containing the
      offer from §4 with its price and a **Get This Deal** button.
- [ ] Copy that storefront URL, open it in a **new incognito window** (no
      login) — confirm the same offer renders publicly, with the
      promoter's name as the page heading.
- [ ] In that same incognito window, try a nonsense storefront URL (change
      the id to something like `00000000-0000-0000-0000-000000000000`) —
      confirm you get a clean "storefront not found" message, not a crash.

## 7. Record a real conversion (the webhook)

This step needs a terminal, not the browser — it's how a business's real
checkout would report a completed sale.

- [ ] Visit the tracking link from §5 in a browser tab (don't submit
      anything — just load it). It should redirect you to the offer's
      destination URL, with `?nx_click=<something>` appended to that URL's
      query string. Copy that `nx_click` value.
- [ ] Run, filling in your own webhook secret (§4) and click id:
  ```bash
  curl -s -X POST http://localhost:8000/api/webhooks/conversions \
    -H "Authorization: Bearer <webhook secret from §4>" \
    -H "Content-Type: application/json" \
    -d '{"click_id":"<nx_click value>","external_ref":"tester-order-1"}'
  ```
- [ ] Response is `HTTP 201` with a `commission_id` and `"duplicate":false`.
- [ ] Run the **exact same command again**. This time `"duplicate":true`
      comes back, with the same `commission_id` as before — retrying a
      webhook call must never double-charge a sale.
- [ ] Refresh `/dashboard/earnings` (promoter) — the new commission shows
      up as **Pending**.
- [ ] Refresh `/business/commissions` (business) — the same commission
      shows up as **Pending**, with **Approve** / **Reject** buttons.

## 8. Fraud detection

- [ ] Repeat the click-then-webhook sequence from §7 with a **new**
      `external_ref` (e.g. `tester-order-2`) — but this time run the curl
      command **immediately** after loading the tracking link, within a
      second or two.
- [ ] Refresh `/business/commissions` — this new commission shows a red
      **⚠ Flagged: Instant Conversion** banner with a **Clear Flag**
      button.
- [ ] Click **Clear Flag** — the banner disappears from that row.
- [ ] (Optional, needs 4+ rapid conversions) Repeat the fast click→webhook
      sequence four times in under 10 minutes with different
      `external_ref`s each time — the 4th one onward should additionally
      show a **High Velocity** flag alongside Instant Conversion.

## 9. Commission actions & the lifecycle sweep

- [ ] On `/business/commissions`, click **Approve** on the commission from
      §7 (the un-flagged one). Its badge changes to **Approved**.
- [ ] Try **Reverse** on the same commission — badge changes to
      **Reversed**. (This is a one-way action in this script — reversing
      is meant for refunds/chargebacks, so only do it here as a test.)
- [ ] On the commission from §8, once its flag is cleared, click
      **Approve** manually as well.
- [ ] From a terminal, with the venv active:
  ```bash
  python -m app.scripts.process_commissions
  ```
  This is the automatic sweep a real deployment would run on a schedule —
  it prints how many commissions it approved/advanced. Newly-approved
  commissions won't move to **Available** yet (campaigns hold for 3 days
  by default); that's expected, not a bug.

## 10. Withdraw & payout account (Paystack)

This needs `PAYSTACK_SECRET_KEY` set to a **test** key
(`sk_test_...`) in `apps/api/.env`. If it's unset, `/dashboard/withdraw`
still works but skips straight to "Withdraw Available Balance" with no
payout-account step — confirm that simpler version behaves sensibly
(disabled until there's a balance) and skip to §11.

- [ ] On `/dashboard/withdraw`, confirm a **Payout Account** card appears
      with an **Add Account** button.
- [ ] Click it. Select a real bank from the dropdown (e.g. "Zenith Bank"),
      enter account number `0000000000` (Paystack's own test account
      number — always resolves in test mode), click **Verify**. - If you see "Test mode daily limit of 3 live bank resolves
      exceeded," that's a Paystack sandbox quota, not a bug — wait for
      it to reset (24h) or borrow a different test key.
- [ ] Once verified, click **Save**. The card now shows the resolved
      account name and bank.
- [ ] With a commission in **Available** status (none will be, right
      after §9 — see the note below), the **Withdraw Available Balance**
      button becomes enabled.

  To actually reach **Available** without waiting 3 real days, an
  engineer can backdate one commission's approval timestamp directly in
  the database — this isn't something a tester does by hand; if you need
  this for a full payout test, ask engineering to fast-forward one
  commission for you.

- [ ] Click **Withdraw Available Balance**. Expect one of:
  - A **success** state and a new row in Payout History with status
    **Processing** (or, rarely, **Completed**) — the happy path.
  - A clear error mentioning Paystack rejected the transfer (e.g. a
    compliance requirement on the sandbox account) — this is a **known
    sandbox limitation**, not a product bug, _as long as_ your commission
    balance is unchanged afterward (check `/dashboard/earnings` — it
    should still show the commission as available, not silently gone).

## 11. Analytics

- [ ] As the promoter, visit `/dashboard/analytics`. Confirm the page
      renders (clicks/conversions/top-sources) without a crash, even with
      only the test data from this script.

## 12. Console/error check

While you're on each page above, open the browser's DevTools console
(F12) and confirm there are no red errors logged — a warning is fine, a
thrown error or a failed network request to `/api/*` (other than the ones
this script deliberately expects, like the 404 in §6) is worth reporting.

---

## Cleanup

Everything you created in this script (accounts, offer, tracking link,
commissions, payout account) is disposable test data. If you're on a
shared dev database, ask engineering to remove it rather than deleting it
yourself — commissions and ledger entries are meant to be immutable, so
there's no "delete" button in the product for a reason.

## What "done" looks like

Every checkbox above ticked, and no unexplained red console errors. Two
categories of "failure" are expected and are **not** bugs to report:

- Paystack sandbox account-level limits (the 3/day bank-resolve cap, or a
  missing compliance field on the test business) — these belong to the
  Paystack test account, not this codebase.
- Waiting on the 3-day campaign hold period — §9's automatic sweep won't
  move a commission to **Available** on the same day it was approved;
  that's the intended behavior, not a bug.

Everything else — a crash, a wrong number, a button that does nothing, a
console error, a double-charged webhook retry — is a real bug. File it
with the step number, what you expected, and what actually happened.
