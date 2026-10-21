from config import db
from models.shared.BaseEntity import BaseEntity
from models.access.associations import access_group_role, user_access_group
from dto.access.group_dto import GroupDTO


class AccessGroup(BaseEntity, db.Model):
    __tablename__ = "access_group"

    group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=False, default="")

    roles = db.relationship("AccessRole", secondary=access_group_role, back_populates="groups")
    members = db.relationship("User", secondary=user_access_group, back_populates="access_groups")

    def to_dict(self) -> GroupDTO:
        return {"group_id": self.group_id, "name": self.name, "description": self.description,
                "role_keys": sorted(role.key for role in self.roles if not role.is_deleted),
                "member_count": sum(not user.is_deleted for user in self.members),
                **self.entity_dict()}
