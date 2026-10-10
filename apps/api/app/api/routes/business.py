import secrets
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_business
from app.core.db import get_db
from app.models.core import Account, Campaign, Commission, Conversion, FraudFlag, Offer
from app.services.commission_lifecycle import IllegalTransitionError, transition

router = APIRouter()

# apps/api/app/api/routes/business.py -> parents[3] == apps/api
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "uploads" / "offers"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class CreateOfferIn(BaseModel):
    title: str
    description: str | None = None
    offer_type: str
    price_minor_units: int | None = None
    currency: str = "USD"
    image_url: str | None = None
    destination_url: str | None = None
    commission_model: str
    commission_config: dict


class BusinessOfferOut(BaseModel):
    id: str
    title: str
    description: str | None
    offer_type: str
    price_minor_units: int | None
    currency: str
    image_url: str | None
    status: str
    commission_model: str
    commission_config: dict


def _to_out(offer: Offer, campaign: Campaign) -> BusinessOfferOut:
    return BusinessOfferOut(
        id=str(offer.id),
        title=offer.title,
        description=offer.description,
        offer_type=offer.offer_type,
        price_minor_units=offer.price_minor_units,
        currency=offer.currency,
        image_url=(offer.branding or {}).get("image"),
        status=offer.status,
        commission_model=campaign.commission_model,
        commission_config=campaign.commission_config,
    )


@router.post("/offers/upload-image")
async def upload_offer_image(
    file: UploadFile = File(...),
    account: Account = Depends(require_business),
) -> dict:
    ext = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, or WEBP images are allowed",
        )

    contents = await file.read(MAX_IMAGE_BYTES + 1)
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image must be under 5MB")

    filename = f"{uuid.uuid4().hex}{ext}"
    (UPLOAD_DIR / filename).write_bytes(contents)

    return {"url": f"/uploads/offers/{filename}"}


