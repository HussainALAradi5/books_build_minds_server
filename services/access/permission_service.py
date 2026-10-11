from flask import request

from config import db
from models.access.AccessPermission import AccessPermission
from services.access.common import list_records
from utils.access_input import PERMISSION_PATTERN
from utils.responses import error, success
from utils.validation import clean_text, json_body


def list_permissions():
    return list_records(AccessPermission, AccessPermission.key, AccessPermission.key)


def save_permission(key=None):
    data = json_body()
    if key is None:
        key = clean_text(data.get("key"), 80)
        if not PERMISSION_PATTERN.fullmatch(key) or len(key) > 80:
            return error("Use a permission key such as resource:action.scope")
        if db.session.get(AccessPermission, key):
            return error("Permission key already exists", 409)
        item = AccessPermission(key=key)
        db.session.add(item)
    else:
        item = db.session.get(AccessPermission, key)
        if not item or item.is_deleted:
            return error("Permission not found", 404)
    label = clean_text(data.get("label"), 120)
    if len(label) < 2:
        return error("Permission label is required")
    item.label = label
    item.description = clean_text(data.get("description"), 500)
    db.session.commit()
    return success("Permission saved", 201 if request.method == "POST" else 200, permission=item.to_dict())


def delete_permission(key):
    item = db.session.get(AccessPermission, key)
    if not item or item.is_deleted:
        return error("Permission not found", 404)
    if item.is_system:
        return error("Built-in permissions cannot be deleted", 403)
    item.is_deleted = True
    db.session.commit()
    return success("Permission deleted")
