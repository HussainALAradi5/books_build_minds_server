from flask import Blueprint
from services import loan_service
from utils.security import require_user

loans = Blueprint("loans", __name__)
loans.add_url_rule("/book/<string:slug>/loan", view_func=require_user()(loan_service.current_loan), methods=["GET"])
loans.add_url_rule("/book/<string:slug>/borrow", view_func=require_user()(loan_service.borrow_book), methods=["POST"])
loans.add_url_rule("/book/<string:slug>/rent", view_func=require_user()(loan_service.rent_book), methods=["POST"])
loans.add_url_rule("/book/<string:slug>/return", view_func=require_user()(loan_service.return_book), methods=["POST"])
loans.add_url_rule("/profile/<int:user_id>/loans", view_func=require_user()(loan_service.list_loans), methods=["GET"])
