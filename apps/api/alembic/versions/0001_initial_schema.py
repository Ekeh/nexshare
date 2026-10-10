"""Initial schema — accounts, offers, campaigns, tracking, ledger

Matches nexshare-skill/references/architecture.md §3.

Revision ID: 0001
Revises:
Create Date: 2026-09-06

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.execute(
        """
        CREATE TABLE accounts (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          role TEXT NOT NULL CHECK (role IN ('business','promoter','customer','admin')),
          email TEXT UNIQUE NOT NULL,
          phone TEXT,
          country_code CHAR(2) NOT NULL,
          kyc_status TEXT NOT NULL DEFAULT 'unverified',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    op.execute(
        """
        CREATE TABLE offers (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          business_id UUID NOT NULL REFERENCES accounts(id),
          offer_type TEXT NOT NULL,
          title TEXT NOT NULL,
          description TEXT,
          price_minor_units BIGINT,
          currency CHAR(3) NOT NULL,
          status TEXT NOT NULL DEFAULT 'draft',
          branding JSONB,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    op.execute(
        """
        CREATE TABLE campaigns (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          offer_id UUID NOT NULL REFERENCES offers(id),
          commission_model TEXT NOT NULL,
          commission_config JSONB NOT NULL,
          budget_minor_units BIGINT,
          max_conversions INT,
          conversions_count INT NOT NULL DEFAULT 0,
          geo_restriction JSONB,
          eligible_promoter_rule JSONB,
          starts_at TIMESTAMPTZ,
          ends_at TIMESTAMPTZ,
          status TEXT NOT NULL DEFAULT 'active',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    op.execute(
        """
        CREATE TABLE tracking_links (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          campaign_id UUID NOT NULL REFERENCES campaigns(id),
          promoter_id UUID NOT NULL REFERENCES accounts(id),
          short_code TEXT UNIQUE NOT NULL,
          channel TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    # NOTE: architecture.md's sketch gives `clicks.id` a standalone PRIMARY
    # KEY, but Postgres requires a partitioned table's unique/primary key to
    # include the partition column. Composite PK (id, occurred_at) preserves
    # `id` as the row identity while satisfying that constraint. A DEFAULT
    # partition is created so inserts work immediately; roll in monthly
    # range partitions (and detach/archive old ones) as click volume grows.
    op.execute(
        """
        CREATE TABLE clicks (
          id UUID NOT NULL DEFAULT gen_random_uuid(),
          tracking_link_id UUID NOT NULL REFERENCES tracking_links(id),
          click_id TEXT NOT NULL,
          ip_hash TEXT,
          device_fingerprint TEXT,
          user_agent TEXT,
          occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          PRIMARY KEY (id, occurred_at),
          UNIQUE (click_id, occurred_at)
        ) PARTITION BY RANGE (occurred_at);
        """
    )
    op.execute("CREATE TABLE clicks_default PARTITION OF clicks DEFAULT;")

    op.execute(
        """
        CREATE TABLE conversions (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          click_id UUID NOT NULL,
          click_occurred_at TIMESTAMPTZ NOT NULL,
          campaign_id UUID NOT NULL REFERENCES campaigns(id),
          customer_id UUID REFERENCES accounts(id),
          conversion_value_minor_units BIGINT,
          status TEXT NOT NULL DEFAULT 'pending_validation',
          occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          FOREIGN KEY (click_id, click_occurred_at) REFERENCES clicks(id, occurred_at)
        );
        """
    )

    op.execute(
        """
        CREATE TABLE commissions (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          conversion_id UUID NOT NULL REFERENCES conversions(id),
          promoter_id UUID NOT NULL REFERENCES accounts(id),
          amount_minor_units BIGINT NOT NULL,
          currency CHAR(3) NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          status_history JSONB NOT NULL DEFAULT '[]',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    op.execute(
        """
        CREATE TABLE ledger_entries (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          account_id UUID NOT NULL REFERENCES accounts(id),
          commission_id UUID REFERENCES commissions(id),
          payout_id UUID,
          entry_type TEXT NOT NULL,
          amount_minor_units BIGINT NOT NULL,
          currency CHAR(3) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    op.execute(
        """
        CREATE TABLE payouts (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          promoter_id UUID NOT NULL REFERENCES accounts(id),
          amount_minor_units BIGINT NOT NULL,
          currency CHAR(3) NOT NULL,
          payout_method TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'requested',
          requested_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    op.execute(
        """
        ALTER TABLE ledger_entries
          ADD CONSTRAINT ledger_entries_payout_id_fkey
          FOREIGN KEY (payout_id) REFERENCES payouts(id);
        """
    )

    op.execute(
        """
        CREATE TABLE fraud_flags (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          subject_type TEXT NOT NULL,
          subject_id UUID NOT NULL,
          rule_triggered TEXT NOT NULL,
          severity TEXT NOT NULL,
          resolved BOOLEAN NOT NULL DEFAULT false,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        """
    )

    # Helpful indexes for the access patterns the dashboards will need.
    op.execute("CREATE INDEX ix_offers_business_id ON offers(business_id);")
    op.execute("CREATE INDEX ix_campaigns_offer_id ON campaigns(offer_id);")
    op.execute(
        "CREATE INDEX ix_tracking_links_promoter_id ON tracking_links(promoter_id);"
    )
    op.execute(
        "CREATE INDEX ix_conversions_campaign_id ON conversions(campaign_id);"
    )
    op.execute(
        "CREATE INDEX ix_commissions_promoter_id ON commissions(promoter_id);"
    )
    op.execute(
        "CREATE INDEX ix_ledger_entries_account_id ON ledger_entries(account_id);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fraud_flags;")
    op.execute("ALTER TABLE ledger_entries DROP CONSTRAINT IF EXISTS ledger_entries_payout_id_fkey;")
    op.execute("DROP TABLE IF EXISTS payouts;")
    op.execute("DROP TABLE IF EXISTS ledger_entries;")
    op.execute("DROP TABLE IF EXISTS commissions;")
    op.execute("DROP TABLE IF EXISTS conversions;")
    op.execute("DROP TABLE IF EXISTS clicks_default;")
    op.execute("DROP TABLE IF EXISTS clicks;")
    op.execute("DROP TABLE IF EXISTS tracking_links;")
    op.execute("DROP TABLE IF EXISTS campaigns;")
    op.execute("DROP TABLE IF EXISTS offers;")
    op.execute("DROP TABLE IF EXISTS accounts;")
