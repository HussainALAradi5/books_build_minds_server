from flask import Blueprint
from services.media import media_service
from utils.accounts.security import require_admin, require_user
from enums.accounts.permission import Permission

media = Blueprint("media", __name__)
media.add_url_rule("/media/books/<int:book_id>", view_func=media_service.list_media, methods=["GET"])
media.add_url_rule("/media/books/<int:book_id>", view_func=require_admin(Permission.BOOK_MEDIA_WRITE)(media_service.upload_media), methods=["POST"])
media.add_url_rule("/media/profile-picture", view_func=require_user(Permission.PROFILE_MEDIA_WRITE_OWN)(media_service.upload_profile_picture), methods=["POST"])
