"""Add offers.destination_url — the business URL a tracking link's click
redirect (`GET /api/clicks/{short_code}`) sends customers to. Nullable: a
draft offer may not have a landing page picked yet.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-09

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE offers ADD COLUMN destination_url TEXT;")


def downgrade() -> None:
    op.execute("ALTER TABLE offers DROP COLUMN IF EXISTS destination_url;")
