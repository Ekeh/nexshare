"""SQLAlchemy models mirroring the DDL in alembic/versions/0001_initial_schema.py
and 0002_add_auth_fields.py. Hand-maintained (alembic env.py runs with
target_metadata=None), so a schema change here must be paired with a migration.
"""
from __future__ import annotations

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint(
            "role IN ('business','promoter','customer','admin')", name="accounts_role_check"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    kyc_status: Mapped[str] = mapped_column(Text, nullable=False, default="unverified")
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    email_verified_at: Mapped["object | None"] = mapped_column(DateTime(timezone=True))
    phone_verified_at: Mapped["object | None"] = mapped_column(DateTime(timezone=True))
    webhook_secret: Mapped[str | None] = mapped_column(Text, unique=True)
    created_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    offer_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_minor_units: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="draft")
    branding: Mapped[dict | None] = mapped_column(JSON)
    destination_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("offers.id"), nullable=False)
    commission_model: Mapped[str] = mapped_column(Text, nullable=False)
    commission_config: Mapped[dict] = mapped_column(JSON, nullable=False)
    budget_minor_units: Mapped[int | None] = mapped_column(BigInteger)
    max_conversions: Mapped[int | None] = mapped_column(Integer)
    conversions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    geo_restriction: Mapped[dict | None] = mapped_column(JSON)
    eligible_promoter_rule: Mapped[dict | None] = mapped_column(JSON)
    starts_at: Mapped["object | None"] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped["object | None"] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    hold_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    created_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    offer: Mapped[Offer] = relationship()


class TrackingLink(Base):
    __tablename__ = "tracking_links"
    __table_args__ = (
        UniqueConstraint("promoter_id", "campaign_id", name="tracking_links_promoter_campaign_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    promoter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    short_code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    channel: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Conversion(Base):
    __tablename__ = "conversions"
    __table_args__ = (
        UniqueConstraint("campaign_id", "external_ref", name="conversions_campaign_external_ref_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    click_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    click_occurred_at: Mapped["object"] = mapped_column(DateTime(timezone=True), nullable=False)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    conversion_value_minor_units: Mapped[int | None] = mapped_column(BigInteger)
    external_ref: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending_validation")
    occurred_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Commission(Base):
    __tablename__ = "commissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversions.id"), nullable=False)
    promoter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    amount_minor_units: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    status_history: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    commission_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("commissions.id"))
    payout_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("payouts.id"))
    entry_type: Mapped[str] = mapped_column(Text, nullable=False)
    amount_minor_units: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promoter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    amount_minor_units: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    payout_method: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="requested")
    requested_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Paystack integration (app/services/paystack.py) — null when Paystack
    # isn't configured (PAYSTACK_SECRET_KEY unset), in which case a payout
    # behaves exactly as before: created, stays "requested" forever.
    paystack_reference: Mapped[str | None] = mapped_column(Text, unique=True)
    paystack_transfer_code: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)


class PayoutAccount(Base):
    """A promoter's saved payout destination — one per promoter, resolved
    and registered as a Paystack transfer recipient before it can be used
    (see app/services/paystack.py). Replacing it re-resolves and
    re-registers from scratch rather than editing in place, so a stale
    recipient_code can never silently linger."""

    __tablename__ = "payout_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promoter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, unique=True
    )
    payout_method: Mapped[str] = mapped_column(Text, nullable=False)
    bank_code: Mapped[str] = mapped_column(Text, nullable=False)
    bank_name: Mapped[str] = mapped_column(Text, nullable=False)
    account_number: Mapped[str] = mapped_column(Text, nullable=False)
    account_name: Mapped[str] = mapped_column(Text, nullable=False)
    paystack_recipient_code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_type: Mapped[str] = mapped_column(Text, nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    rule_triggered: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped["object"] = mapped_column(DateTime(timezone=True), server_default=func.now())
