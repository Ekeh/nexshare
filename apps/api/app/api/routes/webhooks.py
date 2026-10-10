"""Server-to-server: a business's own checkout reports a completed
conversion here so it flows into the real commission pipeline instead of
only existing via seed data. Authenticated with a static webhook secret
(app/api/deps.py get_business_from_webhook_secret), not a session — this is
called by their backend, not a logged-in browser.
"""
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_business_from_webhook_secret
from app.core.config import get_settings
from app.core.db import get_db
from app.models.core import Account, Campaign, Commission, Conversion, Offer, Payout, TrackingLink
from app.services.fraud import evaluate_conversion
from app.services.paystack import verify_webhook_signature

router = APIRouter()
settings = get_settings()
logger = logging.getLogger("nexshare.webhooks")

# amount_minor_units taken directly from commission_config, unscaled by sale value.
_FLAT_COMMISSION_MODELS = {"fixed", "qualified_lead", "booking", "milestone"}


class RecordConversionIn(BaseModel):
    click_id: str = Field(description="The nx_click value from the destination_url redirect query string.")
    external_ref: str | None = Field(
        default=None, description="Your own order/transaction id — makes a retried call safe to send twice."
    )
    value_minor_units: int | None = Field(default=None, ge=0, description="The actual sale value, if it varies.")
    currency: str | None = None


class RecordConversionOut(BaseModel):
    conversion_id: str
    commission_id: str
    commission_amount_minor_units: int
    currency: str
    duplicate: bool


def _compute_commission_amount(campaign: Campaign, value_minor_units: int | None) -> int:
    model = campaign.commission_model
    config = campaign.commission_config

    if model == "percentage":
        if value_minor_units is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_minor_units is required — this campaign's commission is a percentage of sale value",
            )
        pct = config.get("pct")
        if pct is None:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Campaign misconfigured: percentage model with no pct")
        return round(value_minor_units * pct / 100)

    if model in _FLAT_COMMISSION_MODELS:
        amount = config.get("amount_minor_units")
        if amount is None:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Campaign misconfigured: missing amount_minor_units")
        return int(amount)

    raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported commission model: {model}")


def _committed_spend(db: Session, campaign_id: uuid.UUID) -> int:
    """Sum of commission amounts already obligated against this campaign's
    budget. Excludes rejected (never earned); a reversed commission still
    counts — the campaign paid it out at some point, so a chargeback
    doesn't free up new budget."""
    return db.scalar(
        select(func.coalesce(func.sum(Commission.amount_minor_units), 0))
        .join(Conversion, Conversion.id == Commission.conversion_id)
        .where(Conversion.campaign_id == campaign_id, Commission.status != "rejected")
    )


