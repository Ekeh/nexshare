import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_promoter
from app.core.config import get_settings
from app.core.db import get_db
from app.models.core import Account, Commission, LedgerEntry, Payout, PayoutAccount
from app.services.payouts import NoAvailableBalanceError, NoPayoutAccountError, PayoutProviderError, request_payout
from app.services.paystack import PaystackClient, PaystackError

router = APIRouter()
settings = get_settings()


def _paystack_client() -> PaystackClient:
    if not settings.paystack_secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Payouts aren't configured yet")
    return PaystackClient(settings.paystack_secret_key)


class PromoterMeOut(BaseModel):
    id: str
    full_name: str
    email: str
    kyc_status: str


class StatValue(BaseModel):
    amount_minor_units: int
    currency: str
    change_pct: float | None = None


class PromoterStatsOut(BaseModel):
    today_earnings: StatValue
    month_earnings: StatValue
    pending: StatValue
    total_earned: StatValue


def _sum_ledger(
    db: Session,
    promoter_id,
    entry_type: str,
    since: datetime | None = None,
    until: datetime | None = None,
) -> int:
    stmt = select(func.coalesce(func.sum(LedgerEntry.amount_minor_units), 0)).where(
        LedgerEntry.account_id == promoter_id,
        LedgerEntry.entry_type == entry_type,
    )
    if since is not None:
        stmt = stmt.where(LedgerEntry.created_at >= since)
    if until is not None:
        stmt = stmt.where(LedgerEntry.created_at < until)
    return int(db.scalar(stmt) or 0)


def _pct_change(current: int, previous: int) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


@router.get("/me", response_model=PromoterMeOut)
def promoter_me(account: Account = Depends(require_promoter)) -> PromoterMeOut:
    return PromoterMeOut(
        id=str(account.id),
        full_name=account.full_name,
        email=account.email,
        kyc_status=account.kyc_status,
    )


