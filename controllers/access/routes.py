from flask import Blueprint

from enums.accounts.permission import Permission
from enums.accounts.account_role import AccountRole
from services.access import group_service, permission_service, role_service, user_access_service
from utils.accounts.security import require_user
from utils.access.access import all_of, has_role

access = Blueprint("access", __name__)


def admin_access(permission):
    return require_user(all_of(has_role(AccountRole.ADMIN), permission))

access.add_url_rule("/access/permissions", view_func=admin_access(Permission.ACCESS_READ_ANY)(permission_service.list_permissions), methods=["GET"])
access.add_url_rule("/access/permissions", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(permission_service.save_permission), methods=["POST"])
access.add_url_rule("/access/permissions/<string:key>", endpoint="update_permission", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(permission_service.save_permission), methods=["PUT"])
access.add_url_rule("/access/permissions/<string:key>", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(permission_service.delete_permission), methods=["DELETE"])

access.add_url_rule("/access/roles", view_func=admin_access(Permission.ACCESS_READ_ANY)(role_service.list_roles), methods=["GET"])
access.add_url_rule("/access/roles", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(role_service.save_role), methods=["POST"])
access.add_url_rule("/access/roles/<string:key>", endpoint="update_role", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(role_service.save_role), methods=["PUT"])
access.add_url_rule("/access/roles/<string:key>", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(role_service.delete_role), methods=["DELETE"])

access.add_url_rule("/access/groups", view_func=admin_access(Permission.ACCESS_READ_ANY)(group_service.list_groups), methods=["GET"])
access.add_url_rule("/access/groups", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(group_service.save_group), methods=["POST"])
access.add_url_rule("/access/groups/<int:group_id>", endpoint="update_group", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(group_service.save_group), methods=["PUT"])
access.add_url_rule("/access/groups/<int:group_id>", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(group_service.delete_group), methods=["DELETE"])

access.add_url_rule("/access/users", view_func=admin_access(Permission.ACCESS_READ_ANY)(user_access_service.list_users), methods=["GET"])
access.add_url_rule("/access/users/<int:user_id>", view_func=admin_access(Permission.ACCESS_EDIT_ANY)(user_access_service.set_user_access), methods=["PUT"])
