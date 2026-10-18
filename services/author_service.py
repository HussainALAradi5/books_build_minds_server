"""Author profiles and published works."""
from flask import jsonify, request

from config import db
from models.Author import Author
from utils.catalog_input import catalog_values
from utils.pagination import page_options, paginate, order_query
from utils.responses import error, success
from utils.validation import clean_text


def list_authors():
    try:
        options = page_options()
        query = Author.query.filter_by(is_deleted=False, is_archived=False)
        term = clean_text(request.args.get("q"), 120)
        if term:
            query = query.filter(Author.name.ilike(f"%{term}%"))
        return jsonify(paginate(order_query(query, Author.name, options), lambda item: item.to_dict(), options))
    except ValueError as exc:
        return error(str(exc))


def get_author(author_id):
    item = db.session.get(Author, author_id)
    return jsonify(item.to_dict()) if item and not item.is_deleted else error("Author not found", 404)


def save_author():
    try:
        name, description, code = catalog_values()
    except ValueError as exc:
        return error(str(exc))
    if Author.query.filter_by(name=name).first():
        return error("Author already exists", 409)
    item = Author()
    item.name, item.description, item.country_code = name, description, code
    db.session.add(item)
    db.session.commit()
    return success("Author saved", 201, author=item.to_dict())