@router.get("/me/stats", response_model=PromoterStatsOut)
def promoter_stats(
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> PromoterStatsOut:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    month_start = today_start.replace(day=1)
    last_month_end = month_start
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    trailing_30_start = now - timedelta(days=30)
    prior_30_start = now - timedelta(days=60)

    currency = db.scalar(
        select(LedgerEntry.currency).where(LedgerEntry.account_id == account.id).limit(1)
    ) or "USD"

    entry_type = "commission_earned"
    today_earned = _sum_ledger(db, account.id, entry_type, since=today_start)
    yesterday_earned = _sum_ledger(db, account.id, entry_type, since=yesterday_start, until=today_start)
    month_earned = _sum_ledger(db, account.id, entry_type, since=month_start)
    last_month_earned = _sum_ledger(db, account.id, entry_type, since=last_month_start, until=last_month_end)
    total_earned = _sum_ledger(db, account.id, entry_type)
    trailing_30_earned = _sum_ledger(db, account.id, entry_type, since=trailing_30_start)
    prior_30_earned = _sum_ledger(db, account.id, entry_type, since=prior_30_start, until=trailing_30_start)

    pending_amount = int(
        db.scalar(
            select(func.coalesce(func.sum(Commission.amount_minor_units), 0)).where(
                Commission.promoter_id == account.id,
                Commission.status == "pending",
            )
        )
        or 0
    )

    return PromoterStatsOut(
        today_earnings=StatValue(
            amount_minor_units=today_earned,
            currency=currency,
            change_pct=_pct_change(today_earned, yesterday_earned),
        ),
        month_earnings=StatValue(
            amount_minor_units=month_earned,
            currency=currency,
            change_pct=_pct_change(month_earned, last_month_earned),
        ),
        pending=StatValue(amount_minor_units=pending_amount, currency=currency),
        total_earned=StatValue(
            amount_minor_units=total_earned,
            currency=currency,
            change_pct=_pct_change(trailing_30_earned, prior_30_earned),
        ),
    )


class WithdrawIn(BaseModel):
    payout_method: Literal["bank_transfer", "mobile_money"]


class PayoutOut(BaseModel):
    id: str
    amount_minor_units: int
    currency: str
    payout_method: str
    status: str
    failure_reason: str | None
    requested_at: str


def _payout_out(payout: Payout) -> PayoutOut:
    return PayoutOut(
        id=str(payout.id),
        amount_minor_units=payout.amount_minor_units,
        currency=payout.currency,
        payout_method=payout.payout_method,
        status=payout.status,
        failure_reason=payout.failure_reason,
        requested_at=payout.requested_at.isoformat(),
    )


@router.post("/me/withdraw", response_model=PayoutOut, status_code=status.HTTP_201_CREATED)
def withdraw(
    payload: WithdrawIn,
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> PayoutOut:
    """Withdraws the promoter's entire available balance — see
    app/services/payouts.py for why this isn't a partial-amount request."""
    try:
        payout = request_payout(db, account, payload.payout_method)
    except NoAvailableBalanceError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No available balance to withdraw")
    except NoPayoutAccountError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Add a payout account before withdrawing")
    except PayoutProviderError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Payout provider rejected this transfer: {exc}")
    return _payout_out(payout)


@router.get("/me/payouts", response_model=list[PayoutOut])
def list_payouts(
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> list[PayoutOut]:
    rows = db.scalars(
        select(Payout).where(Payout.promoter_id == account.id).order_by(Payout.requested_at.desc())
    ).all()
    return [_payout_out(p) for p in rows]


class BankOut(BaseModel):
    name: str
    code: str


@router.get("/payout-banks", response_model=list[BankOut])
def list_payout_banks(account: Account = Depends(require_promoter)) -> list[BankOut]:
    """Bank list for the payout-account form's dropdown — Paystack's own
    canonical name/code pairs, so a bank_code sent back to /payout-account
    is always one Paystack itself recognizes. Paystack's list has a
    handful of institutions listed twice under the same bank_code (a
    renamed entry left alongside the old one) — de-duplicated by code,
    since that's the only part of the pair we actually send back to them."""
    banks = _paystack_client().list_banks()
    seen: set[str] = set()
    out = []
    for b in banks:
        if b["code"] in seen:
            continue
        seen.add(b["code"])
        out.append(BankOut(name=b["name"], code=b["code"]))
    return out


class ResolveAccountIn(BaseModel):
    bank_code: str
    account_number: str


class ResolveAccountOut(BaseModel):
    account_name: str


@router.post("/me/payout-account/resolve", response_model=ResolveAccountOut)
def resolve_payout_account(
    payload: ResolveAccountIn,
    account: Account = Depends(require_promoter),
) -> ResolveAccountOut:
    """Looks up the real account name for a bank_code/account_number pair
    before it's saved — lets the promoter confirm it's actually their
    account (or catch a typo'd digit) instead of finding out on the first
    failed transfer."""
    try:
        data = _paystack_client().resolve_account(account_number=payload.account_number, bank_code=payload.bank_code)
    except PaystackError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Couldn't verify that account: {exc}")
    return ResolveAccountOut(account_name=data["account_name"])


class SavePayoutAccountIn(BaseModel):
    payout_method: Literal["bank_transfer", "mobile_money"]
    bank_code: str
    account_number: str


class PayoutAccountOut(BaseModel):
    payout_method: str
    bank_name: str
    account_number_masked: str
    account_name: str


def _payout_account_out(pa: PayoutAccount) -> PayoutAccountOut:
    return PayoutAccountOut(
        payout_method=pa.payout_method,
        bank_name=pa.bank_name,
        account_number_masked=f"••••{pa.account_number[-4:]}",
        account_name=pa.account_name,
    )


@router.get("/me/payout-account", response_model=PayoutAccountOut | None)
def get_payout_account(
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> PayoutAccountOut | None:
    pa = db.scalar(select(PayoutAccount).where(PayoutAccount.promoter_id == account.id))
    return _payout_account_out(pa) if pa else None


@router.post("/me/payout-account", response_model=PayoutAccountOut, status_code=status.HTTP_201_CREATED)
def save_payout_account(
    payload: SavePayoutAccountIn,
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> PayoutAccountOut:
    """Re-resolves the account name server-side (never trusts a client-
    supplied name) and registers a fresh Paystack transfer recipient,
    replacing any existing payout account wholesale rather than editing one
    in place — see PayoutAccount's docstring."""
    client = _paystack_client()
    try:
        resolved = client.resolve_account(account_number=payload.account_number, bank_code=payload.bank_code)
        bank_name = next(
            (b["name"] for b in client.list_banks() if b["code"] == payload.bank_code), payload.bank_code
        )
        recipient = client.create_transfer_recipient(
            account_number=payload.account_number,
            bank_code=payload.bank_code,
            account_name=resolved["account_name"],
        )
    except PaystackError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Couldn't save that payout account: {exc}")

    existing = db.scalar(select(PayoutAccount).where(PayoutAccount.promoter_id == account.id))
    if existing is not None:
        db.delete(existing)
        db.flush()

    payout_account = PayoutAccount(
        id=uuid.uuid4(),
        promoter_id=account.id,
        payout_method=payload.payout_method,
        bank_code=payload.bank_code,
        bank_name=bank_name,
        account_number=payload.account_number,
        account_name=resolved["account_name"],
        paystack_recipient_code=recipient["recipient_code"],
    )
    db.add(payout_account)
    db.commit()
    return _payout_account_out(payout_account)
