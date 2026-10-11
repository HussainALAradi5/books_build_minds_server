from config import db

access_role_permission = db.Table(
    "access_role_permission",
    db.Column("role_key", db.String(80), db.ForeignKey("access_role.key"), primary_key=True),
    db.Column("permission_key", db.String(80), db.ForeignKey("access_permission.key"), primary_key=True),
)

user_access_role = db.Table(
    "user_access_role",
    db.Column("user_id", db.Integer, db.ForeignKey("user.user_id"), primary_key=True),
    db.Column("role_key", db.String(80), db.ForeignKey("access_role.key"), primary_key=True),
)

access_group_role = db.Table(
    "access_group_role",
    db.Column("group_id", db.Integer, db.ForeignKey("access_group.group_id"), primary_key=True),
    db.Column("role_key", db.String(80), db.ForeignKey("access_role.key"), primary_key=True),
)

user_access_group = db.Table(
    "user_access_group",
    db.Column("user_id", db.Integer, db.ForeignKey("user.user_id"), primary_key=True),
    db.Column("group_id", db.Integer, db.ForeignKey("access_group.group_id"), primary_key=True),
)
