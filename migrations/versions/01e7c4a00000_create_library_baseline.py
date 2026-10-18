"""Create the original library tables required by later migrations.

Revision ID: 01e7c4a00000
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "01e7c4a00000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("user_id", sa.Integer(), primary_key=True),
        sa.Column("user_name", sa.String(80), nullable=False, unique=True),
        sa.Column("password_digest", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "book",
        sa.Column("book_id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(255), nullable=True, unique=True),
        sa.Column("isbn", sa.String(32), nullable=False, unique=True),
        sa.Column("book_image", sa.String(500)),
        sa.Column("title", sa.String(255), nullable=False, unique=True),
        sa.Column("author", sa.String(255), nullable=False),
        sa.Column("publisher", sa.String(255), nullable=False),
        sa.Column("published_at", sa.Date(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("added_by_user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
    )
    op.create_table(
        "purchased_books",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), primary_key=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("book.book_id"), primary_key=True),
    )
    op.create_table(
        "receipt",
        sa.Column("receipt_id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("book.book_id"), nullable=False),
        sa.Column("written_time", sa.Date(), nullable=False),
    )
    op.create_table(
        "review",
        sa.Column("review_id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("book.book_id"), nullable=False),
        sa.Column("written_time", sa.Date(), nullable=False),
        sa.Column("last_edit", sa.Date()),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
    )
    op.create_table(
        "admin_request",
        sa.Column("request_id", sa.Integer(), primary_key=True),
        sa.Column("is_accepted", sa.Boolean()),
        sa.Column("review_time", sa.Date()),
        sa.Column("reviewed_by_user_id", sa.Integer(), sa.ForeignKey("user.user_id")),
        sa.Column("reason_for_request", sa.Text(), nullable=False),
        sa.Column("requester_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
    )


def downgrade():
    for table in ("admin_request", "review", "receipt", "purchased_books", "book", "user"):
        op.drop_table(table)
