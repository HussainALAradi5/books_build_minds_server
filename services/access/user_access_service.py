from flask import g, jsonify, request

from config import db
from dto.access.user_access_dto import UserAccessDTO
from enums.accounts.account_role import AccountRole
from models.User import User
from utils.access_input import resolve_groups, resolve_roles
from utils.pagination import order_query, page_options, paginate
from utils.responses import error, success
from utils.validation import clean_text, json_body


def serialize_user(user: User) -> UserAccessDTO:
    return {"user_id": user.user_id, "user_name": user.user_name, "email": user.email,
            "role": user.role.value, "is_active": user.is_active,
            "access_role_keys": sorted(role.key for role in user.access_roles if not role.is_deleted),
            "group_ids": sorted(group.group_id for group in user.access_groups if not group.is_deleted),
            **user.entity_dict()}


def list_users():
    try:
        options = page_options(default_size=25, max_size=100)
        query = User.query.filter_by(is_deleted=False)
        term = clean_text(request.args.get("q"), 120)
        if term:
            query = query.filter(User.user_name.ilike(f"%{term}%"))
        return jsonify(paginate(order_query(query, User.user_name, options), serialize_user, options))
    except ValueError as exc:
        return error(str(exc))


def set_user_access(user_id):
    user = db.session.get(User, user_id)
    if not user or user.is_deleted:
        return error("User not found", 404)
    data = json_body()
    try:
        role = AccountRole(data.get("role"))
        roles = resolve_roles(data.get("access_role_keys", []))
        groups = resolve_groups(data.get("group_ids", []))
    except (ValueError, TypeError) as exc:
        return error(str(exc) or "Invalid role")
    if user_id == g.user.user_id and role != AccountRole.ADMIN:
        return error("You cannot remove your own administrator role", 403)
    user.role = role
    user.access_roles = roles
    user.access_groups = groups
    db.session.commit()
    return success("User access updated", user=serialize_user(user))
