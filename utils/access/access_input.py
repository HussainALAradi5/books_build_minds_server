"""Validation shared by access administration services."""
import re

from config import db
from models.access.AccessPermission import AccessPermission
from models.access.AccessRole import AccessRole
from models.access.AccessGroup import AccessGroup

KEY_PATTERN = re.compile(r"^[a-z][a-z0-9-]{1,39}$")
PERMISSION_PATTERN = re.compile(r"^[a-z][a-z0-9-]*:[a-z][a-z0-9-]*(?:\.(?:own|one|any|bulk))?$")


def resolve_keys(values, model, key_name):
    if not isinstance(values, list) or len(values) > 100 or any(not isinstance(value, str) for value in values):
        raise ValueError(f"{key_name} must be a list of keys")
    keys = set(values)
    records = [db.session.get(model, key) for key in keys]
    if any(record is None or record.is_deleted or record.is_archived for record in records):
        raise ValueError(f"Unknown or inactive {key_name}")
    return records


def resolve_permissions(values):
    return resolve_keys(values, AccessPermission, "permission_keys")


def resolve_roles(values):
    return resolve_keys(values, AccessRole, "role_keys")


def resolve_groups(values):
    if not isinstance(values, list) or len(values) > 100 or any(type(value) is not int for value in values):
        raise ValueError("group_ids must be a list of IDs")
    records = [db.session.get(AccessGroup, group_id) for group_id in set(values)]
    if any(record is None or record.is_deleted or record.is_archived for record in records):
        raise ValueError("Unknown or inactive group_ids")
    return records
