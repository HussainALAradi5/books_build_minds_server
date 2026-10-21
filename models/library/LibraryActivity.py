"""Audit record for a reader's library actions."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from config import db
from models.shared.BaseEntity import BaseEntity
from dto.library.library_activity_dto import LibraryActivityDTO


class LibraryActivity(BaseEntity, db.Model):
    __tablename__ = "library_activity"

    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False, index=True)
    action_type = Column(String(16), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="activities")
    book = relationship("Book", back_populates="activities")

    def to_dict(self) -> LibraryActivityDTO:
        return {
            "activity_id": self.activity_id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "book_title": self.book.title,
            "book_slug": self.book.slug,
            "action_type": self.action_type,
            "occurred_at": self.occurred_at.isoformat(),
            **self.entity_dict(),
        }
