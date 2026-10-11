"""Catalog model, purchase relation, and public serializer."""
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from config import db
from dto import BookDTO, BookSummaryDTO

purchased_books_table = db.Table(
    "purchased_books",
    db.Column("user_id", Integer, ForeignKey("user.user_id"), primary_key=True),
    db.Column("book_id", Integer, ForeignKey("book.book_id"), primary_key=True),
)


class Book(db.Model):
    __tablename__ = "book"

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(255), unique=True, nullable=False)
    isbn = Column(String(32), unique=True, nullable=False)
    book_image = Column(String(500))
    title = Column(String(255), unique=True, nullable=False)
    author = Column(String(255), nullable=False)
    publisher = Column(String(255), nullable=False)
    published_at = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    copies_total = Column(Integer, nullable=False, default=1)
    added_by_user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)

    added_by_user = relationship("User", back_populates="added_books")
    purchased_by_users = relationship("User", secondary=purchased_books_table, back_populates="purchased_books")
    receipts = relationship("Receipt", backref="book", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="book", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="book")

    @property
    def available_copies(self):
        return max(0, self.copies_total - sum(loan.returned_at is None for loan in self.loans))

    @property
    def average_rating(self):
        if not self.reviews:
            return 0.0
        return round(sum(review.rating for review in self.reviews) / len(self.reviews), 2)

    def to_summary_dict(self) -> BookSummaryDTO:
        return {
            "book_id": self.book_id,
            "isbn": self.isbn,
            "book_image": self.book_image,
            "slug": self.slug,
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "published_at": self.published_at.isoformat(),
            "price": self.price,
            "copies_total": self.copies_total,
            "available_copies": self.available_copies,
            "average_rating": self.average_rating,
        }

    def to_dict(self) -> BookDTO:
        return {
            **self.to_summary_dict(),
            "reviews": [review.to_dict() for review in self.reviews],
            "added_by_user_id": self.added_by_user_id,
            "purchased_by": [user.user_id for user in self.purchased_by_users],
            "media": [item.to_dict() for item in self.media],
        }
