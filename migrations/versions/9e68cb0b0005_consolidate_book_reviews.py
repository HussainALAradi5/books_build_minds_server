"""Consolidate separate comments and ratings into purchase-gated reviews.

Revision ID: 9e68cb0b0005
Revises: 8d57bafa0004
"""
from collections import defaultdict
from datetime import date

from alembic import op
import sqlalchemy as sa

revision = "9e68cb0b0005"
down_revision = "8d57bafa0004"
branch_labels = None
depends_on = None


def as_date(value):
    return date.fromisoformat(str(value)[:10]) if value else None


def upgrade():
    connection = op.get_bind()
    with op.batch_alter_table("review") as batch:
        batch.drop_constraint("uq_review_user_book", type_="unique")

    existing = connection.execute(sa.text(
        "SELECT user_id, book_id, comment FROM review"
    )).mappings().all()
    existing_comments = {(row["user_id"], row["book_id"], row["comment"]) for row in existing}
    active_pairs = {
        (row["user_id"], row["book_id"])
        for row in connection.execute(sa.text(
            "SELECT user_id, book_id FROM review WHERE is_deleted = false AND is_archived = false"
        )).mappings()
    }
    purchased_pairs = {
        (row["user_id"], row["book_id"])
        for row in connection.execute(sa.text("SELECT user_id, book_id FROM purchased_books")).mappings()
    }
    stars = {
        (row["user_id"], row["book_id"]): row
        for row in connection.execute(sa.text(
            "SELECT user_id, book_id, rating, created_at, updated_at, is_deleted, is_archived FROM book_star"
        )).mappings()
    }
    comments = connection.execute(sa.text(
        "SELECT user_id, book_id, body, created_at, edited_at, is_deleted, is_archived "
        "FROM book_comment ORDER BY created_at DESC, comment_id DESC"
    )).mappings().all()
    comment_pairs = defaultdict(int)
    review = sa.table(
        "review",
        sa.column("user_id", sa.Integer), sa.column("book_id", sa.Integer),
        sa.column("comment", sa.Text), sa.column("rating", sa.Float),
        sa.column("written_time", sa.Date), sa.column("last_edit", sa.Date),
        sa.column("is_deleted", sa.Boolean), sa.column("is_archived", sa.Boolean),
    )
    for item in comments:
        pair = (item["user_id"], item["book_id"])
        comment_pairs[pair] += 1
        if (pair[0], pair[1], item["body"]) in existing_comments:
            continue
        star = stars.get(pair)
        has_complete_review = bool(star and not star["is_deleted"] and not star["is_archived"])
        active = (
            has_complete_review and pair in purchased_pairs and pair not in active_pairs
            and not item["is_deleted"] and not item["is_archived"]
        )
        connection.execute(review.insert().values(
            user_id=pair[0], book_id=pair[1], comment=item["body"],
            rating=float(star["rating"]) if star else 0.0,
            written_time=as_date(item["created_at"]), last_edit=as_date(item["edited_at"]),
            is_deleted=bool(item["is_deleted"]), is_archived=not active,
        ))
        if active:
            active_pairs.add(pair)
    for pair, star in stars.items():
        if pair in comment_pairs or pair in active_pairs:
            continue
        connection.execute(review.insert().values(
            user_id=pair[0], book_id=pair[1], comment="", rating=float(star["rating"]),
            written_time=as_date(star["created_at"]), last_edit=as_date(star["updated_at"]),
            is_deleted=bool(star["is_deleted"]), is_archived=True,
        ))

    op.create_index(
        "uq_review_active_user_book", "review", ["user_id", "book_id"], unique=True,
        postgresql_where=sa.text("is_deleted = false AND is_archived = false"),
        sqlite_where=sa.text("is_deleted = 0 AND is_archived = 0"),
    )
    op.drop_index("ix_book_star_user_id", table_name="book_star")
    op.drop_index("ix_book_star_book_id", table_name="book_star")
    op.drop_table("book_star")
    op.drop_index("ix_book_comment_user_id", table_name="book_comment")
    op.drop_index("ix_book_comment_book_id", table_name="book_comment")
    op.drop_table("book_comment")


def downgrade():
    raise RuntimeError("Review consolidation preserves legacy history in reviews; restore the database backup to reverse it")
