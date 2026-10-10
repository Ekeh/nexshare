"""A promoter's public storefront (product-spec.md §7, "Personal Promoter
Store") — one page listing every offer they're actively promoting, each
linking through their real tracking link so a customer arriving from the
storefront attributes exactly like one from a direct share. No new
tracking mechanism: this just surfaces the promoter's existing
tracking_links.

Intentionally public — a customer browsing a promoter's store is never
logged in, so there's no require_promoter/business dependency here.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.models.core import Account, Campaign, Offer, TrackingLink

router = APIRouter()
settings = get_settings()


class StorefrontOfferOut(BaseModel):
    tracking_link_id: str
    url: str
    offer_id: str
    title: str
    description: str | None
    offer_type: str
    price_minor_units: int | None
    currency: str
    image_url: str | None


class StorefrontOut(BaseModel):
    promoter_name: str
    offers: list[StorefrontOfferOut]


@router.get("/{promoter_id}", response_model=StorefrontOut)
def get_storefront(promoter_id: str, db: Session = Depends(get_db)) -> StorefrontOut:
    try:
        pid = uuid.UUID(promoter_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storefront not found")

    promoter = db.get(Account, pid)
    if promoter is None or promoter.role != "promoter":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storefront not found")

    rows = db.execute(
        select(TrackingLink, Offer)
        .join(Campaign, Campaign.id == TrackingLink.campaign_id)
        .join(Offer, Offer.id == Campaign.offer_id)
        .where(
            TrackingLink.promoter_id == pid,
            Offer.status == "active",
            Campaign.status == "active",
        )
        .order_by(TrackingLink.created_at.desc())
    ).all()

    offers = [
        StorefrontOfferOut(
            tracking_link_id=str(link.id),
            url=f"{settings.public_base_url}/api/clicks/{link.short_code}",
            offer_id=str(offer.id),
            title=offer.title,
            description=offer.description,
            offer_type=offer.offer_type,
            price_minor_units=offer.price_minor_units,
            currency=offer.currency,
            image_url=(offer.branding or {}).get("image"),
        )
        for link, offer in rows
    ]
    return StorefrontOut(promoter_name=promoter.full_name, offers=offers)
