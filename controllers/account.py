from flask import Blueprint
from services import account_service
from utils.security import require_user
from enums.accounts.permission import Permission

account = Blueprint("account", __name__)
account.add_url_rule("/register", view_func=account_service.register, methods=["POST"])
account.add_url_rule("/login", view_func=account_service.login, methods=["POST"])
account.add_url_rule("/profile/<int:user_id>", view_func=require_user(Permission.PROFILE_READ_OWN, owner_param="user_id")(account_service.profile), methods=["GET"])
account.add_url_rule("/profile/<int:user_id>/edit", view_func=require_user(Permission.PROFILE_EDIT_OWN, owner_param="user_id")(account_service.edit_profile), methods=["PUT"])
account.add_url_rule("/profile/<int:user_id>/books", view_func=require_user(Permission.PURCHASE_READ_OWN, owner_param="user_id")(account_service.purchased_books), methods=["GET"])
account.add_url_rule("/profile/<int:user_id>/activities", view_func=require_user(Permission.ACTIVITY_READ_OWN, owner_param="user_id")(account_service.list_activities), methods=["GET"])
account.add_url_rule("/admin-requests", view_func=require_user(Permission.ADMIN_REQUEST_READ_ANY)(account_service.list_admin_requests), methods=["GET"])
account.add_url_rule("/admin-requests", view_func=require_user(Permission.ADMIN_REQUEST_WRITE_ONE)(account_service.submit_admin_request), methods=["POST"])
account.add_url_rule("/admin-requests/<int:request_id>", view_func=require_user(Permission.ADMIN_REQUEST_EDIT_ANY)(account_service.review_admin_request), methods=["PATCH"])
