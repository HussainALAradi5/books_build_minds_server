"""Harden uniqueness and required account fields.

Revision ID: c8ad12e960b0
Revises: b47f19d54a13
"""
from alembic import op
import sqlalchemy as sa

revision = "c8ad12e960b0"
down_revision = "b47f19d54a13"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("purchased_books") as batch:
        batch.alter_column("user_id", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("book_id", existing_type=sa.Integer(), nullable=False)
    with op.batch_alter_table("receipt") as batch:
        batch.create_unique_constraint("uq_receipt_user_book", ["user_id", "book_id"])
    with op.batch_alter_table("review") as batch:
        batch.create_unique_constraint("uq_review_user_book", ["user_id", "book_id"])
    with op.batch_alter_table("user") as batch:
        batch.alter_column("is_admin", existing_type=sa.Boolean(), nullable=False)
        batch.alter_column("is_active", existing_type=sa.Boolean(), nullable=False)


def downgrade():
    with op.batch_alter_table("user") as batch:
        batch.alter_column("is_admin", existing_type=sa.Boolean(), nullable=True)
        batch.alter_column("is_active", existing_type=sa.Boolean(), nullable=True)
    with op.batch_alter_table("review") as batch:
        batch.drop_constraint("uq_review_user_book", type_="unique")
    with op.batch_alter_table("receipt") as batch:
        batch.drop_constraint("uq_receipt_user_book", type_="unique")
    with op.batch_alter_table("purchased_books") as batch:
        batch.alter_column("book_id", existing_type=sa.Integer(), nullable=True)
        batch.alter_column("user_id", existing_type=sa.Integer(), nullable=True)
