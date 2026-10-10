"""Small, deliberately un-abstracted builders for test fixtures — mirrors
exactly what a real request creates, at the ORM/SQL level, so tests exercise
the same shapes production code does. `clicks` has no ORM model (see
app/models/core.py's docstring on why) so make_click uses raw SQL, same as
app/api/routes/clicks.py itself does.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.core import Account, Campaign, Commission, Conversion, Offer, TrackingLink


def make_account(db: Session, *, role: str, suffix: str, **overrides) -> Account:
    now = datetime.now(timezone.utc)
    # Digits derived from role+suffix (not suffix alone) — two accounts
    # sharing a suffix (a business and a promoter built from the same
    # fixture, say) must still get different phone numbers.
    phone_digits = str(abs(hash(f"{role}-{suffix}")))[:9].ljust(9, "0")
    defaults = dict(
        id=uuid.uuid4(),
        role=role,
        email=f"{role}-{suffix}@example.com",
        phone=f"+1555{phone_digits}",
        country_code="NG",
        kyc_status="unverified",
        password_hash=hash_password("password123"),
        full_name=f"Test {role.title()} {suffix}",
        email_verified_at=now,
        phone_verified_at=now,
    )
    defaults.update(overrides)
    account = Account(**defaults)
    db.add(account)
    db.flush()
    return account


def make_offer_campaign(
    db: Session,
    *,
    business: Account,
    currency: str = "NGN",
    commission_model: str = "fixed",
    commission_config: dict | None = None,
    offer_overrides: dict | None = None,
    campaign_overrides: dict | None = None,
) -> tuple[Offer, Campaign]:
    offer_defaults = dict(
        id=uuid.uuid4(),
        business_id=business.id,
        offer_type="physical",
        title="Test Offer",
        description="A test offer",
        price_minor_units=500_00,
        currency=currency,
        status="active",
        branding={},
        destination_url="https://example.com/offer",
    )
    offer_defaults.update(offer_overrides or {})
    offer = Offer(**offer_defaults)
    db.add(offer)
    db.flush()

    campaign_defaults = dict(
        id=uuid.uuid4(),
        offer_id=offer.id,
        commission_model=commission_model,
        commission_config=commission_config or {"amount_minor_units": 50_00},
        status="active",
    )
    campaign_defaults.update(campaign_overrides or {})
    campaign = Campaign(**campaign_defaults)
    db.add(campaign)
    db.flush()
    return offer, campaign


def make_tracking_link(db: Session, *, campaign: Campaign, promoter: Account, short_code: str) -> TrackingLink:
    link = TrackingLink(id=uuid.uuid4(), campaign_id=campaign.id, promoter_id=promoter.id, short_code=short_code)
    db.add(link)
    db.flush()
    return link


def make_click(db: Session, *, tracking_link: TrackingLink, occurred_at: datetime | None = None) -> tuple[uuid.UUID, str, datetime]:
    """Returns (click_row_id, click_id_key, occurred_at) — click_row_id is
    what Conversion.click_id references (clicks.id), click_id_key is the
    cookie/redirect key a webhook caller would pass as `click_id` in its
    payload (clicks.click_id, a different column — see the schema note in
    app/models/core.py)."""
    click_row_id = uuid.uuid4()
    click_id_key = uuid.uuid4().hex
    when = occurred_at or datetime.now(timezone.utc)
    db.execute(
        text(
            "INSERT INTO clicks (id, tracking_link_id, click_id, occurred_at) "
            "VALUES (:id, :tracking_link_id, :click_id, :occurred_at)"
        ),
        {"id": str(click_row_id), "tracking_link_id": str(tracking_link.id), "click_id": click_id_key, "occurred_at": when},
    )
    return click_row_id, click_id_key, when


def make_conversion(
    db: Session,
    *,
    campaign: Campaign,
    click_row_id: uuid.UUID,
    click_occurred_at: datetime,
    value_minor_units: int = 500_00,
    external_ref: str | None = None,
    **overrides,
) -> Conversion:
    defaults = dict(
        id=uuid.uuid4(),
        click_id=click_row_id,
        click_occurred_at=click_occurred_at,
        campaign_id=campaign.id,
        conversion_value_minor_units=value_minor_units,
        external_ref=external_ref,
        status="approved",
    )
    defaults.update(overrides)
    conversion = Conversion(**defaults)
    db.add(conversion)
    db.flush()
    return conversion


def make_commission(
    db: Session, *, conversion: Conversion, promoter: Account, amount_minor_units: int = 50_00, status: str = "pending", **overrides
) -> Commission:
    defaults = dict(
        id=uuid.uuid4(),
        conversion_id=conversion.id,
        promoter_id=promoter.id,
        amount_minor_units=amount_minor_units,
        currency="NGN",
        status=status,
        status_history=[],
    )
    defaults.update(overrides)
    commission = Commission(**defaults)
    db.add(commission)
    db.flush()
    return commission
