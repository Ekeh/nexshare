import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.api.deps import require_promoter
from app.core.config import get_settings
from app.core.db import get_db
from app.models.core import Account, Campaign, Offer, TrackingLink

router = APIRouter()
settings = get_settings()


class CreateTrackingLinkIn(BaseModel):
    offer_id: str


class TrackingLinkOut(BaseModel):
    id: str
    short_code: str
    url: str
    offer_id: str
    offer_title: str
    offer_image_url: str | None


def _to_out(link: TrackingLink, offer: Offer) -> TrackingLinkOut:
    return TrackingLinkOut(
        id=str(link.id),
        short_code=link.short_code,
        url=f"{settings.public_base_url}/api/clicks/{link.short_code}",
        offer_id=str(offer.id),
        offer_title=offer.title,
        offer_image_url=(offer.branding or {}).get("image"),
    )


def _active_campaign_for_offer(db: Session, offer_id: uuid.UUID) -> tuple[Offer, Campaign]:
    row = db.execute(
        select(Offer, Campaign)
        .join(Campaign, Campaign.offer_id == Offer.id)
        .where(Offer.id == offer_id, Offer.status == "active", Campaign.status == "active")
        .order_by(Campaign.created_at.desc())
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found or not active")
    return row


@router.post("", response_model=TrackingLinkOut, status_code=status.HTTP_201_CREATED)
def create_tracking_link(
    payload: CreateTrackingLinkIn,
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> TrackingLinkOut:
    try:
        offer_id = uuid.UUID(payload.offer_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid offer_id")

    offer, campaign = _active_campaign_for_offer(db, offer_id)

    # One tracking link per promoter x campaign — reused across every share
    # channel, matching the single "Your Tracking Link" box in the Share &
    # Earn design (channel-specific buttons just wrap this same URL).
    #
    # Insert-then-fall-back-to-select (atomic via ON CONFLICT DO NOTHING),
    # not select-then-insert: two concurrent requests for the same
    # promoter+campaign (e.g. React Strict Mode double-firing an effect, or
    # a double-clicked "Promote") would otherwise both pass the "no
    # existing row" check and both insert, producing duplicates — the
    # tracking_links_promoter_campaign_key constraint (0005) makes that a
    # conflict instead, and this just re-fetches whichever request won.
    new_id = db.scalar(
        pg_insert(TrackingLink)
        .values(
            id=uuid.uuid4(),
            campaign_id=campaign.id,
            promoter_id=account.id,
            short_code=secrets.token_urlsafe(6),
        )
        .on_conflict_do_nothing(index_elements=["promoter_id", "campaign_id"])
        .returning(TrackingLink.id)
    )
    db.commit()

    if new_id is not None:
        link = db.get(TrackingLink, new_id)
    else:
        link = db.scalar(
            select(TrackingLink).where(
                TrackingLink.promoter_id == account.id, TrackingLink.campaign_id == campaign.id
            )
        )

    return _to_out(link, offer)


@router.get("", response_model=list[TrackingLinkOut])
def list_tracking_links(
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> list[TrackingLinkOut]:
    rows = db.execute(
        select(TrackingLink, Offer)
        .join(Campaign, Campaign.id == TrackingLink.campaign_id)
        .join(Offer, Offer.id == Campaign.offer_id)
        .where(TrackingLink.promoter_id == account.id)
        .order_by(TrackingLink.created_at.desc())
    ).all()
    return [_to_out(link, offer) for link, offer in rows]
