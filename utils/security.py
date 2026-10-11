"""JWT creation and account-based authorization helpers."""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, request

from config import app, db
from models.User import User
from utils.responses import error


def create_token(user):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.user_id), "iat": now, "exp": now + timedelta(hours=8)},
        app.config["JWT_SECRET_KEY"], algorithm="HS256",
    )


def current_user():
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.removeprefix("Bearer ").strip()
        payload = jwt.decode(token, app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        user_id = int(payload["sub"])
        user = db.session.get(User, user_id)
        return user if user and user.is_active else None
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None


def require_user(admin=False):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return error("Authentication required", 401)
            if admin and not user.is_admin:
                return error("Administrator access required", 403)
            g.user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator
