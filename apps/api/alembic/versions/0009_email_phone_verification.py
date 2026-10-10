"""Email + phone verification.

Adds accounts.email_verified_at / phone_verified_at (both null =
unverified). The verification codes themselves live in Redis with a TTL
(app/services/verification.py), not Postgres — they're short-lived,
write-once secrets with no reporting/audit value once consumed or expired,
which is exactly what Redis's expiry is for, and it avoids a table whose
only purpose is being deleted from a few minutes after every insert.

Existing accounts are grandfathered as verified as of this migration — they
were created before this requirement existed, so there's no code to have
sent them, and locking out already-issued demo/test credentials would just
break the app for anyone already using it.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-10

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE accounts ADD COLUMN email_verified_at TIMESTAMPTZ;")
    op.execute("ALTER TABLE accounts ADD COLUMN phone_verified_at TIMESTAMPTZ;")
    op.execute(
        "UPDATE accounts SET email_verified_at = created_at, phone_verified_at = created_at;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE accounts DROP COLUMN IF EXISTS phone_verified_at;")
    op.execute("ALTER TABLE accounts DROP COLUMN IF EXISTS email_verified_at;")
