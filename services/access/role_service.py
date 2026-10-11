from flask import request

from config import db
from models.access.AccessRole import AccessRole
from services.access.common import list_records
from utils.access_input import KEY_PATTERN, resolve_permissions
from utils.responses import error, success
from utils.validation import clean_text, json_body


def list_roles():
    return list_records(AccessRole, AccessRole.name, AccessRole.name)


def save_role(key=None):
    data = json_body()
    if key is None:
        key = clean_text(data.get("key"), 80)
        if not KEY_PATTERN.fullmatch(key):
            return error("Role key must be lowercase letters, numbers, or hyphens")
        if db.session.get(AccessRole, key):
            return error("Role key already exists", 409)
        item = AccessRole(key=key)
    else:
        item = db.session.get(AccessRole, key)
        if not item or item.is_deleted:
            return error("Role not found", 404)
    name = clean_text(data.get("name"), 120)
    if len(name) < 2:
        return error("Role name is required")
    try:
        permissions = resolve_permissions(data.get("permission_keys", []))
    except ValueError as exc:
        return error(str(exc))
    if item.key == "admin" and {entry.key for entry in permissions} != {entry.key for entry in item.permissions}:
        return error("Administrator permissions are fixed", 403)
    item.name = name
    item.description = clean_text(data.get("description"), 500)
    item.permissions = permissions
    db.session.add(item)
    db.session.commit()
    return success("Role saved", 201 if request.method == "POST" else 200, role=item.to_dict())


def delete_role(key):
    item = db.session.get(AccessRole, key)
    if not item or item.is_deleted:
        return error("Role not found", 404)
    if item.is_system:
        return error("Built-in roles cannot be deleted", 403)
    item.is_deleted = True
    db.session.commit()
    return success("Role deleted")
