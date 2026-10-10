"""Enforce one tracking_link per (promoter, campaign) at the DB level.

The API's create-tracking-link endpoint used to do a plain
check-then-insert, which is racy under concurrent requests (e.g. React
Strict Mode double-firing an effect in dev, or a user double-clicking
"Promote") — two requests can both see "no existing link" and both insert,
producing duplicates. This constraint makes that impossible, and the route
now does insert-then-catch-conflict instead of select-then-insert.

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-09

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dedupe any rows already created under the old racy behavior, keeping
    # the earliest tracking link per (promoter, campaign).
    op.execute(
        """
        DELETE FROM tracking_links a USING tracking_links b
        WHERE a.promoter_id = b.promoter_id
          AND a.campaign_id = b.campaign_id
          AND a.created_at > b.created_at;
        """
    )
    op.execute(
        """
        ALTER TABLE tracking_links
          ADD CONSTRAINT tracking_links_promoter_campaign_key
          UNIQUE (promoter_id, campaign_id);
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE tracking_links DROP CONSTRAINT IF EXISTS tracking_links_promoter_campaign_key;"
    )