@router.post("/conversions", response_model=RecordConversionOut, status_code=status.HTTP_201_CREATED)
def record_conversion(
    payload: RecordConversionIn,
    account: Account = Depends(get_business_from_webhook_secret),
    db: Session = Depends(get_db),
) -> RecordConversionOut:
    click_row = db.execute(
        text(
            "SELECT id, occurred_at, tracking_link_id FROM clicks WHERE click_id = :click_id "
            "ORDER BY occurred_at DESC LIMIT 1"
        ),
        {"click_id": payload.click_id},
    ).first()
    if click_row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown click_id")

    link_row = db.execute(
        select(TrackingLink, Campaign, Offer)
        .join(Campaign, Campaign.id == TrackingLink.campaign_id)
        .join(Offer, Offer.id == Campaign.offer_id)
        .where(TrackingLink.id == click_row.tracking_link_id)
    ).first()
    # Also 404 (not 403) if the click belongs to a campaign owned by a
    # different business — don't confirm the click_id even exists to them.
    if link_row is None or link_row[2].business_id != account.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown click_id")
    tracking_link, campaign, offer = link_row

    # Lock the campaign row for the rest of this transaction so two
    # concurrent conversions against the same near-exhausted campaign can't
    # both pass the cap/budget checks below before either one commits.
    campaign = db.execute(select(Campaign).where(Campaign.id == campaign.id).with_for_update()).scalar_one()

    # Check for a retried call up front — a real webhook sender retries on
    # timeout/5xx, and that has to stay a safe no-op even once the campaign
    # is at its cap, not get rejected as "over budget" for replaying a
    # conversion that was already accepted.
    if payload.external_ref is not None:
        existing = db.scalar(
            select(Conversion).where(
                Conversion.campaign_id == campaign.id, Conversion.external_ref == payload.external_ref
            )
        )
        if existing is not None:
            existing_commission = db.scalar(select(Commission).where(Commission.conversion_id == existing.id))
            if existing_commission is not None:
                return RecordConversionOut(
                    conversion_id=str(existing.id),
                    commission_id=str(existing_commission.id),
                    commission_amount_minor_units=existing_commission.amount_minor_units,
                    currency=existing_commission.currency,
                    duplicate=True,
                )

    if campaign.max_conversions is not None and campaign.conversions_count >= campaign.max_conversions:
        raise HTTPException(status.HTTP_409_CONFLICT, "Campaign has reached its maximum conversions")

    value_minor_units = payload.value_minor_units if payload.value_minor_units is not None else offer.price_minor_units
    commission_amount = _compute_commission_amount(campaign, value_minor_units)
    currency = payload.currency or offer.currency

    if campaign.budget_minor_units is not None:
        spent = _committed_spend(db, campaign.id)
        if spent + commission_amount > campaign.budget_minor_units:
            raise HTTPException(status.HTTP_409_CONFLICT, "Campaign budget exhausted")

    now = datetime.now(timezone.utc)

    conversion = Conversion(
        id=uuid.uuid4(),
        click_id=click_row.id,
        click_occurred_at=click_row.occurred_at,
        campaign_id=campaign.id,
        conversion_value_minor_units=value_minor_units,
        external_ref=payload.external_ref,
        # No fraud/validation service exists yet (see architecture doc) —
        # the business's own authenticated webhook call is, for now, the
        # validation. Matches the seed script's convention.
        status="approved",
        occurred_at=now,
    )
    db.add(conversion)
    try:
        db.flush()
    except IntegrityError:
        # Same (campaign_id, external_ref) as an earlier call — a real
        # webhook sender retries on timeout/5xx, so this has to be a safe
        # no-op, not a duplicate charge. Return what already exists.
        db.rollback()
        if payload.external_ref is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Conversion already recorded")
        existing = db.scalar(
            select(Conversion).where(
                Conversion.campaign_id == campaign.id, Conversion.external_ref == payload.external_ref
            )
        )
        existing_commission = (
            db.scalar(select(Commission).where(Commission.conversion_id == existing.id)) if existing else None
        )
        if existing is None or existing_commission is None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Conversion already recorded")
        return RecordConversionOut(
            conversion_id=str(existing.id),
            commission_id=str(existing_commission.id),
            commission_amount_minor_units=existing_commission.amount_minor_units,
            currency=existing_commission.currency,
            duplicate=True,
        )

    # The cap itself was already enforced above; this WHERE clause is just a
    # race-condition guard so two concurrent requests can't both slip past
    # max_conversions - 1 and push the counter over the limit.
    db.execute(
        text(
            "UPDATE campaigns SET conversions_count = conversions_count + 1 "
            "WHERE id = :id AND (max_conversions IS NULL OR conversions_count < max_conversions)"
        ),
        {"id": str(campaign.id)},
    )

    commission = Commission(
        id=uuid.uuid4(),
        conversion_id=conversion.id,
        promoter_id=tracking_link.promoter_id,
        amount_minor_units=commission_amount,
        currency=currency,
        status="pending",
        status_history=[{"status": "pending", "at": now.isoformat()}],
        created_at=now,
    )
    db.add(commission)
    db.flush()

    flags = evaluate_conversion(
        db, commission=commission, campaign_id=campaign.id, click_occurred_at=click_row.occurred_at
    )
    if flags:
        db.add_all(flags)
    db.commit()

    return RecordConversionOut(
        conversion_id=str(conversion.id),
        commission_id=str(commission.id),
        commission_amount_minor_units=commission_amount,
        currency=currency,
        duplicate=False,
    )


# Paystack event -> Payout status. transfer.reversed means Paystack sent the
# money back to the platform's balance (the recipient's bank rejected it,
# wrong account details, etc.) — a failure from the promoter's point of
# view, same as transfer.failed, just with a different reason on Paystack's
# side of things.
_PAYSTACK_EVENT_STATUS = {
    "transfer.success": "completed",
    "transfer.failed": "failed",
    "transfer.reversed": "failed",
}


@router.post("/paystack", status_code=status.HTTP_200_OK)
async def paystack_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    """Paystack calls this when a transfer we initiated
    (app/services/payouts.py) finishes, asynchronously — initiating a
    transfer only ever returns a non-terminal status. Signature-verified
    (there's no session here; Paystack is a server, not a logged-in
    browser), not authenticated any other way, matching how
    /webhooks/conversions uses a static secret instead of a cookie/JWT."""
    if not settings.paystack_secret_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Payouts aren't configured")

    body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")
    if not verify_webhook_signature(payload=body, signature=signature, secret_key=settings.paystack_secret_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid signature")

    payload = await request.json()
    event = payload.get("event")
    new_status = _PAYSTACK_EVENT_STATUS.get(event)
    if new_status is None:
        # Paystack sends other event types (transfer.reversed's siblings,
        # recipient events, etc.) we don't act on — 200 so it doesn't retry
        # delivering an event we're intentionally ignoring.
        return {"ok": True, "ignored": event}

    data = payload.get("data", {})
    reference = data.get("reference")
    payout = db.scalar(select(Payout).where(Payout.paystack_reference == reference)) if reference else None
    if payout is None:
        logger.warning("Paystack webhook for unknown payout reference=%s event=%s", reference, event)
        return {"ok": True, "matched": False}

    payout.status = new_status
    if new_status == "failed":
        payout.failure_reason = data.get("reason") or event
    db.commit()
    return {"ok": True, "matched": True}
