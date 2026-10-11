"""Account model and public serializer."""
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from config import db
from dto import UserDTO


class User(db.Model):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(80), unique=True, nullable=False)
    password_digest = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    purchased_books = relationship("Book", secondary="purchased_books", back_populates="purchased_by_users")
    receipts = relationship("Receipt", back_populates="user", cascade="all, delete-orphan")
    added_books = relationship("Book", back_populates="added_by_user")
    loans = relationship("Loan", back_populates="user")
    profile_media = relationship("Media", foreign_keys="Media.user_id", back_populates="profile_user", order_by="Media.media_id")

    def to_dict(self) -> UserDTO:
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "email": self.email,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "purchased_books": [book.book_id for book in self.purchased_books],
            "receipts": [receipt.to_dict() for receipt in self.receipts],
            "profile_picture_url": self.profile_media[-1].to_dict()["url"] if self.profile_media else None,
        }
