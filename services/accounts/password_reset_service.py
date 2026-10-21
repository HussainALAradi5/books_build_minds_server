"""Issue and consume short-lived, single-use password reset codes."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from werkzeug.security import generate_password_hash

from config import db
from models.accounts.PasswordResetCode import PasswordResetCode
from models.accounts.User import User
from services.accounts.reset_delivery import delivery_ready, send_reset_code
from utils.accounts.mobile_number import normalize_mobile
from utils.shared.responses import error, success
from utils.shared.validation import clean_text, json_body, valid_password

GENERIC_RESPONSE = "If this account exists, a reset code was sent to its saved email address."


def find_user(identifier):
    raw = clean_text(identifier, 255).lower()
    if not raw:
        return None
    try:
        mobile = normalize_mobile(raw) if raw.startswith("+") else None
    except ValueError:
        return None
    identity = (User.user_name == raw) | (User.email == raw)
    if mobile:
        identity = identity | (User.mobile_number == mobile)
    return User.query.filter(identity).first()


def code_digest(reset_id, code):
    key = current_app.config["JWT_SECRET_KEY"].encode("utf-8")
    return hmac.new(key, f"{reset_id}:{code}".encode("ascii"), hashlib.sha256).hexdigest()


def issue_code():
    identifier = clean_text(json_body().get("identifier"), 255)
    if not identifier:
        return error("Email, username, or mobile number is required")
    if not delivery_ready():
        return error("Password reset email is not configured", 503)
    user = find_user(identifier)
    if not user or not user.is_active or user.is_deleted or user.is_archived:
        return success(GENERIC_RESPONSE)
    now = datetime.now(timezone.utc)
    latest = PasswordResetCode.query.filter_by(user_id=user.user_id).order_by(
        PasswordResetCode.reset_code_id.desc()).first()
    if latest and latest.created_at and latest.created_at.replace(tzinfo=timezone.utc) > now - timedelta(seconds=60):
        return success(GENERIC_RESPONSE)
    for previous in PasswordResetCode.query.filter_by(user_id=user.user_id, consumed_at=None).all():
        previous.consumed_at = now
    item = PasswordResetCode(user_id=user.user_id, code_hash="pending", expires_at=now + timedelta(minutes=10))
    db.session.add(item)
    db.session.flush()
    code = f"{secrets.randbelow(1_000_000):06d}"
    item.code_hash = code_digest(item.reset_code_id, code)
    try:
        send_reset_code(user.email, code)
    except RuntimeError:
        db.session.rollback()
        return success(GENERIC_RESPONSE)
    db.session.commit()
    return success(GENERIC_RESPONSE)


def confirm_code():
    data = json_body()
    identifier = clean_text(data.get("identifier"), 255)
    code = data.get("code")
    password = data.get("new_password")
    if not identifier or not isinstance(code, str) or len(code) != 6 or not code.isdigit() or not valid_password(password):
        return error("Enter a six-digit code and a password with at least 5 letters and 3 numbers")
    user = find_user(identifier)
    if not user or not user.is_active or user.is_deleted or user.is_archived:
        return error("Invalid or expired reset code", 400)
    item = PasswordResetCode.query.filter_by(user_id=user.user_id, consumed_at=None).order_by(
        PasswordResetCode.reset_code_id.desc()).first()
    now = datetime.now(timezone.utc)
    if not item or item.attempts >= 5 or item.expires_at.replace(tzinfo=timezone.utc) <= now:
        return error("Invalid or expired reset code", 400)
    item.attempts += 1
    if not hmac.compare_digest(item.code_hash, code_digest(item.reset_code_id, code)):
        db.session.commit()
        return error("Invalid or expired reset code", 400)
    item.consumed_at = now
    user.password_digest = generate_password_hash(password)
    user.token_version += 1
    db.session.commit()
    return success("Password updated. Sign in with your new password.")
