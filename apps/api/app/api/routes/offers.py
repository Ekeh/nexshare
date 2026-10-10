from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_promoter
from app.core.db import get_db
from app.models.core import Account, Campaign, Offer

router = APIRouter()


class OfferOut(BaseModel):
    id: str
    title: str
    description: str | None
    offer_type: str
    price_minor_units: int | None
    currency: str
    image_url: str | None
    commission_model: str
    commission_config: dict


@router.get("", response_model=list[OfferOut])
def list_offers(
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> list[OfferOut]:
    # One row per (offer, campaign); an offer with several active campaigns
    # is unusual for this MVP, so we just take the most recent campaign.
    rows = db.execute(
        select(Offer, Campaign)
        .join(Campaign, Campaign.offer_id == Offer.id)
        .where(Offer.status == "active", Campaign.status == "active")
        .order_by(Offer.created_at.desc(), Campaign.created_at.desc())
    ).all()

    seen_offer_ids: set = set()
    out: list[OfferOut] = []
    for offer, campaign in rows:
        if offer.id in seen_offer_ids:
            continue
        seen_offer_ids.add(offer.id)
        out.append(
            OfferOut(
                id=str(offer.id),
                title=offer.title,
                description=offer.description,
                offer_type=offer.offer_type,
                price_minor_units=offer.price_minor_units,
                currency=offer.currency,
                image_url=(offer.branding or {}).get("image"),
                commission_model=campaign.commission_model,
                commission_config=campaign.commission_config,
            )
        )
    return out
