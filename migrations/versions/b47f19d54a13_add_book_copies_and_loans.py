"""Add book inventory and borrowing records.

Revision ID: b47f19d54a13
Revises: 4280997db745
"""
from alembic import op
import sqlalchemy as sa

revision = "b47f19d54a13"
down_revision = "4280997db745"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("book") as batch:
        batch.add_column(sa.Column("copies_total", sa.Integer(), nullable=False, server_default="1"))
        batch.alter_column("slug", existing_type=sa.String(), nullable=False)
    op.create_table(
        "loan",
        sa.Column("loan_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("book.book_id"), nullable=False),
        sa.Column("borrowed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_loan_user_id", "loan", ["user_id"])
    op.create_index("ix_loan_book_id", "loan", ["book_id"])


def downgrade():
    op.drop_index("ix_loan_book_id", table_name="loan")
    op.drop_index("ix_loan_user_id", table_name="loan")
    op.drop_table("loan")
    with op.batch_alter_table("book") as batch:
        batch.alter_column("slug", existing_type=sa.String(), nullable=True)
        batch.drop_column("copies_total")
