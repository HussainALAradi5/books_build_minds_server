"""Store the canonical user role and migrate administrator flags.

Revision ID: b8e0c71a0007
Revises: af79dc1c0006
"""
from alembic import op
import sqlalchemy as sa

revision = "b8e0c71a0007"
down_revision = "af79dc1c0006"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user") as batch:
        batch.add_column(sa.Column("role", sa.String(length=20), nullable=False, server_default="client"))
    op.execute("UPDATE \"user\" SET role = 'admin' WHERE is_admin = true")
    with op.batch_alter_table("user") as batch:
        batch.drop_column("is_admin")


def downgrade():
    with op.batch_alter_table("user") as batch:
        batch.add_column(sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE \"user\" SET is_admin = true WHERE role = 'admin'")
    with op.batch_alter_table("user") as batch:
        batch.drop_column("role")
