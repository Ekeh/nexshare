"""Add campaigns.hold_period_days — the number of days a commission sits in
'approved' before it moves to 'available' (withdrawable), giving late
disputes/refunds a window to surface first. Referenced in
nexshare-skill/references/architecture.md §4 ("a hold period (configurable
per campaign, e.g. 3-7 days)") but never given a concrete column.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-10

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE campaigns ADD COLUMN hold_period_days INT NOT NULL DEFAULT 3;"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE campaigns DROP COLUMN IF EXISTS hold_period_days;")
