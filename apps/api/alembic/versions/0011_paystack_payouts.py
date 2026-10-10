"""Wire payouts to a real payment rail (Paystack).

Adds payout_accounts — a promoter's saved payout destination, resolved
against Paystack's /bank/resolve and registered as a transfer recipient
before it's ever used (see app/services/paystack.py). One per promoter;
replacing it re-resolves and re-registers from scratch.

Adds payouts.paystack_reference / paystack_transfer_code / failure_reason —
null when Paystack isn't configured, in which case a payout behaves exactly
as before this migration: created, stuck at "requested" forever.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-13

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE payout_accounts (
            id UUID PRIMARY KEY,
            promoter_id UUID NOT NULL UNIQUE REFERENCES accounts(id),
            payout_method TEXT NOT NULL,
            bank_code TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            account_number TEXT NOT NULL,
            account_name TEXT NOT NULL,
            paystack_recipient_code TEXT NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )
    op.execute("ALTER TABLE payouts ADD COLUMN paystack_reference TEXT UNIQUE;")
    op.execute("ALTER TABLE payouts ADD COLUMN paystack_transfer_code TEXT;")
    op.execute("ALTER TABLE payouts ADD COLUMN failure_reason TEXT;")


def downgrade() -> None:
    op.execute("ALTER TABLE payouts DROP COLUMN IF EXISTS failure_reason;")
    op.execute("ALTER TABLE payouts DROP COLUMN IF EXISTS paystack_transfer_code;")
    op.execute("ALTER TABLE payouts DROP COLUMN IF EXISTS paystack_reference;")
    op.execute("DROP TABLE IF EXISTS payout_accounts;")