@router.post("/offers", response_model=BusinessOfferOut, status_code=status.HTTP_201_CREATED)
def create_offer(
    payload: CreateOfferIn,
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> BusinessOfferOut:
    offer = Offer(
        id=uuid.uuid4(),
        business_id=account.id,
        offer_type=payload.offer_type,
        title=payload.title,
        description=payload.description,
        price_minor_units=payload.price_minor_units,
        currency=payload.currency,
        status="active",
        branding={"image": payload.image_url} if payload.image_url else {},
        destination_url=payload.destination_url,
    )
    db.add(offer)
    db.flush()

    campaign = Campaign(
        id=uuid.uuid4(),
        offer_id=offer.id,
        commission_model=payload.commission_model,
        commission_config=payload.commission_config,
        status="active",
    )
    db.add(campaign)
    db.commit()

    return _to_out(offer, campaign)


@router.get("/offers", response_model=list[BusinessOfferOut])
def list_business_offers(
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> list[BusinessOfferOut]:
    rows = db.execute(
        select(Offer, Campaign)
        .join(Campaign, Campaign.offer_id == Offer.id)
        .where(Offer.business_id == account.id)
        .order_by(Offer.created_at.desc())
    ).all()
    return [_to_out(offer, campaign) for offer, campaign in rows]


class CommissionOut(BaseModel):
    id: str
    offer_title: str
    promoter_name: str
    amount_minor_units: int
    currency: str
    status: str
    created_at: str


def _commission_query():
    return (
        select(Commission, Offer.title, Account.full_name)
        .join(Conversion, Conversion.id == Commission.conversion_id)
        .join(Campaign, Campaign.id == Conversion.campaign_id)
        .join(Offer, Offer.id == Campaign.offer_id)
        .join(Account, Account.id == Commission.promoter_id)
    )


def _commission_to_out(commission: Commission, offer_title: str, promoter_name: str) -> CommissionOut:
    return CommissionOut(
        id=str(commission.id),
        offer_title=offer_title,
        promoter_name=promoter_name,
        amount_minor_units=commission.amount_minor_units,
        currency=commission.currency,
        status=commission.status,
        created_at=commission.created_at.isoformat(),
    )


@router.get("/commissions", response_model=list[CommissionOut])
def list_business_commissions(
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> list[CommissionOut]:
    rows = db.execute(
        _commission_query().where(Offer.business_id == account.id).order_by(Commission.created_at.desc())
    ).all()
    return [_commission_to_out(c, title, name) for c, title, name in rows]


def _get_owned_commission(db: Session, account: Account, commission_id: str) -> Commission:
    try:
        cid = uuid.UUID(commission_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid commission id")

    row = db.execute(
        _commission_query().where(Commission.id == cid, Offer.business_id == account.id)
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commission not found")
    return row[0]


def _apply_transition(db: Session, account: Account, commission_id: str, new_status: str, reason: str) -> CommissionOut:
    commission = _get_owned_commission(db, account, commission_id)
    try:
        transition(db, commission, new_status, reason=reason)
    except IllegalTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    db.commit()

    row = db.execute(_commission_query().where(Commission.id == commission.id)).first()
    return _commission_to_out(*row)


@router.post("/commissions/{commission_id}/approve", response_model=CommissionOut)
def approve_commission(
    commission_id: str,
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> CommissionOut:
    return _apply_transition(db, account, commission_id, "approved", reason="business: manual approval")


@router.post("/commissions/{commission_id}/reject", response_model=CommissionOut)
def reject_commission(
    commission_id: str,
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> CommissionOut:
    return _apply_transition(db, account, commission_id, "rejected", reason="business: manual rejection")


@router.post("/commissions/{commission_id}/reverse", response_model=CommissionOut)
def reverse_commission(
    commission_id: str,
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> CommissionOut:
    return _apply_transition(db, account, commission_id, "reversed", reason="business: manual reversal")


class WebhookSecretOut(BaseModel):
    webhook_secret: str


@router.get("/webhook-secret", response_model=WebhookSecretOut)
def get_webhook_secret(
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> WebhookSecretOut:
    """Returns this business's webhook secret, generating one on first
    request. Used to authenticate POST /api/webhooks/conversions calls from
    their own checkout — see app/api/routes/webhooks.py."""
    if account.webhook_secret is None:
        account.webhook_secret = f"whsec_{secrets.token_urlsafe(32)}"
        db.commit()
    return WebhookSecretOut(webhook_secret=account.webhook_secret)


@router.post("/webhook-secret/rotate", response_model=WebhookSecretOut)
def rotate_webhook_secret(
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> WebhookSecretOut:
    """Invalidates the old secret immediately — anything still using it
    starts getting 401s until the checkout integration is updated."""
    account.webhook_secret = f"whsec_{secrets.token_urlsafe(32)}"
    db.commit()
    return WebhookSecretOut(webhook_secret=account.webhook_secret)


class FraudFlagOut(BaseModel):
    id: str
    commission_id: str
    offer_title: str
    promoter_name: str
    rule_triggered: str
    severity: str
    resolved: bool
    created_at: str


def _fraud_flag_query():
    # FraudFlag.subject_id always names a Commission here — every flag this
    # app writes today comes from app/services/fraud.py, which only ever
    # flags subject_type="commission" (see its docstring).
    return (
        select(FraudFlag, Commission.id, Offer.title, Account.full_name)
        .join(Commission, Commission.id == FraudFlag.subject_id)
        .join(Conversion, Conversion.id == Commission.conversion_id)
        .join(Campaign, Campaign.id == Conversion.campaign_id)
        .join(Offer, Offer.id == Campaign.offer_id)
        .join(Account, Account.id == Commission.promoter_id)
        .where(FraudFlag.subject_type == "commission")
    )


def _fraud_flag_to_out(flag: FraudFlag, commission_id: uuid.UUID, offer_title: str, promoter_name: str) -> FraudFlagOut:
    return FraudFlagOut(
        id=str(flag.id),
        commission_id=str(commission_id),
        offer_title=offer_title,
        promoter_name=promoter_name,
        rule_triggered=flag.rule_triggered,
        severity=flag.severity,
        resolved=flag.resolved,
        created_at=flag.created_at.isoformat(),
    )


@router.get("/fraud-flags", response_model=list[FraudFlagOut])
def list_fraud_flags(
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> list[FraudFlagOut]:
    rows = db.execute(
        _fraud_flag_query().where(Offer.business_id == account.id).order_by(FraudFlag.created_at.desc())
    ).all()
    return [_fraud_flag_to_out(*row) for row in rows]


@router.post("/fraud-flags/{flag_id}/resolve", response_model=FraudFlagOut)
def resolve_fraud_flag(
    flag_id: str,
    account: Account = Depends(require_business),
    db: Session = Depends(get_db),
) -> FraudFlagOut:
    try:
        fid = uuid.UUID(flag_id)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid flag id")

    row = db.execute(_fraud_flag_query().where(FraudFlag.id == fid, Offer.business_id == account.id)).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fraud flag not found")
    flag = row[0]
    flag.resolved = True
    db.commit()
    return _fraud_flag_to_out(*row)
