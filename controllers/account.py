from flask import Blueprint
from services import account_service
from utils.security import require_user

account = Blueprint("account", __name__)
account.add_url_rule("/register", view_func=account_service.register, methods=["POST"])
account.add_url_rule("/login", view_func=account_service.login, methods=["POST"])
account.add_url_rule("/profile/<int:user_id>", view_func=require_user()(account_service.profile), methods=["GET"])
account.add_url_rule("/profile/<int:user_id>/edit", view_func=require_user()(account_service.edit_profile), methods=["PUT"])
account.add_url_rule("/profile/<int:user_id>/books", view_func=require_user()(account_service.purchased_books), methods=["GET"])
