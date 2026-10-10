"""Reconcile any Payout still "requested"/"processing" against Paystack's
own record of the transfer — a fallback for webhook delivery that never
reaches this app (no public URL in local dev, a dropped webhook in
production, etc.). POST /api/webhooks/paystack is the primary, real-time
path; this is the same "no task scheduler, run by hand or from cron"
pattern as app/scripts/process_commissions.

Run from apps/api with the venv active:
    python -m app.scripts.sync_payouts
"""
from __future__ import annotations

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models.core import Payout
from app.services.paystack import PaystackClient, PaystackError

# Mirrors _PAYSTACK_EVENT_STATUS in app/api/routes/webhooks.py — a fetched
# transfer's `status` field uses the same vocabulary as the webhook event
# suffix.
_TRANSFER_STATUS_MAP = {"success": "completed", "failed": "failed", "reversed": "failed"}


def main() -> None:
    settings = get_settings()
    if not settings.paystack_secret_key:
        print("PAYSTACK_SECRET_KEY not set — nothing to sync.")
        return

    client = PaystackClient(settings.paystack_secret_key)
    db = SessionLocal()
    updated = 0
    try:
        pending = db.scalars(
            select(Payout).where(
                Payout.status.in_(["requested", "processing"]), Payout.paystack_transfer_code.is_not(None)
            )
        ).all()
        for payout in pending:
            try:
                data = client.fetch_transfer(payout.paystack_transfer_code)
            except PaystackError as exc:
                print(f"  {payout.id}: couldn't fetch status ({exc})")
                continue

            new_status = _TRANSFER_STATUS_MAP.get(data.get("status", ""))
            if new_status is None or new_status == payout.status:
                continue

            payout.status = new_status
            if new_status == "failed":
                payout.failure_reason = data.get("reason") or data.get("status")
            updated += 1
            print(f"  {payout.id}: {payout.status} -> {new_status}")

        db.commit()
    finally:
        db.close()

    print(f"Synced {updated} payout(s).")


if __name__ == "__main__":
    main()
