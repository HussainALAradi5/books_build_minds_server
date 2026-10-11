from config import db
from models.BaseEntity import BaseEntity
from models.access.associations import access_role_permission, access_group_role, user_access_role
from dto.access.role_dto import RoleDTO


class AccessRole(BaseEntity, db.Model):
    __tablename__ = "access_role"

    key = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False, default="")
    is_system = db.Column(db.Boolean, nullable=False, default=False)

    permissions = db.relationship("AccessPermission", secondary=access_role_permission, back_populates="roles")
    groups = db.relationship("AccessGroup", secondary=access_group_role, back_populates="roles")
    users = db.relationship("User", secondary=user_access_role, back_populates="access_roles")

    def to_dict(self) -> RoleDTO:
        return {"key": self.key, "name": self.name, "description": self.description,
                "is_system": self.is_system,
                "permission_keys": sorted(item.key for item in self.permissions if not item.is_deleted),
                **self.entity_dict()}
