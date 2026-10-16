from flask import Blueprint
from services.reviews import review_service
from utils.security import require_user
from enums.accounts.permission import Permission
from utils.access import any_of

reviews = Blueprint("reviews", __name__)
reviews.add_url_rule("/book/<string:slug>/review", view_func=review_service.list_reviews, methods=["GET"])
reviews.add_url_rule("/book/<string:slug>/review/mine", view_func=require_user(Permission.REVIEW_READ_OWN)(review_service.my_review), methods=["GET"])
reviews.add_url_rule("/book/<string:slug>/review", view_func=require_user(Permission.REVIEW_WRITE_ONE)(review_service.add_review), methods=["POST"])
reviews.add_url_rule("/book/<string:slug>/review/<int:review_id>", view_func=require_user(Permission.REVIEW_EDIT_OWN)(review_service.edit_review), methods=["PUT"])
reviews.add_url_rule("/book/<string:slug>/review/<int:review_id>", view_func=require_user(any_of(Permission.REVIEW_DELETE_OWN, Permission.REVIEW_DELETE_ANY))(review_service.delete_review), methods=["DELETE"])
