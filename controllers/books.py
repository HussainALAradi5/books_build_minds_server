from flask import Blueprint
from services import book_service
from utils.security import require_user

books = Blueprint("books", __name__)
books.add_url_rule("/", view_func=book_service.list_books, methods=["GET"])
books.add_url_rule("/book", view_func=require_user(admin=True)(book_service.create_book), methods=["POST"])
books.add_url_rule("/book/export", view_func=require_user(admin=True)(book_service.export_books), methods=["GET"])
books.add_url_rule("/book/manage", view_func=require_user(admin=True)(book_service.list_managed_books), methods=["GET"])
books.add_url_rule("/book/import", view_func=require_user(admin=True)(book_service.import_books), methods=["POST"])
books.add_url_rule("/book/bulk", view_func=require_user(admin=True)(book_service.bulk_books), methods=["POST"])
books.add_url_rule("/book/<string:slug>", view_func=book_service.get_book, methods=["GET"])
books.add_url_rule("/book/<string:slug>", view_func=require_user(admin=True)(book_service.update_book), methods=["PUT"])
books.add_url_rule("/book/<string:slug>", view_func=require_user(admin=True)(book_service.delete_book), methods=["DELETE"])
books.add_url_rule("/book/<string:slug>/purchase", view_func=require_user()(book_service.purchase_book), methods=["POST"])
