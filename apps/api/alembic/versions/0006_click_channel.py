"""Add clicks.channel — which share channel (whatsapp, facebook, ...) a
click came through, read from the `?ch=` query param on the redirect link.

Recorded per-click rather than on tracking_links: a promoter's tracking
link is now a single URL reused across every channel (see
tracking_links.py), so channel attribution has to travel with the click,
not live on the link itself.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-09

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE clicks ADD COLUMN channel TEXT;")


def downgrade() -> None:
    op.execute("ALTER TABLE clicks DROP COLUMN IF EXISTS channel;")
