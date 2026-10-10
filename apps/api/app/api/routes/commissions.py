from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_promoter
from app.core.db import get_db
from app.models.core import Account, Campaign, Commission, Conversion, Offer

router = APIRouter()


class CommissionOut(BaseModel):
    id: str
    offer_title: str
    amount_minor_units: int
    currency: str
    status: str
    created_at: str


@router.get("", response_model=list[CommissionOut])
def list_commissions(
    account: Account = Depends(require_promoter),
    db: Session = Depends(get_db),
) -> list[CommissionOut]:
    rows = db.execute(
        select(Commission, Offer.title)
        .join(Conversion, Conversion.id == Commission.conversion_id)
        .join(Campaign, Campaign.id == Conversion.campaign_id)
        .join(Offer, Offer.id == Campaign.offer_id)
        .where(Commission.promoter_id == account.id)
        .order_by(Commission.created_at.desc())
    ).all()
    return [
        CommissionOut(
            id=str(commission.id),
            offer_title=offer_title,
            amount_minor_units=commission.amount_minor_units,
            currency=commission.currency,
            status=commission.status,
            created_at=commission.created_at.isoformat(),
        )
        for commission, offer_title in rows
    ]
