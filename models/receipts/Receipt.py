"""Receipt for one purchased book."""
from sqlalchemy import Column, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from config import db
from models.shared.BaseEntity import BaseEntity
from dto.receipts.receipt_dto import ReceiptDTO


class Receipt(BaseEntity, db.Model):
    __tablename__ = "receipt"
    transaction_id = Column(String(36), ForeignKey("library_transaction.transaction_id", name="fk_receipt_transaction"), unique=True)
    amount_minor = Column(Integer)
    currency = Column(String(3))
    currency_scale = Column(Integer)
    book_title = Column(String(255))
    book_author = Column(String(255))
    customer_name = Column(String(80))
    kind = Column(String(16))
    transaction = relationship("Transaction", back_populates="receipt")

    receipt_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False)
    written_time = Column(Date, nullable=False)
    user = relationship("User", back_populates="receipts")

    def to_dict(self) -> ReceiptDTO:
        return {
            "receipt_id": self.receipt_id,
            "transaction_id": self.transaction_id,
            "amount_minor": self.amount_minor,
            "currency": self.currency,
            "currency_scale": self.currency_scale,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "written_time": self.written_time.isoformat(),
            **self.entity_dict(),
        }
