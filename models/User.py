"""Account model and public serializer."""
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from config import db
from models.BaseEntity import BaseEntity
from dto.accounts.user_dto import UserDTO
from enums.accounts.account_role import AccountRole


class User(BaseEntity, db.Model):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(80), unique=True, nullable=False)
    password_digest = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(20), nullable=False, default=AccountRole.CLIENT.value, server_default=AccountRole.CLIENT.value)
    is_active = Column(Boolean, nullable=False, default=True)

    purchased_books = relationship("Book", secondary="purchased_books", back_populates="purchased_by_users")
    receipts = relationship("Receipt", back_populates="user", cascade="all, delete-orphan")
    added_books = relationship("Book", back_populates="added_by_user")
    loans = relationship("Loan", back_populates="user")
    activities = relationship("LibraryActivity", back_populates="user")
    profile_media = relationship("Media", foreign_keys="Media.user_id", back_populates="profile_user", order_by="Media.media_id")

    @property
    def is_admin(self) -> bool:
        return self.role == AccountRole.ADMIN.value

    @is_admin.setter
    def is_admin(self, value: bool) -> None:
        self.role = AccountRole.ADMIN.value if value else AccountRole.CLIENT.value

    def to_dict(self) -> UserDTO:
        profile_pictures = [item for item in self.profile_media if not item.is_deleted and not item.is_archived]
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "email": self.email,
            "is_active": self.is_active,
            "role": self.role,
            **self.entity_dict(),
            "purchased_books": [book.book_id for book in self.purchased_books if not book.is_deleted and not book.is_archived],
            "receipts": [receipt.to_dict() for receipt in self.receipts if not receipt.is_deleted and not receipt.is_archived],
            "profile_picture_url": profile_pictures[-1].to_dict()["url"] if profile_pictures else None,
        }
