"""Seed a demo promoter (+ a business/offer/campaign/commissions to back the
dashboard stats) for local development.

Run from apps/api with the venv active:
    python -m app.scripts.seed_demo

Demo login: demo.promoter@nexshare.app / password123
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.core import Account, Campaign, Commission, LedgerEntry, Offer

DEMO_PROMOTER_EMAIL = "demo.promoter@nexshare.app"
DEMO_PROMOTER_PHONE = "+2348010000001"
DEMO_PROMOTER_PASSWORD = "password123"
DEMO_BUSINESS_EMAIL = "demo.business@nexshare.app"
DEMO_BUSINESS_PHONE = "+2348010000002"


def get_or_create_account(db, *, email: str, phone: str, role: str, full_name: str, password: str) -> Account:
    account = db.query(Account).filter(Account.email == email).one_or_none()
    if account:
        return account
    account = Account(
        id=uuid.uuid4(),
        role=role,
        email=email,
        phone=phone,
        country_code="NG",
        kyc_status="verified",
        password_hash=hash_password(password),
        full_name=full_name,
    )
    db.add(account)
    db.flush()
    return account


def get_or_create_offer(
    db,
    *,
    business_id,
    title: str,
    offer_type: str,
    price_minor_units: int | None,
    description: str | None = None,
    image: str | None = None,
    destination_url: str | None = None,
) -> Offer:
    offer = db.query(Offer).filter(Offer.business_id == business_id, Offer.title == title).one_or_none()
    if offer:
        return offer
    branding = {"cta": "Shop Now"}
    if image:
        branding["image"] = image
    offer = Offer(
        id=uuid.uuid4(),
        business_id=business_id,
        offer_type=offer_type,
        title=title,
        description=description or f"{title} — demo seed offer",
        price_minor_units=price_minor_units,
        currency="USD",
        status="active",
        branding=branding,
        # example.com is IANA-reserved for docs/placeholders (RFC 2606) — it
        # deliberately never resolves to a real site, which is exactly right
        # for a demo business that has no real storefront.
        destination_url=destination_url or "https://shop.example.com",
    )
    db.add(offer)
    db.flush()
    return offer


def get_or_create_campaign(
    db,
    *,
    offer_id,
    commission_model: str = "percentage",
    commission_config: dict | None = None,
) -> Campaign:
    campaign = db.query(Campaign).filter(Campaign.offer_id == offer_id).one_or_none()
    if campaign:
        return campaign
    campaign = Campaign(
        id=uuid.uuid4(),
        offer_id=offer_id,
        commission_model=commission_model,
        commission_config=commission_config or {"pct": 10},
        budget_minor_units=100_000_00,
        max_conversions=1000,
        status="active",
    )
    db.add(campaign)
    db.flush()
    return campaign


def seed_commission(db, *, promoter_id, campaign_id, amount_minor_units: int, when: datetime, status: str) -> None:
    """Insert a conversion + commission + (if past pending) ledger entry, backdated to `when`."""
    from app.models.core import Conversion
    from sqlalchemy import text

    click_id = uuid.uuid4()
    conversion_id = uuid.uuid4()

    # clicks needs a tracking_link row; reuse/create one short code per campaign+promoter.
    tracking_link_id = db.execute(
        text(
            "SELECT id FROM tracking_links WHERE promoter_id = :promoter_id AND campaign_id = :campaign_id LIMIT 1"
        ),
        {"promoter_id": str(promoter_id), "campaign_id": str(campaign_id)},
    ).scalar()
    if tracking_link_id is None:
        tracking_link_id = uuid.uuid4()
        db.execute(
            text(
                """
                INSERT INTO tracking_links (id, campaign_id, promoter_id, short_code, channel)
                VALUES (:id, :campaign_id, :promoter_id, :short_code, 'direct')
                """
            ),
            {
                "id": str(tracking_link_id),
                "campaign_id": str(campaign_id),
                "promoter_id": str(promoter_id),
                "short_code": uuid.uuid4().hex[:10],
            },
        )

    db.execute(
        text(
            """
            INSERT INTO clicks (id, tracking_link_id, click_id, occurred_at)
            VALUES (:id, :tracking_link_id, :click_id, :occurred_at)
            """
        ),
        {
            "id": str(click_id),
            "tracking_link_id": str(tracking_link_id),
            "click_id": uuid.uuid4().hex,
            "occurred_at": when,
        },
    )

    conversion = Conversion(
        id=conversion_id,
        click_id=click_id,
        click_occurred_at=when,
        campaign_id=campaign_id,
        conversion_value_minor_units=amount_minor_units * 10,
        status="approved",
        occurred_at=when,
    )
    db.add(conversion)
    db.flush()

    commission = Commission(
        id=uuid.uuid4(),
        conversion_id=conversion.id,
        promoter_id=promoter_id,
        amount_minor_units=amount_minor_units,
        currency="USD",
        status=status,
        status_history=[{"status": status, "at": when.isoformat()}],
        created_at=when,
    )
    db.add(commission)
    db.flush()

    if status in ("available", "paid"):
        db.add(
            LedgerEntry(
                id=uuid.uuid4(),
                account_id=promoter_id,
                commission_id=commission.id,
                entry_type="commission_earned",
                amount_minor_units=amount_minor_units,
                currency="USD",
                created_at=when,
            )
        )


def main() -> None:
    db = SessionLocal()
    try:
        promoter = get_or_create_account(
            db,
            email=DEMO_PROMOTER_EMAIL,
            phone=DEMO_PROMOTER_PHONE,
            role="promoter",
            full_name="Sarah Adeyemi",
            password=DEMO_PROMOTER_PASSWORD,
        )
        business = get_or_create_account(
            db,
            email=DEMO_BUSINESS_EMAIL,
            phone=DEMO_BUSINESS_PHONE,
            role="business",
            full_name="Sunset Resorts",
            password="password123",
        )
        offer = get_or_create_offer(
            db,
            business_id=business.id,
            title="Weekend Getaway — 3 Nights",
            offer_type="booking",
            price_minor_units=29900,
            description="Enjoy a relaxing 3-night stay at our beachfront resort.",
            image="/images/offers/weekend-getaway.jpg",
            destination_url="https://sunsetresorts.example.com/weekend-getaway",
        )
        campaign = get_or_create_campaign(db, offer_id=offer.id, commission_model="percentage", commission_config={"pct": 10})
        db.commit()

        # A few more active offers across categories, purely so the "Find
        # Offers" page has more than one card/category to browse and filter.
        # No commission history is seeded against these.
        other_offers = [
            dict(
                title="Wireless Earbuds Pro",
                offer_type="physical",
                price_minor_units=8900,
                description="Noise-cancelling wireless earbuds with 30-hour battery life.",
                image="/images/offers/wireless-earbuds-pro.jpg",
                destination_url="https://gearmarket.example.com/wireless-earbuds-pro",
                commission_model="fixed",
                commission_config={"amount_minor_units": 1200},
            ),
            dict(
                title="Online Design Masterclass",
                offer_type="digital",
                price_minor_units=4900,
                description="Self-paced UI/UX design course with certificate.",
                image="/images/offers/online-design-masterclass.jpg",
                destination_url="https://learnhub.example.com/design-masterclass",
                commission_model="percentage",
                commission_config={"pct": 20},
            ),
            dict(
                title="MBA Program — Global",
                offer_type="education",
                price_minor_units=5000,
                description="Accredited part-time MBA with global cohort intake.",
                image="/images/offers/mba-program-global.jpg",
                destination_url="https://globalmba.example.com/apply",
                commission_model="qualified_lead",
                commission_config={"amount_minor_units": 10000},
            ),
        ]
        for spec in other_offers:
            o = get_or_create_offer(
                db,
                business_id=business.id,
                title=spec["title"],
                offer_type=spec["offer_type"],
                price_minor_units=spec["price_minor_units"],
                description=spec["description"],
                image=spec["image"],
                destination_url=spec["destination_url"],
            )
            get_or_create_campaign(
                db,
                offer_id=o.id,
                commission_model=spec["commission_model"],
                commission_config=spec["commission_config"],
            )
        db.commit()

        existing_commissions = db.query(Commission).filter(Commission.promoter_id == promoter.id).count()
        if existing_commissions == 0:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            month_start = today_start.replace(day=1)

            # Earlier months (lifetime total, not in this month/today).
            for i in range(6):
                seed_commission(
                    db,
                    promoter_id=promoter.id,
                    campaign_id=campaign.id,
                    amount_minor_units=45000 + i * 5000,
                    when=month_start - timedelta(days=30 * (i + 1)),
                    status="paid",
                )
            # Earlier this month (but before today), already available.
            for i in range(4):
                when = max(month_start + timedelta(hours=1), now - timedelta(days=1 + i))
                seed_commission(
                    db,
                    promoter_id=promoter.id,
                    campaign_id=campaign.id,
                    amount_minor_units=52000 + i * 3000,
                    when=when,
                    status="available",
                )
            # Today, already available (counts in today + month + total).
            seed_commission(
                db,
                promoter_id=promoter.id,
                campaign_id=campaign.id,
                amount_minor_units=4850,
                when=now - timedelta(hours=2),
                status="available",
            )
            # Still pending (counts only in "pending", not in earnings).
            seed_commission(
                db,
                promoter_id=promoter.id,
                campaign_id=campaign.id,
                amount_minor_units=112050,
                when=now - timedelta(hours=5),
                status="pending",
            )
            db.commit()
            print("Seeded demo commissions/ledger entries.")
        else:
            print("Demo promoter already has commissions — skipped seeding financial data.")

        print(f"Demo promoter login: {DEMO_PROMOTER_EMAIL} / {DEMO_PROMOTER_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
