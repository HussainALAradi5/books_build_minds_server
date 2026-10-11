"""Normalize country, author, and publisher records.

Revision ID: 7c46a9e9f003
Revises: 6b35f8d8e002
"""
from alembic import op
import sqlalchemy as sa

revision = "7c46a9e9f003"
down_revision = "6b35f8d8e002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "country",
        sa.Column("code", sa.String(2), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("flag_url", sa.String(500)),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    for table, key in (("author", "author_id"), ("publisher", "publisher_id")):
        op.create_table(
            table,
            sa.Column(key, sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(255), nullable=False, unique=True),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("country_code", sa.String(2), sa.ForeignKey("country.code")),
            sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    with op.batch_alter_table("book") as batch:
        batch.add_column(sa.Column("author_id", sa.Integer(), sa.ForeignKey("author.author_id", name="fk_book_author_id")))
        batch.add_column(sa.Column("publisher_id", sa.Integer(), sa.ForeignKey("publisher.publisher_id", name="fk_book_publisher_id")))
        batch.create_index("ix_book_author_id", ["author_id"])
        batch.create_index("ix_book_publisher_id", ["publisher_id"])
    connection = op.get_bind()
    connection.execute(sa.text("INSERT INTO author (name, description, is_archived, is_deleted) SELECT DISTINCT author, '', 0, 0 FROM book"))
    connection.execute(sa.text("INSERT INTO publisher (name, description, is_archived, is_deleted) SELECT DISTINCT publisher, '', 0, 0 FROM book"))
    connection.execute(sa.text("UPDATE book SET author_id = (SELECT author_id FROM author WHERE author.name = book.author)"))
    connection.execute(sa.text("UPDATE book SET publisher_id = (SELECT publisher_id FROM publisher WHERE publisher.name = book.publisher)"))


def downgrade():
    with op.batch_alter_table("book") as batch:
        batch.drop_index("ix_book_publisher_id")
        batch.drop_index("ix_book_author_id")
        batch.drop_column("publisher_id")
        batch.drop_column("author_id")
    op.drop_table("publisher")
    op.drop_table("author")
    op.drop_table("country")
