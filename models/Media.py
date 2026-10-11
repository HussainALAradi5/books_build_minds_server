"""Uploaded book media metadata; file bytes live under static/media."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from config import db
from models.BaseEntity import BaseEntity
from dto.media.media_dto import MediaDTO
from enums.media.media_type import MediaType


class Media(BaseEntity, db.Model):
    __tablename__ = "media"

    media_id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("book.book_id"), index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), index=True)
    media_type = Column(String(32), nullable=False)
    uploaded_by_user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    filename = Column(String(255), unique=True, nullable=False)
    original_name = Column(String(255), nullable=False)
    mime_type = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    book = relationship("Book", back_populates="media")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by_user_id])
    profile_user = relationship("User", foreign_keys=[user_id], back_populates="profile_media")

    def to_dict(self) -> MediaDTO:
        return {
            "media_id": self.media_id,
            "book_id": self.book_id,
            "user_id": self.user_id,
            "media_type": self.media_type,
            "uploaded_by_user_id": self.uploaded_by_user_id,
            "original_name": self.original_name,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "uploaded_at": self.uploaded_at.isoformat(),
            "url": f"/static/media/{self.filename}",
            **self.entity_dict(),
        }
