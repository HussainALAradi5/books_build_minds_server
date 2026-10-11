"""Reviewed requests for administrator access."""
from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from config import db
from models.BaseEntity import BaseEntity
from dto.accounts.admin_request_dto import AdminRequestDTO


class AdminRequest(BaseEntity, db.Model):
    __tablename__ = "admin_request"

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    is_accepted = Column(Boolean)
    review_time = Column(Date)
    reviewed_by_user_id = Column(Integer, ForeignKey("user.user_id"))
    reason_for_request = Column(Text, nullable=False)
    requester_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)

    requester = relationship("User", foreign_keys=[requester_id], backref="admin_requests")
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by_user_id], backref="reviewed_requests")

    def to_dict(self) -> AdminRequestDTO:
        return {
            "request_id": self.request_id,
            "is_accepted": self.is_accepted,
            "review_time": self.review_time.isoformat() if self.review_time else None,
            "reviewed_by_user_id": self.reviewed_by_user_id,
            "reason_for_request": self.reason_for_request,
            "requester_id": self.requester_id,
            **self.entity_dict(),
        }
