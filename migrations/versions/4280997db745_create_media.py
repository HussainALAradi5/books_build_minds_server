"""Create typed media storage metadata.

Revision ID: 4280997db745
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "4280997db745"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "media",
        sa.Column("media_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("book.book_id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=True),
        sa.Column("media_type", sa.String(32), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False, unique=True),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_media_book_id", "media", ["book_id"])
    op.create_index("ix_media_user_id", "media", ["user_id"])


def downgrade():
    op.drop_index("ix_media_user_id", table_name="media")
    op.drop_index("ix_media_book_id", table_name="media")
    op.drop_table("media")
