"""Add shared actor/timestamp fields and review descriptions.

Revision ID: af79dc1c0006
Revises: 9e68cb0b0005
"""
from alembic import op
import sqlalchemy as sa

revision = "af79dc1c0006"
down_revision = "9e68cb0b0005"
branch_labels = None
depends_on = None

TABLES = (
    "user", "book", "review", "receipt", "admin_request", "media", "loan",
    "library_activity", "country", "author", "publisher",
)
CREATORS = {
    "user": "user_id", "book": "added_by_user_id", "review": "user_id",
    "receipt": "user_id", "admin_request": "requester_id",
    "media": "uploaded_by_user_id", "loan": "user_id", "library_activity": "user_id",
}
CREATED_DATES = {
    "review": "written_time", "receipt": "written_time", "media": "uploaded_at",
    "loan": "borrowed_at", "library_activity": "occurred_at",
}


def upgrade():
    connection = op.get_bind()
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))
            batch.add_column(sa.Column("updated_by", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        quoted = f'"{table}"'
        source = CREATED_DATES.get(table)
        if source:
            connection.execute(sa.text(f"UPDATE {quoted} SET created_at = {source}"))
        connection.execute(sa.text(f"UPDATE {quoted} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
        creator = CREATORS.get(table)
        if creator:
            connection.execute(sa.text(f"UPDATE {quoted} SET created_by = {creator}"))
        with op.batch_alter_table(table) as batch:
            batch.alter_column("created_at", existing_type=sa.DateTime(timezone=True), nullable=False,
                               server_default=sa.text("CURRENT_TIMESTAMP"))
    connection.execute(sa.text("UPDATE review SET updated_at = last_edit WHERE last_edit IS NOT NULL"))
    connection.execute(sa.text("UPDATE review SET updated_by = user_id WHERE last_edit IS NOT NULL"))
    connection.execute(sa.text("UPDATE admin_request SET updated_by = reviewed_by_user_id WHERE reviewed_by_user_id IS NOT NULL"))
    with op.batch_alter_table("review") as batch:
        batch.add_column(sa.Column("description", sa.Text(), nullable=False, server_default=""))


def downgrade():
    with op.batch_alter_table("review") as batch:
        batch.drop_column("description")
    for table in reversed(TABLES):
        with op.batch_alter_table(table) as batch:
            batch.drop_column("updated_at")
            batch.drop_column("updated_by")
            batch.drop_column("created_at")
            batch.drop_column("created_by")
