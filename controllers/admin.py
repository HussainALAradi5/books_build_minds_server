from flask import Blueprint
from services import admin_service
from utils.security import require_user

admin = Blueprint("admin", __name__)
admin.add_url_rule("/admin-requests", view_func=require_user(admin=True)(admin_service.list_requests), methods=["GET"])
admin.add_url_rule("/admin-requests", view_func=require_user()(admin_service.submit_request), methods=["POST"])
admin.add_url_rule("/admin-requests/<int:request_id>", view_func=require_user(admin=True)(admin_service.review_request), methods=["PATCH"])
