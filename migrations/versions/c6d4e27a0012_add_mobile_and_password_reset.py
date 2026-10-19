"""Add optional mobile login and single-use password reset codes.

Revision ID: c6d4e27a0012
Revises: f5c2a16b0011
"""
from alembic import op
import sqlalchemy as sa

revision = "c6d4e27a0012"
down_revision = "f5c2a16b0011"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user") as batch:
        batch.add_column(sa.Column("mobile_number", sa.String(16), nullable=True))
        batch.create_unique_constraint("uq_user_mobile_number", ["mobile_number"])
    op.create_table(
        "password_reset_code",
        sa.Column("reset_code_id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.Integer()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_password_reset_code_user_id", "password_reset_code", ["user_id"])


def downgrade():
    op.drop_index("ix_password_reset_code_user_id", table_name="password_reset_code")
    op.drop_table("password_reset_code")
    with op.batch_alter_table("user") as batch:
        batch.drop_constraint("uq_user_mobile_number", type_="unique")
        batch.drop_column("mobile_number")
