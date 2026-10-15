from uuid import uuid4
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from config import db
from models.BaseEntity import BaseEntity
from dto.payments.transaction_dto import TransactionDTO
from enums.payments.transaction_status import TransactionStatus

class Transaction(BaseEntity, db.Model):
    __tablename__ = "library_transaction"
    __table_args__ = (UniqueConstraint("user_id", "request_key", name="uq_transaction_request"),
                     CheckConstraint("amount_minor > 0", name="ck_transaction_amount_positive"))
    transaction_id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("book.book_id"), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": version}
    request_key = Column(String(36), nullable=False)
    kind = Column(String(16), nullable=False)
    status = Column(String(24), nullable=False, default=TransactionStatus.PENDING.value, index=True)
    amount_minor = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False)
    currency_scale = Column(Integer, nullable=False)
    book_title = Column(String(255), nullable=False)
    book_author = Column(String(255), nullable=False)
    customer_name = Column(String(80), nullable=False)
    book_slug = Column(String(255), nullable=False)
    policy_version = Column(String(32), nullable=False)
    provider_charge_id = Column(String(255), unique=True)
    provider_payment_id = Column(String(255), unique=True)
    provider_refund_id = Column(String(255), unique=True)
    refund_started_at = Column(DateTime(timezone=True))
    checkout_url = Column(String(2048))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True))
    failure_reason = Column(String(255))
    book = relationship("Book", back_populates="transactions")
    user = relationship("User")
    receipt = relationship("Receipt", back_populates="transaction", uselist=False)

    def to_dict(self) -> TransactionDTO:
        return {"transaction_id": self.transaction_id, "book_id": self.book_id,
                "book_title": self.book_title, "book_slug": self.book_slug, "kind": self.kind,
                "status": self.status, "amount_minor": self.amount_minor, "currency": self.currency,
                "currency_scale": self.currency_scale, "paid_at": self.paid_at.isoformat() if self.paid_at else None,
                "checkout_url": self.checkout_url if self.status == TransactionStatus.PENDING else None,
                "receipt_id": self.receipt.receipt_id if self.receipt else None,
                "failure_reason": self.failure_reason, **self.entity_dict()}
