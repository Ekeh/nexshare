"""Make accounts.phone unique — registration now collects phone, and it
must be unique like email (Postgres allows multiple NULLs under a unique
constraint, so existing null-phone rows are unaffected).

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE accounts ADD CONSTRAINT accounts_phone_key UNIQUE (phone);")


def downgrade() -> None:
    op.execute("ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_phone_key;")
