"""Catalog model, purchase relation, and public serializer."""
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from config import db
from models.shared.BaseEntity import BaseEntity
from dto.books.book_dto import BookDTO
from dto.books.book_summary_dto import BookSummaryDTO
from enums.books.book_status import BookStatus
from models.catalog.Category import book_categories

purchased_books_table = db.Table(
    "purchased_books",
    db.Column("user_id", Integer, ForeignKey("user.user_id"), primary_key=True),
    db.Column("book_id", Integer, ForeignKey("book.book_id"), primary_key=True),
)


class Book(BaseEntity, db.Model):
    __tablename__ = "book"

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(255), unique=True, nullable=False)
    isbn = Column(String(32), unique=True, nullable=False)
    book_image = Column(String(500))
    title = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=False, default="", server_default="")
    author = Column(String(255), nullable=False)
    publisher = Column(String(255), nullable=False)
    published_at = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    copies_total = Column(Integer, nullable=False, default=1)
    condition = Column(String(32), nullable=False, default=BookStatus.GOOD.value)
    added_by_user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    author_id = Column(Integer, ForeignKey("author.author_id"), index=True)
    publisher_id = Column(Integer, ForeignKey("publisher.publisher_id"), index=True)

    added_by_user = relationship("User", back_populates="added_books")
    author_record = relationship("Author", back_populates="books")
    publisher_record = relationship("Publisher", back_populates="books")
    categories = relationship("Category", secondary=book_categories, back_populates="books")
    purchased_by_users = relationship("User", secondary=purchased_books_table, back_populates="purchased_books")
    receipts = relationship("Receipt", backref="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="book", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="book")
    loans = relationship("Loan", back_populates="book")
    activities = relationship("LibraryActivity", back_populates="book")

    @property
    def available_copies(self):
        active_loans = sum(loan.returned_at is None and not loan.is_deleted and not loan.is_archived for loan in self.loans)
        reservations = sum(item.status == "pending" for item in self.transactions)
        return max(0, self.copies_total - active_loans - len(self.purchased_by_users) - reservations)

    @property
    def average_rating(self):
        active_reviews = [review.rating for review in self.reviews if not review.is_deleted and not review.is_archived]
        if not active_reviews:
            return 0.0
        return round(sum(active_reviews) / len(active_reviews), 2)

    def to_summary_dict(self) -> BookSummaryDTO:
        return {
            "book_id": self.book_id,
            "isbn": self.isbn,
            "book_image": self.book_image,
            "slug": self.slug,
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "categories": [category.to_dict() for category in self.categories if not category.is_deleted and not category.is_archived],
            "published_at": self.published_at.isoformat(),
            "price": self.price,
            "copies_total": self.copies_total,
            "available_copies": self.available_copies,
            "condition": self.condition,
            "average_rating": self.average_rating,
            **self.entity_dict(),
        }

    def to_dict(self) -> BookDTO:
        return {
            **self.to_summary_dict(),
            "description": self.description,
            "reviews": [review.to_dict() for review in self.reviews if not review.is_deleted and not review.is_archived],
            "added_by_user_id": self.added_by_user_id,
            "purchased_by": [user.user_id for user in self.purchased_by_users],
            "media": [item.to_dict() for item in self.media if not item.is_deleted and not item.is_archived],
            "author_details": self.author_record.to_dict() if self.author_record else None,
            "publisher_details": self.publisher_record.to_dict() if self.publisher_record else None,
        }
