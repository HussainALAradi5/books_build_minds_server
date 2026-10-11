"""Add lifecycle flags to all persisted library entities.

Revision ID: 5a24f7c7e001
Revises: 3d636ddd36b6
"""
from alembic import op
import sqlalchemy as sa

revision = "5a24f7c7e001"
down_revision = "3d636ddd36b6"
branch_labels = None
depends_on = None

TABLES = ("user", "book", "review", "receipt", "admin_request", "media", "loan", "library_activity")


def upgrade():
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()))
            batch.add_column(sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    for table in reversed(TABLES):
        with op.batch_alter_table(table) as batch:
            batch.drop_column("is_deleted")
            batch.drop_column("is_archived")
