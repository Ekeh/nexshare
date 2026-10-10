"""Add auth fields to accounts — password_hash, full_name

Needed for promoter login/session auth and dashboard display ("Welcome
back, {full_name}!"), per SKILL.md step 4. Not in architecture.md's
original DDL sketch, which predates the auth build-out.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-07

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE accounts ADD COLUMN password_hash TEXT NOT NULL DEFAULT '';")
    op.execute("ALTER TABLE accounts ALTER COLUMN password_hash DROP DEFAULT;")
    op.execute("ALTER TABLE accounts ADD COLUMN full_name TEXT NOT NULL DEFAULT '';")


def downgrade() -> None:
    op.execute("ALTER TABLE accounts DROP COLUMN IF EXISTS full_name;")
    op.execute("ALTER TABLE accounts DROP COLUMN IF EXISTS password_hash;")
