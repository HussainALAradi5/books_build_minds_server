"""Add many-to-many book categories and classify existing books.

Revision ID: b7c8d9e00013
Revises: a6f3b41c0012
"""
from alembic import op
import sqlalchemy as sa

revision = "b7c8d9e00013"
down_revision = "a6f3b41c0012"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "category",
        sa.Column("category_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("created_by", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.Integer()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "book_categories",
        sa.Column("book_id", sa.Integer(), sa.ForeignKey("book.book_id"), primary_key=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("category.category_id"), primary_key=True),
    )
    bind = op.get_bind()
    category = sa.table("category", sa.column("category_id", sa.Integer), sa.column("name", sa.String), sa.column("slug", sa.String))
    bind.execute(category.insert().values(name="General", slug="general"))
    general_id = bind.execute(sa.select(category.c.category_id).where(category.c.slug == "general")).scalar_one()
    book_categories = sa.table("book_categories", sa.column("book_id", sa.Integer), sa.column("category_id", sa.Integer))
    book = sa.table("book", sa.column("book_id", sa.Integer))
    for book_id in bind.execute(sa.select(book.c.book_id)).scalars():
        bind.execute(book_categories.insert().values(book_id=book_id, category_id=general_id))


def downgrade():
    op.drop_table("book_categories")
    op.drop_table("category")
