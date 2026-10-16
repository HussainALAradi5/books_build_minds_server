from flask import Blueprint
from services import book_service
from services.books import book_print_service
from utils.security import require_admin, require_user
from enums.accounts.permission import Permission

books = Blueprint("books", __name__)
books.add_url_rule("/", view_func=book_service.list_books, methods=["GET"])
books.add_url_rule("/book", view_func=require_admin(Permission.BOOK_WRITE_ONE)(book_service.create_book), methods=["POST"])
books.add_url_rule("/book/export", view_func=require_user()(book_service.export_books), methods=["GET"])
books.add_url_rule("/book/manage", view_func=require_user(Permission.BOOK_READ_ANY)(book_service.list_managed_books), methods=["GET"])
books.add_url_rule("/book/import", view_func=require_admin(Permission.BOOK_IMPORT)(book_service.import_books), methods=["POST"])
books.add_url_rule("/book/bulk", view_func=require_admin(Permission.BOOK_BULK_EDIT)(book_service.bulk_books), methods=["POST"])
books.add_url_rule("/book/<string:slug>", view_func=book_service.get_book, methods=["GET"])
books.add_url_rule("/book/<string:slug>", view_func=require_admin(Permission.BOOK_EDIT_ANY)(book_service.update_book), methods=["PUT"])
books.add_url_rule("/book/<string:slug>", view_func=require_admin(Permission.BOOK_DELETE_ANY)(book_service.delete_book), methods=["DELETE"])
books.add_url_rule("/book/<string:slug>/purchase", view_func=require_user(Permission.PURCHASE_WRITE_ONE)(book_service.purchase_book), methods=["POST"])

books.add_url_rule("/book/<string:slug>/codes", view_func=book_print_service.get_book_codes, methods=["GET"])
books.add_url_rule("/book/<string:slug>/print", view_func=book_print_service.download_book_pdf, methods=["GET"])
