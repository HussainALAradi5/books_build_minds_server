"""Search and manage reusable book categories."""
from flask import jsonify, request

from config import db
from models.catalog.Category import Category
from models.catalog.Book import Book
from utils.books.book_ranking import ranked_books
from utils.catalog.category_input import category_slug
from utils.shared.pagination import page_options, paginate, order_query
from utils.shared.responses import error, success
from utils.shared.validation import clean_text, json_body


def list_categories():
    try:
        options = page_options()
        query = Category.query.filter_by(is_deleted=False, is_archived=False)
        term = clean_text(request.args.get("q"), 120)
        if term:
            query = query.filter(Category.name.ilike(f"%{term}%"))
        return jsonify(paginate(order_query(query, Category.name, options), lambda item: item.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def save_category():
    name = clean_text(json_body().get("name"), 120)
    if not name:
        return error("Name is required")
    try:
        slug = category_slug(name)
    except ValueError as exc:
        return error(str(exc))
    if Category.query.filter((Category.name == name) | (Category.slug == slug)).first():
        return error("Category already exists", 409)
    item = Category(name=name, slug=slug)
    db.session.add(item)
    db.session.commit()
    return success("Category saved", 201, category=item.to_dict())


def top_categories():
    sort = request.args.get("sort", "most_rated")
    if sort not in ("most_rated", "best_selling"):
        return error("sort must be most_rated or best_selling")
    try:
        options = page_options(default_size=10)
        category_page = paginate(order_query(Category.query.filter_by(is_deleted=False, is_archived=False), Category.name, options),
            lambda item: item.to_dict(), options)
        groups = []
        for category in category_page["items"]:
            query = Book.query.join(Book.categories).filter(Category.category_id == category["category_id"],
                Book.is_deleted.is_(False), Book.is_archived.is_(False))
            books = ranked_books(query, sort).limit(5).all()
            groups.append({"category": category, "books": [book.to_summary_dict() for book in books]})
        return jsonify({"items": groups, "pagination": category_page["pagination"]})
    except ValueError as exc:
        return error(str(exc))
