"""Conversion-reporting webhook.

Adds accounts.webhook_secret — a per-business static credential for
server-to-server calls to POST /api/webhooks/conversions (their checkout
reporting a completed sale/lead back to us), authenticated separately from
the cookie/JWT session flow every other endpoint uses.

Adds conversions.external_ref — the business's own order/transaction id,
so a retried webhook call (any real webhook sender retries on timeout/5xx)
doesn't record the same sale twice. Unique per campaign when present;
Postgres allows repeated NULLs under a unique constraint, so callers who
omit it aren't blocked — they just don't get idempotency.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-10

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE accounts ADD COLUMN webhook_secret TEXT UNIQUE;")
    op.execute("ALTER TABLE conversions ADD COLUMN external_ref TEXT;")
    op.execute(
        "ALTER TABLE conversions ADD CONSTRAINT conversions_campaign_external_ref_key "
        "UNIQUE (campaign_id, external_ref);"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE conversions DROP CONSTRAINT IF EXISTS conversions_campaign_external_ref_key;"
    )
    op.execute("ALTER TABLE conversions DROP COLUMN IF EXISTS external_ref;")
    op.execute("ALTER TABLE accounts DROP COLUMN IF EXISTS webhook_secret;")
