"""Requesting a withdrawal — the available -> paid step of the commission
lifecycle (app/services/commission_lifecycle.py), "triggered by a Payout
batch" per architecture.md §4.

Scope, deliberately: a promoter withdraws their *entire* available balance
in one action, not an arbitrary partial amount — splitting a single
commission's earned amount across two payouts would break the one
ledger-entry-per-commission model this is built on, and nothing has asked
for partial withdrawal. "Launch simply" (product-spec.md principle).

Paystack (app/services/paystack.py) is the real payment rail: if
PAYSTACK_SECRET_KEY is configured, withdrawing requires a saved
PayoutAccount and actually initiates a transfer, moving the Payout past
"requested" for real (to "processing", then "completed"/"failed" once
Paystack confirms — see the /api/webhooks/paystack handler and
app/scripts/sync_payouts.py). If Paystack isn't configured, this behaves
exactly as before it was wired up: a Payout is created and stays
"requested" forever. Either way, the commissions themselves move to "paid"
immediately — the platform has committed to paying them out, independent
of whether the bank transfer has settled.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.core import Account, Commission, LedgerEntry, Payout, PayoutAccount
from app.services.commission_lifecycle import transition
from app.services.paystack import PaystackClient, PaystackError

settings = get_settings()

# Paystack's own initial transfer statuses collapse to this app's three
# non-terminal-or-terminal Payout statuses. "success" is rare at initiate
# time (same-bank/instant corridors); everything else waits for the
# transfer.success/failed/reversed webhook — or sync_payouts.py.
_INITIATE_STATUS_MAP = {"success": "completed", "failed": "failed"}


class NoAvailableBalanceError(Exception):
    pass


class NoPayoutAccountError(Exception):
    """Paystack is configured but this promoter hasn't saved a payout
    destination yet — see POST /api/promoters/me/payout-account."""


class PayoutProviderError(Exception):
    """Paystack rejected the transfer outright (bad recipient, insufficient
    platform balance, etc.) — the whole withdrawal is rolled back, nothing
    is marked paid for a transfer that never actually started."""


def request_payout(db: Session, promoter: Account, payout_method: str) -> Payout:
    available = list(
        db.scalars(
            select(Commission).where(Commission.promoter_id == promoter.id, Commission.status == "available")
        )
    )
    if not available:
        raise NoAvailableBalanceError()

    payout_account: PayoutAccount | None = None
    if settings.paystack_secret_key:
        payout_account = db.scalar(select(PayoutAccount).where(PayoutAccount.promoter_id == promoter.id))
        if payout_account is None:
            raise NoPayoutAccountError()

    # In practice every commission here is the same currency (this app is
    # single-currency end to end) — grouping defensively rather than
    # assuming it, so a future multi-currency campaign can't silently pay
    # out the wrong amount by summing across currencies.
    by_currency: dict[str, list[Commission]] = {}
    for c in available:
        by_currency.setdefault(c.currency, []).append(c)

    # One Payout per currency; return the first (the only one, in the
    # current single-currency reality) for the API response.
    payouts: list[Payout] = []
    now = datetime.now(timezone.utc)
    for currency, commissions in by_currency.items():
        total = sum(c.amount_minor_units for c in commissions)

        payout = Payout(
            id=uuid.uuid4(),
            promoter_id=promoter.id,
            amount_minor_units=total,
            currency=currency,
            payout_method=payout_method,
            status="requested",
            requested_at=now,
        )
        db.add(payout)
        db.flush()

        for commission in commissions:
            transition(db, commission, "paid", reason=f"payout {payout.id} requested")

        db.add(
            LedgerEntry(
                id=uuid.uuid4(),
                account_id=promoter.id,
                payout_id=payout.id,
                entry_type="payout_debit",
                amount_minor_units=-total,
                currency=currency,
                created_at=now,
            )
        )

        if payout_account is not None:
            reference = str(payout.id)
            client = PaystackClient(settings.paystack_secret_key)
            try:
                data = client.initiate_transfer(
                    amount_minor_units=total,
                    recipient_code=payout_account.paystack_recipient_code,
                    reference=reference,
                    reason=f"NexShare payout {payout.id}",
                    currency=currency,
                )
            except PaystackError as exc:
                db.rollback()
                raise PayoutProviderError(str(exc)) from exc

            payout.paystack_reference = reference
            payout.paystack_transfer_code = data.get("transfer_code")
            payout.status = _INITIATE_STATUS_MAP.get(data.get("status", ""), "processing")

        payouts.append(payout)

    db.commit()
    return payouts[0]
