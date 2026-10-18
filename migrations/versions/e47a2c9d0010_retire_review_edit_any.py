"""Retire the obsolete permission to edit another user's review.

Revision ID: e47a2c9d0010
Revises: d0a2e93c0009
"""
from alembic import op
import sqlalchemy as sa

revision = "e47a2c9d0010"
down_revision = "d0a2e93c0009"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(sa.text(
        "UPDATE access_permission SET is_deleted = true WHERE key = 'review:edit.any'"
    ))


def downgrade():
    op.get_bind().execute(sa.text(
        "UPDATE access_permission SET is_deleted = false WHERE key = 'review:edit.any'"
    ))
