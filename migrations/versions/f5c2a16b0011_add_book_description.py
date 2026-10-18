"""Add a creation-time book description.

Revision ID: f5c2a16b0011
Revises: e47a2c9d0010
"""
from alembic import op
import sqlalchemy as sa

revision = "f5c2a16b0011"
down_revision = "e47a2c9d0010"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("book") as batch:
        batch.add_column(sa.Column("description", sa.Text(), nullable=False, server_default=""))


def downgrade():
    with op.batch_alter_table("book") as batch:
        batch.drop_column("description")
