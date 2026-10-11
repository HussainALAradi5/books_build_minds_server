"""Persist permission catalog, roles, groups, and assignments.

Revision ID: c9f1d82b0008
Revises: b8e0c71a0007
"""
from alembic import op
import sqlalchemy as sa

revision = "c9f1d82b0008"
down_revision = "b8e0c71a0007"
branch_labels = None
depends_on = None

PERMISSIONS = (
    "profile:read.own", "profile:edit.own", "activity:read.own",
    "purchase:read.own", "purchase:write.one", "loan:read.own",
    "loan:write.one", "receipt:read.own", "review:read.own",
    "review:write.one", "review:edit.own", "review:edit.any",
    "review:delete.own", "review:delete.any", "book:read.any",
    "book:write.one", "book:edit.any", "book:delete.any",
    "book:write.bulk", "book:edit.bulk", "book-media:write.one",
    "profile-media:write.own", "author:write.one", "publisher:write.one",
    "country:sync", "admin-request:write.one", "admin-request:read.any",
    "admin-request:edit.any", "access:read.any", "access:edit.any",
)
MEMBER_PERMISSIONS = (
    "profile:read.own", "profile:edit.own", "activity:read.own",
    "purchase:read.own", "purchase:write.one", "loan:read.own",
    "loan:write.one", "receipt:read.own", "review:read.own",
    "review:write.one", "review:edit.own", "review:delete.own",
    "profile-media:write.own", "admin-request:write.one",
)


def audit_columns():
    return (
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def upgrade():
    op.create_table(
        "access_permission", sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        *audit_columns(),
    )
    op.create_table(
        "access_role", sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        *audit_columns(),
    )
    op.create_table(
        "access_group", sa.Column("group_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(120), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=False, server_default=""),
        *audit_columns(),
    )
    op.create_table("access_role_permission",
                    sa.Column("role_key", sa.String(80), sa.ForeignKey("access_role.key"), primary_key=True),
                    sa.Column("permission_key", sa.String(80), sa.ForeignKey("access_permission.key"), primary_key=True))
    op.create_table("user_access_role",
                    sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), primary_key=True),
                    sa.Column("role_key", sa.String(80), sa.ForeignKey("access_role.key"), primary_key=True))
    op.create_table("access_group_role",
                    sa.Column("group_id", sa.Integer(), sa.ForeignKey("access_group.group_id"), primary_key=True),
                    sa.Column("role_key", sa.String(80), sa.ForeignKey("access_role.key"), primary_key=True))
    op.create_table("user_access_group",
                    sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.user_id"), primary_key=True),
                    sa.Column("group_id", sa.Integer(), sa.ForeignKey("access_group.group_id"), primary_key=True))
    permission_table = sa.table("access_permission", sa.column("key", sa.String), sa.column("label", sa.String),
                                sa.column("is_system", sa.Boolean))
    role_table = sa.table("access_role", sa.column("key", sa.String), sa.column("name", sa.String),
                          sa.column("is_system", sa.Boolean))
    role_permission_table = sa.table("access_role_permission", sa.column("role_key", sa.String),
                                     sa.column("permission_key", sa.String))
    op.bulk_insert(permission_table, [{"key": key, "label": key.replace(":", " · "), "is_system": True} for key in PERMISSIONS])
    op.bulk_insert(role_table, [{"key": key, "name": key.title(), "is_system": True}
                                for key in ("visitor", "client", "employee", "admin")])
    op.bulk_insert(role_permission_table, [
        {"role_key": role, "permission_key": permission}
        for role in ("client", "employee", "admin")
        for permission in (PERMISSIONS if role == "admin" else MEMBER_PERMISSIONS)
    ])


def downgrade():
    for table in ("user_access_group", "access_group_role", "user_access_role", "access_role_permission",
                  "access_group", "access_role", "access_permission"):
        op.drop_table(table)
