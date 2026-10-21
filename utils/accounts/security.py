"""JWT creation and account-based authorization helpers."""
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, request

from config import app, db
from models.accounts.User import User
from utils.access.access import AccessRule, all_of, has_access, has_role, owns
from enums.accounts.account_role import AccountRole
from utils.shared.responses import error


def create_token(user):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.user_id), "ver": user.token_version, "iat": now, "exp": now + timedelta(hours=8)},
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
        return user if user and payload.get("ver") == user.token_version and user.is_active and not user.is_deleted and not user.is_archived else None
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        return None


def require_user(access: AccessRule | None = None, owner_param: str | None = None):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return error("Authentication required", 401)
            rule = all_of(access, owns(kwargs[owner_param])) if access and owner_param else access
            if rule and not has_access(user, rule):
                return error("Access denied", 403)
            g.user = user
            return view(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(access: AccessRule):
    """Require the administrator account role as well as the action permission."""
    return require_user(all_of(has_role(AccountRole.ADMIN), access))
