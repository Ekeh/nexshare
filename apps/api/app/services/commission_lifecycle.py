"""The commission lifecycle state machine — nexshare-skill/references/
architecture.md §4.

    pending -> approved -> available -> paid
       \\-> rejected        \\-> reversed (from approved/available/paid)

This is the one place that enforces legal transitions and records them, per
architecture.md's explicit instruction ("one place that enforces legal
transitions... rather than ad-hoc status string checks scattered across the
codebase"). Every caller — the automatic sweep below or a business's manual
approve/reject/reverse action — goes through `transition()`.

Two transitions are automatic (time/rule-based, see `run_lifecycle_sweep`):
pending -> approved (once no unresolved fraud flag blocks it) and
approved -> available (once the campaign's hold period has elapsed).
rejected and reversed are always a deliberate business action — there is no
real fraud/dispute detector built yet, so nothing should look automatically
fraudulent or refunded. available -> paid is intentionally not automated
here either: it belongs to a Payout batch (the withdrawal flow), which
hasn't been built.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.core import Campaign, Commission, Conversion, FraudFlag, LedgerEntry

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"approved", "rejected"},
    "approved": {"available", "reversed"},
    "available": {"paid", "reversed"},
    "paid": {"reversed"},
    "rejected": set(),
    "reversed": set(),
}

# Statuses at which a commission_earned ledger entry has already been posted
# (see `transition`) — a reversal from one of these needs an offsetting entry;
# reversing straight out of "approved" doesn't, since nothing was posted yet.
_LEDGER_POSTED_STATUSES = {"available", "paid"}


class IllegalTransitionError(Exception):
    def __init__(self, commission_id: uuid.UUID, from_status: str, to_status: str):
        self.commission_id = commission_id
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(f"Commission {commission_id}: cannot move '{from_status}' -> '{to_status}'")


def transition(db: Session, commission: Commission, new_status: str, *, reason: str) -> Commission:
    """Apply a legal status transition, recording it in status_history and
    posting the ledger entry it implies. Raises IllegalTransitionError and
    changes nothing if the transition isn't legal from the current status."""
    current = commission.status
    if new_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise IllegalTransitionError(commission.id, current, new_status)

    now = datetime.now(timezone.utc)

    if new_status == "available":
        db.add(
            LedgerEntry(
                id=uuid.uuid4(),
                account_id=commission.promoter_id,
                commission_id=commission.id,
                entry_type="commission_earned",
                amount_minor_units=commission.amount_minor_units,
                currency=commission.currency,
                created_at=now,
            )
        )
    elif new_status == "reversed" and current in _LEDGER_POSTED_STATUSES:
        # Never delete/update the original entry — an immutable ledger nets
        # reversals as new, signed rows (architecture.md principle 16).
        db.add(
            LedgerEntry(
                id=uuid.uuid4(),
                account_id=commission.promoter_id,
                commission_id=commission.id,
                entry_type="commission_reversed",
                amount_minor_units=-commission.amount_minor_units,
                currency=commission.currency,
                created_at=now,
            )
        )

    # Reassign (don't .append) — SQLAlchemy only picks up JSON-column
    # mutations that produce a new object reference.
    commission.status_history = [
        *commission.status_history,
        {"status": new_status, "at": now.isoformat(), "reason": reason},
    ]
    commission.status = new_status
    db.flush()
    return commission


def _last_transition_at(commission: Commission, status: str) -> datetime | None:
    for entry in reversed(commission.status_history):
        if entry.get("status") == status:
            return datetime.fromisoformat(entry["at"])
    return None


def _has_unresolved_fraud_flags(db: Session, *, conversion_id: uuid.UUID, commission_id: uuid.UUID) -> bool:
    count = db.scalar(
        select(func.count()).select_from(FraudFlag).where(
            FraudFlag.resolved.is_(False),
            (
                (FraudFlag.subject_type == "conversion") & (FraudFlag.subject_id == conversion_id)
                | (FraudFlag.subject_type == "commission") & (FraudFlag.subject_id == commission_id)
            ),
        )
    )
    return bool(count)


def run_lifecycle_sweep(db: Session) -> dict[str, int]:
    """Apply the two automatic, rule-based transitions to every commission
    currently eligible. Idempotent — safe to run repeatedly (e.g. on a
    schedule); a commission not yet eligible is simply left where it is."""
    now = datetime.now(timezone.utc)
    approved_count = 0
    available_count = 0

    pending_rows = db.execute(
        select(Commission, Conversion.id)
        .join(Conversion, Conversion.id == Commission.conversion_id)
        .where(Commission.status == "pending")
    ).all()
    for commission, conversion_id in pending_rows:
        if not _has_unresolved_fraud_flags(db, conversion_id=conversion_id, commission_id=commission.id):
            transition(db, commission, "approved", reason="auto: no unresolved fraud flags")
            approved_count += 1

    approved_rows = db.execute(
        select(Commission, Campaign.hold_period_days)
        .join(Conversion, Conversion.id == Commission.conversion_id)
        .join(Campaign, Campaign.id == Conversion.campaign_id)
        .where(Commission.status == "approved")
    ).all()
    for commission, hold_period_days in approved_rows:
        approved_at = _last_transition_at(commission, "approved")
        if approved_at and now - approved_at >= timedelta(days=hold_period_days):
            transition(db, commission, "available", reason=f"auto: {hold_period_days}-day hold period elapsed")
            available_count += 1

    db.commit()
    return {"approved": approved_count, "available": available_count}
