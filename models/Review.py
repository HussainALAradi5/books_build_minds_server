"""Purchase-gated book review model."""
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from config import db
from dto import ReviewDTO


class Review(db.Model):
    __tablename__ = "review"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_review_user_book"),)

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False)
    written_time = Column(Date, nullable=False)
    last_edit = Column(Date)
    rating = Column(Float, nullable=False)
    comment = Column(Text, nullable=False)

    user = relationship("User", backref="reviews")
    book = relationship("Book", back_populates="reviews")

    def to_dict(self) -> ReviewDTO:
        return {
            "review_id": self.review_id,
            "user_id": self.user_id,
            "user_name": self.user.user_name,
            "book_id": self.book_id,
            "comment": self.comment,
            "written_time": self.written_time.isoformat(),
            "last_edit": self.last_edit.isoformat() if self.last_edit else None,
            "rating": self.rating,
        }
