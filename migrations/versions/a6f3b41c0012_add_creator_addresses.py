"""Add optional author and publisher addresses.

Revision ID: a6f3b41c0012
Revises: c6d4e27a0012
"""
from alembic import op
import sqlalchemy as sa

revision = "a6f3b41c0012"
down_revision = "c6d4e27a0012"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("author", "publisher"):
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("address", sa.String(length=500), nullable=False, server_default=""))


def downgrade():
    for table in ("author", "publisher"):
        with op.batch_alter_table(table) as batch:
            batch.drop_column("address")
