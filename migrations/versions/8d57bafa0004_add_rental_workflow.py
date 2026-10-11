"""Track whether a loan is borrowed or rented.

Revision ID: 8d57bafa0004
Revises: 7c46a9e9f003
"""
from alembic import op
import sqlalchemy as sa

revision = "8d57bafa0004"
down_revision = "7c46a9e9f003"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("loan") as batch:
        batch.add_column(sa.Column("loan_kind", sa.String(16), nullable=False, server_default="borrow"))
        batch.add_column(sa.Column("rental_fee", sa.Float(), nullable=False, server_default="0"))


def downgrade():
    with op.batch_alter_table("loan") as batch:
        batch.drop_column("rental_fee")
        batch.drop_column("loan_kind")
