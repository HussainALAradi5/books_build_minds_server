"""Receipt for one purchased book."""
from sqlalchemy import Column, Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from config import db
from dto import ReceiptDTO


class Receipt(db.Model):
    __tablename__ = "receipt"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_receipt_user_book"),)

    receipt_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False)
    written_time = Column(Date, nullable=False)
    user = relationship("User", back_populates="receipts")

    def to_dict(self) -> ReceiptDTO:
        return {
            "receipt_id": self.receipt_id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "written_time": self.written_time.isoformat(),
        }
