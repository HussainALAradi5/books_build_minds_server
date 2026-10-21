from flask import request

from config import db
from models.access.AccessGroup import AccessGroup
from services.access.common import list_records
from utils.access.access_input import resolve_roles
from utils.shared.responses import error, success
from utils.shared.validation import clean_text, json_body


def list_groups():
    return list_records(AccessGroup, AccessGroup.name, AccessGroup.name)


def save_group(group_id=None):
    data = json_body()
    item = db.session.get(AccessGroup, group_id) if group_id else AccessGroup()
    if group_id and (not item or item.is_deleted):
        return error("Group not found", 404)
    name = clean_text(data.get("name"), 120)
    if len(name) < 2:
        return error("Group name is required")
    existing = AccessGroup.query.filter(AccessGroup.name == name, AccessGroup.group_id != group_id).first()
    if existing:
        return error("Group name already exists", 409)
    try:
        roles = resolve_roles(data.get("role_keys", []))
    except ValueError as exc:
        return error(str(exc))
    item.name = name
    item.description = clean_text(data.get("description"), 500)
    item.roles = roles
    db.session.add(item)
    db.session.commit()
    return success("Group saved", 201 if request.method == "POST" else 200, group=item.to_dict())


def delete_group(group_id):
    item = db.session.get(AccessGroup, group_id)
    if not item or item.is_deleted:
        return error("Group not found", 404)
    item.is_deleted = True
    db.session.commit()
    return success("Group deleted")
