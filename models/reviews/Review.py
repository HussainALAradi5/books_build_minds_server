"""Purchase-gated book review model."""
from sqlalchemy import Column, Date, Float, ForeignKey, Index, Integer, Text, text
from sqlalchemy.orm import relationship

from config import db
from dto.reviews.review_dto import ReviewDTO
from models.shared.BaseEntity import BaseEntity


class Review(BaseEntity, db.Model):
    __tablename__ = "review"
    __table_args__ = (
        Index(
            "uq_review_active_user_book", "user_id", "book_id", unique=True,
            sqlite_where=text("is_deleted = 0 AND is_archived = 0"),
            postgresql_where=text("is_deleted = false AND is_archived = false"),
        ),
    )

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False)
    written_time = Column(Date, nullable=False)
    last_edit = Column(Date)
    rating = Column(Float, nullable=False)
    comment = Column(Text, nullable=False)
    description = Column(Text, nullable=False, default="", server_default="")

    user = relationship("User", backref="reviews")
    book = relationship("Book", back_populates="reviews")

    def to_dict(self) -> ReviewDTO:
        return {
            "review_id": self.review_id,
            "user_id": self.user_id,
            "user_name": self.user.user_name,
            "profile_picture_url": self.user.profile_picture_url,
            "book_id": self.book_id,
            "comment": self.comment,
            "description": self.description,
            "written_time": self.written_time.isoformat(),
            "last_edit": self.last_edit.isoformat() if self.last_edit else None,
            "rating": self.rating,
            **self.entity_dict(),
        }
