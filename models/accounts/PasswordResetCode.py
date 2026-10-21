"""Single-use email code for resetting an account password."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from config import db
from models.shared.BaseEntity import BaseEntity


class PasswordResetCode(BaseEntity, db.Model):
    __tablename__ = "password_reset_code"

    reset_code_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False, index=True)
    code_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True))
    attempts = Column(Integer, nullable=False, default=0, server_default="0")
