"""Make accounts.phone required — email and phone must both be present and
unique for every account (phone was already unique per 0003, but nullable,
so "compulsory" wasn't actually enforced at the schema level).

Backfills the two known seed/demo accounts (the only pre-existing rows with
a null phone at the time this was written) before adding the constraint.
Any other null-phone row makes this migration fail loudly rather than
silently assigning a real account a fake number — that row needs a real
phone number attached by hand first.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-10

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE accounts SET phone = '+2348010000001'
        WHERE email = 'demo.promoter@nexshare.app' AND phone IS NULL;
        """
    )
    op.execute(
        """
        UPDATE accounts SET phone = '+2348010000002'
        WHERE email = 'demo.business@nexshare.app' AND phone IS NULL;
        """
    )
    op.execute("ALTER TABLE accounts ALTER COLUMN phone SET NOT NULL;")


def downgrade() -> None:
    op.execute("ALTER TABLE accounts ALTER COLUMN phone DROP NOT NULL;")
