from flask import Blueprint
from services import media_service
from utils.security import require_user

media = Blueprint("media", __name__)
media.add_url_rule("/media/books/<int:book_id>", view_func=media_service.list_media, methods=["GET"])
media.add_url_rule("/media/books/<int:book_id>", view_func=require_user(admin=True)(media_service.upload_media), methods=["POST"])
media.add_url_rule("/media/profile-picture", view_func=require_user()(media_service.upload_profile_picture), methods=["POST"])
