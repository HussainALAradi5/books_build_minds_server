"""A borrow transaction with an explicit return date."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from config import db
from models.BaseEntity import BaseEntity
from dto.library.loan_dto import LoanDTO
from enums.library.loan_status import LoanStatus
from enums.library.loan_kind import LoanKind


class Loan(BaseEntity, db.Model):
    __tablename__ = "loan"

    loan_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False, index=True)
    borrowed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    due_at = Column(DateTime(timezone=True), nullable=False)
    returned_at = Column(DateTime(timezone=True))
    loan_kind = Column(String(16), nullable=False, default=LoanKind.BORROW.value)
    rental_fee = Column(Float, nullable=False, default=0)

    user = relationship("User", back_populates="loans")
    book = relationship("Book", back_populates="loans")

    @property
    def status(self) -> LoanStatus:
        if self.returned_at:
            return LoanStatus.RETURNED
        if self.due_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return LoanStatus.OVERDUE
        return LoanStatus.ACTIVE

    def to_dict(self) -> LoanDTO:
        return {
            "loan_id": self.loan_id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "book_title": self.book.title,
            "book_slug": self.book.slug,
            "borrowed_at": self.borrowed_at.isoformat(),
            "due_at": self.due_at.isoformat(),
            "returned_at": self.returned_at.isoformat() if self.returned_at else None,
            "status": self.status.value,
            "loan_kind": self.loan_kind,
            "rental_fee": self.rental_fee,
            **self.entity_dict(),
        }
