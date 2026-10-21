from config import db
from models.shared.BaseEntity import BaseEntity
from models.access.associations import access_role_permission
from dto.access.permission_dto import PermissionDTO


class AccessPermission(BaseEntity, db.Model):
    __tablename__ = "access_permission"

    key = db.Column(db.String(80), primary_key=True)
    label = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False, default="")
    is_system = db.Column(db.Boolean, nullable=False, default=False)

    roles = db.relationship("AccessRole", secondary=access_role_permission, back_populates="permissions")

    def to_dict(self) -> PermissionDTO:
        return {"key": self.key, "label": self.label, "description": self.description,
                "is_system": self.is_system, **self.entity_dict()}
