"""Add independent book comments and star ratings.

Revision ID: 6b35f8d8e002
Revises: 5a24f7c7e001
"""
from alembic import op
import sqlalchemy as sa

revision = "6b35f8d8e002"
down_revision = "5a24f7c7e001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "book_comment",
        sa.Column("comment_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("book.book_id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_book_comment_book_id", "book_comment", ["book_id"])
    op.create_index("ix_book_comment_user_id", "book_comment", ["user_id"])
    op.create_table(
        "book_star",
        sa.Column("star_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("book.book_id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("book_id", "user_id", name="uq_book_star_book_user"),
    )
    op.create_index("ix_book_star_book_id", "book_star", ["book_id"])
    op.create_index("ix_book_star_user_id", "book_star", ["user_id"])
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO book_comment (book_id, user_id, body, created_at, edited_at, is_archived, is_deleted)
        SELECT book_id, user_id, comment, written_time, last_edit, is_archived, is_deleted FROM review
    """))
    connection.execute(sa.text("""
        INSERT INTO book_star (book_id, user_id, rating, created_at, updated_at, is_archived, is_deleted)
        SELECT book_id, user_id, CAST(ROUND(rating) AS INTEGER), written_time, last_edit, is_archived, is_deleted FROM review
    """))


def downgrade():
    op.drop_index("ix_book_star_user_id", table_name="book_star")
    op.drop_index("ix_book_star_book_id", table_name="book_star")
    op.drop_table("book_star")
    op.drop_index("ix_book_comment_user_id", table_name="book_comment")
    op.drop_index("ix_book_comment_book_id", table_name="book_comment")
    op.drop_table("book_comment")
