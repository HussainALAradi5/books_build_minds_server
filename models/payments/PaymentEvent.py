from sqlalchemy import Column, String, ForeignKey
from config import db
from models.shared.BaseEntity import BaseEntity

class PaymentEvent(BaseEntity, db.Model):
    __tablename__ = "payment_event"
    event_id = Column(String(255), primary_key=True)
    transaction_id = Column(String(36), ForeignKey("library_transaction.transaction_id"), nullable=False)
    event_type = Column(String(80), nullable=False)
